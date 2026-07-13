"""
AI Assistant service — LangGraph agent with PostgreSQL-backed checkpointing.

The agent exposes tool schemas to the LLM so it can reason about editing the
exam paper, but the actual tool side-effects are executed by the frontend.
When the LLM emits tool_calls, the backend pauses and returns them to the
frontend. The frontend applies the mutations and sends the results back via
``/tool-results/stream``, at which point the agent continues and produces a
final natural-language response.

Thread identity is (user_id, exam_id). Opening the same exam always resumes
the same conversation.
"""

from __future__ import annotations

import atexit
import json
import uuid
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Annotated, Any, TypedDict

import httpx
import psycopg
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from sqlalchemy import text
from sqlmodel import Session, delete, select

from app.core.config import settings
from app.modules.ai_assistant.llm import MyVLLMChatModel
from app.modules.ai_assistant.models import AIAssistantThread
from app.modules.ai_assistant.schemas import (
    BatchCreateQuestionsArgs,
    CreateQuestionArgs,
    DeleteQuestionArgs,
    EditQuestionArgs,
    SearchQuestionsArgs,
    ToolResult,
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class LLMUnavailableError(RuntimeError):
    """Raised when the LLM endpoint is unreachable or times out."""


_SYSTEM_PROMPT = """你是考试管理系统的 AI 组卷助手，帮助管理员管理试卷题目。

可用题型只有三种：
- SINGLE_CHOICE：单选题，有且只有一个正确答案
- MULTIPLE_CHOICE：多选题，有一个或多个正确答案
- TRUE_FALSE：判断题，只有「正确」和「错误」两个选项

重要规则：
1. 你只通过工具调用给出修改意图，真正的修改由前端执行，不会直接写入数据库。
2. 用户必须手动点击「保存试卷」才能持久化改动。
3. 删除或编辑题目时，index 是当前题目列表的零基索引（从 0 开始）。
4. 请用中文回答，保持简洁、专业。"""


def _make_human_message(
    user_message: str,
    exam_id: str,
    current_questions: list[dict[str, Any]],
) -> HumanMessage:
    content = (
        f"考试 ID: {exam_id}\n"
        f"当前题目数量: {len(current_questions)}\n"
        f"当前题目列表（JSON）:\n"
        f"{json.dumps(current_questions, ensure_ascii=False, indent=2)}\n\n"
        f"用户请求: {user_message}"
    )
    return HumanMessage(content=content)


# ─── Tool stubs: schemas for the LLM, execution happens in the frontend ───────

def _create_question_stub(_args: CreateQuestionArgs) -> str:
    return "ok"


def _edit_question_stub(_args: EditQuestionArgs) -> str:
    return "ok"


def _delete_question_stub(_args: DeleteQuestionArgs) -> str:
    return "ok"


def _search_questions_stub(_args: SearchQuestionsArgs) -> str:
    return "ok"


def _get_paper_summary_stub() -> str:
    return "ok"


def _batch_create_questions_stub(_args: BatchCreateQuestionsArgs) -> str:
    return "ok"


_create_question_tool = StructuredTool.from_function(
    name="create_question",
    description="创建一道新题。请提供完整题干、题型、分值、选项和正确答案。",
    args_schema=CreateQuestionArgs,
    func=_create_question_stub,
)

_edit_question_tool = StructuredTool.from_function(
    name="edit_question",
    description="编辑已有题目。通过 index 指定题目，可修改题干、分值、选项和解析。",
    args_schema=EditQuestionArgs,
    func=_edit_question_stub,
)

_delete_question_tool = StructuredTool.from_function(
    name="delete_question",
    description="删除指定索引的题目。",
    args_schema=DeleteQuestionArgs,
    func=_delete_question_stub,
)

_search_questions_tool = StructuredTool.from_function(
    name="search_questions",
    description="按关键词搜索题目题干，返回匹配题目的索引列表。",
    args_schema=SearchQuestionsArgs,
    func=_search_questions_stub,
)

_get_paper_summary_tool = StructuredTool.from_function(
    name="get_paper_summary",
    description="获取当前试卷的统计摘要：题目总数、总分、题型分布。",
    func=_get_paper_summary_stub,
)

_batch_create_questions_tool = StructuredTool.from_function(
    name="batch_create_questions",
    description="批量创建多道题目。",
    args_schema=BatchCreateQuestionsArgs,
    func=_batch_create_questions_stub,
)

TOOLS = [
    _create_question_tool,
    _edit_question_tool,
    _delete_question_tool,
    _search_questions_tool,
    _get_paper_summary_tool,
    _batch_create_questions_tool,
]


# ─── LangGraph state and graph ────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    exam_id: str
    current_questions: list[dict[str, Any]]
    pending_tool_calls: list[dict[str, Any]] | None


def _get_model() -> MyVLLMChatModel:
    return MyVLLMChatModel(
        base_url=settings.LLM_BASE_URL.rstrip("/"),
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
        temperature=0.2,
    )


def _agent_node(state: AgentState) -> Any:
    """Return the conversation history so the bound model can stream tokens."""
    return state["messages"]


def _agent_output_node(output: BaseMessage) -> AgentState:
    """Wrap the model's final message so LangGraph writes it to state."""
    return {"messages": [output]}


_AGENT_RUNNABLE = (
    RunnableLambda(_agent_node)
    | _get_model().bind_tools(TOOLS)
    | RunnableLambda(_agent_output_node)
)


_COMPILED_GRAPH: Any | None = None
_PG_CONNECTION: "psycopg.Connection[Any] | None" = None


def _get_compiled_graph() -> Any:
    """Lazy-load and compile the LangGraph agent with PostgresSaver."""
    global _COMPILED_GRAPH, _PG_CONNECTION
    if _COMPILED_GRAPH is None:
        pg_uri = str(settings.SQLALCHEMY_DATABASE_URI).replace(
            "postgresql+psycopg", "postgresql"
        )
        _PG_CONNECTION = psycopg.connect(
            pg_uri, autocommit=True, prepare_threshold=0
        )
        saver = PostgresSaver(_PG_CONNECTION)
        saver.setup()
        graph = StateGraph(AgentState)
        graph.add_node("agent", _AGENT_RUNNABLE)
        graph.set_entry_point("agent")
        graph.add_edge("agent", END)
        _COMPILED_GRAPH = graph.compile(checkpointer=saver)
    return _COMPILED_GRAPH


@atexit.register
def _close_pg_connection() -> None:
    global _PG_CONNECTION
    if _PG_CONNECTION is not None:
        try:
            _PG_CONNECTION.close()
        except Exception:
            pass
        _PG_CONNECTION = None


# ─── Thread helpers ───────────────────────────────────────────────────────────

def _thread_id(user_id: uuid.UUID, exam_id: str) -> str:
    """LangGraph checkpoint thread id; derived from the natural (user, exam) key."""
    return f"{user_id}:{exam_id}"


def _ensure_thread_metadata(
    session: Session,
    user_id: uuid.UUID,
    exam_id: str,
) -> None:
    existing = session.exec(
        select(AIAssistantThread).where(
            AIAssistantThread.user_id == user_id,
            AIAssistantThread.exam_id == uuid.UUID(exam_id),
        )
    ).first()
    if existing:
        existing.updated_at = _now_utc()
        session.add(existing)
        return
    session.add(
        AIAssistantThread(
            user_id=user_id,
            exam_id=uuid.UUID(exam_id),
        )
    )


def _touch_thread(session: Session, user_id: uuid.UUID, exam_id: str) -> None:
    row = session.exec(
        select(AIAssistantThread).where(
            AIAssistantThread.user_id == user_id,
            AIAssistantThread.exam_id == uuid.UUID(exam_id),
        )
    ).first()
    if row:
        row.updated_at = _now_utc()
        session.add(row)


# ─── Public API ───────────────────────────────────────────────────────────────

def _extract_message_chunks(stream_item: Any) -> Iterator[BaseMessage]:
    """Normalize graph.stream(..., stream_mode='messages') output.

    Depending on the LangGraph version, each streamed item is either a
    ``(messages, metadata)`` tuple or just a list of messages.
    """
    messages: Any
    if isinstance(stream_item, tuple):
        messages = stream_item[0]
    else:
        messages = stream_item

    if isinstance(messages, BaseMessage):
        yield messages
    elif isinstance(messages, list):
        for msg in messages:
            if isinstance(msg, BaseMessage):
                yield msg


def _stream_model_output(graph: Any, input_state: dict[str, Any], config: dict[str, Any]) -> Iterator[tuple[str, str]]:
    """Yield ('reasoning', delta) and ('content', delta) chunks from the model."""
    for item in graph.stream(input_state, config, stream_mode="messages"):
        for msg in _extract_message_chunks(item):
            if isinstance(msg, AIMessageChunk):
                # 提取返回的msg中的reasoning部分.如果不存在会优雅返回None而不是抛出错误.
                reasoning = msg.additional_kwargs.get("reasoning")
                if reasoning:
                    yield "reasoning", reasoning
                content = msg.content
                if content:
                    if isinstance(content, str):
                        yield "content", content
                    elif isinstance(content, list):
                        yield "content", "".join(str(c) for c in content)


def _finalize_response(
    final_state: Any | None,
) -> tuple[str | None, list[dict[str, Any]] | None]:
    """Extract the final assistant message text and any tool calls."""
    if not final_state:
        return None, None
    messages_out = final_state.values.get("messages", [])
    last_message = messages_out[-1] if messages_out else None
    if not isinstance(last_message, AIMessage):
        return None, None

    response_text = last_message.content or ""
    raw_tool_calls = getattr(last_message, "tool_calls", None) or []
    pending = None
    if raw_tool_calls:
        pending = [
            {
                "id": tc.get("id") or str(uuid.uuid4()),
                "name": tc["name"],
                "arguments": tc.get("args", {}),
            }
            for tc in raw_tool_calls
        ]
    return response_text, pending



def _build_file_message(file_context: str) -> str:
    return (
        "以下是从上传文件中提取到的参考内容（文件未保存，仅用于本次出题）：\n\n"
        f"{file_context}"
    )


def chat_stream(
    session: Session,
    user_id: uuid.UUID,
    exam_id: str,
    message: str,
    current_questions: list[dict[str, Any]],
    file_context: str | None = None,
) -> Iterator[str]:
    """Stream chat events (reasoning, content, tool-calls, done) via SSE."""
    thread_id = _thread_id(user_id, exam_id)
    config = {"configurable": {"thread_id": thread_id}}

    _ensure_thread_metadata(session, user_id, exam_id)

    graph = _get_compiled_graph()
    existing_state = graph.get_state(config)
    has_history = bool(existing_state and existing_state.values.get("messages"))
    # message.strip():将字符串的首尾空白字符去掉
    user_prompt = message.strip() if message.strip() else "请根据上传的文件内容生成相关考试题目。"
    if file_context:
        user_prompt += "\n\n" + _build_file_message(file_context)

    human_msg = _make_human_message(user_prompt, exam_id, current_questions)
    messages: list[BaseMessage] = [SystemMessage(content=_SYSTEM_PROMPT)] if not has_history else []
    messages.append(human_msg)

    input_state = {
        "messages": messages,
        "exam_id": exam_id,
        "current_questions": current_questions,
        "pending_tool_calls": None,
    }

    yield _sse_event("status", {"type": "status", "status": "thinking"})

    try:
        for chunk_type, delta in _stream_model_output(graph, input_state, config):
            if chunk_type == "reasoning":
                yield _sse_event("reasoning", {"type": "reasoning", "delta": delta})
            elif chunk_type == "content":
                yield _sse_event("content", {"type": "content", "delta": delta})
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        yield _sse_event("error", {"type": "error", "message": f"大模型服务无响应或连接失败: {exc}"})
        return
    except Exception as exc:
        yield _sse_event("error", {"type": "error", "message": f"大模型服务调用异常: {exc}"})
        return

    _touch_thread(session, user_id, exam_id)
    session.commit()

    final_state = graph.get_state(config)
    response_text, pending = _finalize_response(final_state)

    if pending:
        names = [tc.get("name") for tc in pending if tc.get("name")]
        yield _sse_event("status", {"type": "status", "status": "tool-calling", "tools": names})
        yield _sse_event("tool-calls", {"type": "tool-calls", "tool_calls": pending})

    yield _sse_event(
        "done",
        {
            "type": "done",
            "message": response_text,
            "tool_calls": pending,
        },
    )


def submit_tool_results_stream(
    session: Session,
    user_id: uuid.UUID,
    exam_id: str,
    tool_results: list[ToolResult],
    current_questions: list[dict[str, Any]],
) -> Iterator[str]:
    """Stream tool-result feedback events via SSE."""
    thread_id = _thread_id(user_id, exam_id)
    config = {"configurable": {"thread_id": thread_id}}

    tool_messages = [
        ToolMessage(content=r.content, tool_call_id=r.tool_call_id)
        for r in tool_results
    ]
    human_msg = _make_human_message(
        "已完成上述工具调用，请根据执行结果继续。", exam_id, current_questions
    )

    graph = _get_compiled_graph()
    input_state = {
        "messages": [*tool_messages, human_msg],
        "exam_id": exam_id,
        "current_questions": current_questions,
        "pending_tool_calls": None,
    }

    yield _sse_event("status", {"type": "status", "status": "thinking"})

    try:
        for chunk_type, delta in _stream_model_output(graph, input_state, config):
            if chunk_type == "reasoning":
                yield _sse_event("reasoning", {"type": "reasoning", "delta": delta})
            elif chunk_type == "content":
                yield _sse_event("content", {"type": "content", "delta": delta})
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        yield _sse_event("error", {"type": "error", "message": f"大模型服务无响应或连接失败: {exc}"})
        return
    except Exception as exc:
        yield _sse_event("error", {"type": "error", "message": f"大模型服务调用异常: {exc}"})
        return

    _touch_thread(session, user_id, exam_id)
    session.commit()

    final_state = graph.get_state(config)
    response_text, pending = _finalize_response(final_state)

    yield _sse_event(
        "done",
        {
            "type": "done",
            "message": response_text,
            "tool_calls": pending,
        },
    )


def clear_thread(
    session: Session,
    user_id: uuid.UUID,
    exam_id: str,
) -> None:
    """Delete the thread metadata and all associated LangGraph checkpoints."""
    thread_id = _thread_id(user_id, exam_id)

    # Ensure PostgresSaver tables exist before trying to delete from them.
    _get_compiled_graph()

    session.exec(
        delete(AIAssistantThread).where(
            AIAssistantThread.user_id == user_id,
            AIAssistantThread.exam_id == uuid.UUID(exam_id),
        )
    )
    session.execute(
        text("DELETE FROM checkpoints WHERE thread_id = :thread_id").bindparams(
            thread_id=thread_id
        )
    )
    session.execute(
        text("DELETE FROM checkpoint_blobs WHERE thread_id = :thread_id").bindparams(
            thread_id=thread_id
        )
    )
    session.execute(
        text("DELETE FROM checkpoint_writes WHERE thread_id = :thread_id").bindparams(
            thread_id=thread_id
        )
    )


def _sse_event(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

"""
AI Assistant API Router  (/api/v1/ai-assistant/*)

Endpoints:
  POST /ai-assistant/chat         — send a chat message, may return tool calls
  POST /ai-assistant/tool-results — feed tool execution results from the frontend
  POST /ai-assistant/clear        — delete the thread context
  GET  /ai-assistant/thread       — get thread status / message count

All endpoints require exam admin or superuser.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import SessionDep
from app.modules.ai_assistant.deps import RequireAIAssistantAccess
from app.modules.ai_assistant.schemas import (
    ChatRequest,
    ChatResponse,
    ClearThreadRequest,
    ThreadStatusResponse,
    ToolResultsRequest,
    ToolResultsResponse,
)
from app.modules.ai_assistant.service import (
    LLMUnavailableError,
    chat,
    clear_thread,
    get_thread_status,
    submit_tool_results,
)

router = APIRouter(prefix="/ai-assistant", tags=["ai-assistant"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest,
    session: SessionDep,
    current_user: RequireAIAssistantAccess,
) -> ChatResponse:
    try:
        result = chat(
            session=session,
            user_id=current_user.id,
            exam_id=request.exam_id,
            message=request.message,
            current_questions=request.current_questions,
        )
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI 助手调用失败: {exc}") from exc
    session.commit()
    return ChatResponse(**result)


@router.post("/tool-results", response_model=ToolResultsResponse)
def tool_results_endpoint(
    request: ToolResultsRequest,
    session: SessionDep,
    current_user: RequireAIAssistantAccess,
) -> ToolResultsResponse:
    try:
        result = submit_tool_results(
            session=session,
            user_id=current_user.id,
            exam_id=request.exam_id,
            tool_results=request.tool_results,
            current_questions=request.current_questions,
        )
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI 助手调用失败: {exc}") from exc
    session.commit()
    return ToolResultsResponse(**result)


@router.post("/clear")
def clear_thread_endpoint(
    request: ClearThreadRequest,
    session: SessionDep,
    current_user: RequireAIAssistantAccess,
) -> dict[str, bool]:
    try:
        clear_thread(
            session=session,
            user_id=current_user.id,
            exam_id=request.exam_id,
        )
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI 助手调用失败: {exc}") from exc
    session.commit()
    return {"success": True}


@router.get("/thread", response_model=ThreadStatusResponse)
def thread_status_endpoint(
    exam_id: str,
    session: SessionDep,
    current_user: RequireAIAssistantAccess,
) -> ThreadStatusResponse:
    try:
        result = get_thread_status(
            session=session,
            user_id=current_user.id,
            exam_id=exam_id,
        )
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI 助手调用失败: {exc}") from exc
    return ThreadStatusResponse(**result)

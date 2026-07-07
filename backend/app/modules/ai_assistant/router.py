"""
AI Assistant API Router  (/api/v1/ai-assistant/*)

Endpoints:
  POST /ai-assistant/chat/stream         — send a chat message (optional files), SSE stream
  POST /ai-assistant/tool-results/stream — feed tool execution results from the frontend, SSE stream
  POST /ai-assistant/clear               — delete the thread context for (user, exam)

All endpoints require exam admin or superuser.
"""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.deps import SessionDep
from app.modules.ai_assistant.deps import RequireAIAssistantAccess
from app.modules.ai_assistant.parser import FileContentTooLargeError, FileParseError, parse_upload_files
from app.modules.ai_assistant.schemas import ClearThreadRequest, ToolResultsRequest
from app.modules.ai_assistant.service import (
    LLMUnavailableError,
    _sse_event,
    chat_stream,
    clear_thread,
    submit_tool_results_stream,
)

router = APIRouter(prefix="/ai-assistant", tags=["ai-assistant"])


@router.post("/chat/stream")
def chat_stream_endpoint(
    session: SessionDep,
    current_user: RequireAIAssistantAccess,
    exam_id: Annotated[str, Form()],
    files: Annotated[list[UploadFile], File(default_factory=list)] = [],
    message: Annotated[str, Form()] = "",
    current_questions: Annotated[str, Form()] = "[]",
):
    try:
        questions = json.loads(current_questions)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="current_questions 格式错误") from exc

    file_context: str | None = None
    if files:
        try:
            file_context = parse_upload_files(files)
        except FileParseError as exc:
            def _error_gen(msg: str = str(exc)):
                yield _sse_event("error", {"type": "error", "message": msg})
            return StreamingResponse(
                _error_gen(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )
        except FileContentTooLargeError as exc:
            def _error_gen(msg: str = str(exc)):
                yield _sse_event("error", {"type": "error", "message": msg})
            return StreamingResponse(
                _error_gen(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )

    def event_generator():
        try:
            yield from chat_stream(
                session=session,
                user_id=current_user.id,
                exam_id=exam_id,
                message=message,
                current_questions=questions,
                file_context=file_context,
            )
        except LLMUnavailableError as exc:
            yield _sse_event("error", {"type": "error", "message": str(exc)})
        except Exception as exc:
            yield _sse_event("error", {"type": "error", "message": f"AI 助手调用失败: {exc}"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/tool-results/stream")
def tool_results_stream_endpoint(
    request: ToolResultsRequest,
    session: SessionDep,
    current_user: RequireAIAssistantAccess,
):
    def event_generator():
        try:
            yield from submit_tool_results_stream(
                session=session,
                user_id=current_user.id,
                exam_id=request.exam_id,
                tool_results=request.tool_results,
                current_questions=request.current_questions,
            )
        except Exception as exc:
            yield _sse_event("error", {"type": "error", "message": f"AI 助手调用失败: {exc}"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


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

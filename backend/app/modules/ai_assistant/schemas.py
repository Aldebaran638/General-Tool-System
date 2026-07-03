"""
AI Assistant API schemas.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class QuestionOptionArgs(BaseModel):
    option_key: str
    option_text: str
    is_correct: bool
    sort_no: int


class CreateQuestionArgs(BaseModel):
    question_type: Literal["SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"]
    stem: str
    score: float
    options: list[QuestionOptionArgs]
    analysis: str = ""


class EditQuestionArgs(BaseModel):
    index: int = Field(..., ge=0, description="Zero-based index of the question to edit")
    stem: str | None = None
    score: float | None = None
    options: list[QuestionOptionArgs] | None = None
    analysis: str | None = None


class DeleteQuestionArgs(BaseModel):
    index: int = Field(..., ge=0, description="Zero-based index of the question to delete")


class SearchQuestionsArgs(BaseModel):
    query: str = Field(..., description="Keyword to search in question stems")


class BatchCreateQuestionsArgs(BaseModel):
    questions: list[CreateQuestionArgs]


class ToolCall(BaseModel):
    id: str
    name: Literal[
        "create_question",
        "edit_question",
        "delete_question",
        "search_questions",
        "get_paper_summary",
        "batch_create_questions",
    ]
    arguments: dict[str, Any]


class ToolResult(BaseModel):
    tool_call_id: str
    content: str


class ChatRequest(BaseModel):
    exam_id: str
    message: str = ""
    current_questions: list[dict[str, Any]] = []


class ToolResultsRequest(BaseModel):
    exam_id: str
    tool_results: list[ToolResult]
    current_questions: list[dict[str, Any]] = []


class ClearThreadRequest(BaseModel):
    exam_id: str

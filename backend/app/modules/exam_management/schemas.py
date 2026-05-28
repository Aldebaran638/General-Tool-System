"""
Exam Management Module — Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlmodel import SQLModel


# ─── Exam ────────────────────────────────────────────────────────────────────

class ExamCreate(BaseModel):
    name: str
    description: str | None = None
    start_at: datetime
    end_at: datetime
    duration_minutes: int
    attempt_limit_type: str = "UNLIMITED"
    attempt_limit_count: int | None = None
    pass_score: float
    submit_rule: str = "ALL_REQUIRED"
    show_answer: bool = False
    random_question_order: bool = False
    random_option_order: bool = False


class ExamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    duration_minutes: int | None = None
    attempt_limit_type: str | None = None
    attempt_limit_count: int | None = None
    pass_score: float | None = None
    submit_rule: str | None = None
    show_answer: bool | None = None
    random_question_order: bool | None = None
    random_option_order: bool | None = None


class ExamPublic(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    status: str
    start_at: datetime
    end_at: datetime
    duration_minutes: int
    attempt_limit_type: str
    attempt_limit_count: int | None
    pass_score: float
    submit_rule: str
    show_answer: bool
    random_question_order: bool
    random_option_order: bool
    created_by: uuid.UUID
    published_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None


class ExamsPublic(BaseModel):
    data: list[ExamPublic]
    count: int


# ─── Question ────────────────────────────────────────────────────────────────

class OptionCreate(BaseModel):
    option_key: str
    option_text: str
    is_correct: bool = False
    sort_no: int = 0


class OptionPublic(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    option_key: str
    option_text: str
    is_correct: bool
    sort_no: int


class QuestionCreate(BaseModel):
    question_type: str
    stem: str
    score: float
    sort_no: int = 0
    analysis: str | None = None
    options: list[OptionCreate]


class QuestionPublic(BaseModel):
    id: uuid.UUID
    exam_id: uuid.UUID
    question_type: str
    stem: str
    score: float
    sort_no: int
    analysis: str | None
    options: list[OptionPublic]


class PaperSaveRequest(BaseModel):
    questions: list[QuestionCreate]


class PaperPublic(BaseModel):
    questions: list[QuestionPublic]
    total_score: float
    question_count: int


# ─── Exam Participant ────────────────────────────────────────────────────────

class ParticipantPublic(BaseModel):
    id: uuid.UUID
    exam_id: uuid.UUID
    userid: str
    name_snapshot: str | None
    center_snapshot: str | None
    department_snapshot: str | None
    position_snapshot: str | None
    wecom_status_snapshot: int | None
    created_at: datetime | None


class ParticipantsPublic(BaseModel):
    data: list[ParticipantPublic]
    count: int


class AddByCentersRequest(BaseModel):
    center_ids: list[int]


class AddByDepartmentsRequest(BaseModel):
    department_ids: list[int]


class AddByUsersRequest(BaseModel):
    userids: list[str]


# ─── Publish validation result ──────────────────────────────────────────────

class PublishValidation(BaseModel):
    valid: bool
    errors: list[str] = []

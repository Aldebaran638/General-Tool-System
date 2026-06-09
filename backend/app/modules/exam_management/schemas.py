"""
Exam Management Module — Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlmodel import SQLModel


# ─── Exam Category ──────────────────────────────────────────────────────────

class ExamCategoryCreate(BaseModel):
    name: str
    sort_order: int = 0


class ExamCategoryUpdate(BaseModel):
    name: str | None = None
    sort_order: int | None = None


class ExamCategoryPublic(BaseModel):
    id: int
    name: str
    sort_order: int
    created_at: datetime | None


class ExamCategoriesPublic(BaseModel):
    data: list[ExamCategoryPublic]
    count: int


# ─── Trainer Info ────────────────────────────────────────────────────────────

class TrainerInfo(BaseModel):
    id: str
    name: str


# ─── Exam ────────────────────────────────────────────────────────────────────

class ExamCreate(BaseModel):
    name: str
    trainer_ids: list[str] | None = None
    category_id: int | None = None
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
    trainer_ids: list[str] | None = None
    category_id: int | None = None
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
    trainer_ids: list[str] | None
    trainers: list[TrainerInfo] | None = None
    status: str
    category_id: int | None
    category_name: str | None
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


# ─── Exam Statistics ─────────────────────────────────────────────────────────

class ScoreDistribution(BaseModel):
    range_label: str  # "0-59", "60-69", "70-79", "80-89", "90-100"
    count: int


class ExamStatistics(BaseModel):
    total_participants: int
    completed_count: int
    passed_count: int
    failed_count: int
    not_started_count: int
    in_progress_count: int
    pass_rate: float  # percentage, e.g. 85.5
    avg_score: float | None
    max_score: float | None
    min_score: float | None
    score_distribution: list[ScoreDistribution]


class ParticipantDetail(BaseModel):
    id: uuid.UUID
    userid: str
    name_snapshot: str | None
    center_snapshot: str | None
    department_snapshot: str | None
    position_snapshot: str | None
    completion_status: str
    final_score: float | None
    final_passed: bool
    completed_at: datetime | None


class ParticipantListResponse(BaseModel):
    data: list[ParticipantDetail]
    count: int


# ─── System Dashboard ─────────────────────────────────────────────────────

class QuestionTypeCount(BaseModel):
    question_type: str
    count: int


class DeviceTypeCount(BaseModel):
    device_type: str
    count: int


class SystemDashboardStats(BaseModel):
    exam_count: int
    total_participation: int
    overall_pass_rate: float  # percentage
    question_count: int
    paper_count: int
    question_type_distribution: list[QuestionTypeCount]
    device_type_distribution: list[DeviceTypeCount]


# ─── Question Bank ──────────────────────────────────────────────────────────

class QuestionBankItem(BaseModel):
    exam_id: uuid.UUID
    exam_name: str
    category_id: int | None
    category_name: str | None
    status: str  # PENDING / GENERATED / FAILED
    generated_at: datetime | None
    question_count: int
    total_score: float


class QuestionBankPublic(BaseModel):
    data: list[QuestionBankItem]
    count: int


class QuestionBankDetail(BaseModel):
    exam_id: uuid.UUID
    exam_name: str
    questions: list[QuestionPublic]
    total_score: float
    question_count: int


# ─── Trainer Summary ─────────────────────────────────────────────────────────

class TrainerExamItem(BaseModel):
    exam_id: uuid.UUID
    exam_name: str
    center: str | None
    start_at: datetime
    participant_count: int


class TrainerGroup(BaseModel):
    trainer_id: str
    trainer_name: str
    exam_count: int
    total_participants: int
    exams: list[TrainerExamItem]


class TrainerSummaryResponse(BaseModel):
    data: list[TrainerGroup]
    count: int


# ─── My Pending Exams ────────────────────────────────────────────────────────

class MyPendingExam(BaseModel):
    id: uuid.UUID
    name: str
    start_at: datetime
    end_at: datetime
    is_in_progress: bool


class MyPendingExamsResponse(BaseModel):
    data: list[MyPendingExam]
    count: int

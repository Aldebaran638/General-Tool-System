"""
Exam Management Module — DB Models

Tables:
  exam                  — a single exam instance
  exam_category         — exam category / classification
  question              — a question belonging to an exam
  question_option       — an option belonging to a question
  exam_participant      — a user enrolled in an exam (with snapshots)
  exam_attempt          — a user's exam submission attempt
  exam_answer           — individual answers within an attempt
  exam_paper_snapshot   — frozen paper at publish time
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# =============================================================================
# Exam Category
# =============================================================================

class ExamCategory(SQLModel, table=True):
    __tablename__ = "exam_category"

    id: int = Field(primary_key=True)
    name: str = Field(max_length=128, unique=True)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )


# =============================================================================
# Exam
# =============================================================================

class Exam(SQLModel, table=True):
    __tablename__ = "exam"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    name: str = Field(max_length=255)
    trainer_ids: list[str] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    status: str = Field(default="DRAFT", max_length=16, index=True)
    # DRAFT / PUBLISHED / ARCHIVED

    # Category
    category_id: int | None = Field(default=None, foreign_key="exam_category.id", index=True)

    # Schedule
    start_at: datetime = Field(sa_type=DateTime(timezone=True))      # type: ignore[call-arg]
    end_at: datetime = Field(sa_type=DateTime(timezone=True))        # type: ignore[call-arg]
    duration_minutes: int

    # Attempt rules
    attempt_limit_type: str = Field(default="UNLIMITED", max_length=16)
    # UNLIMITED / LIMITED
    attempt_limit_count: int | None = Field(default=None)

    # Scoring
    pass_score: float
    submit_rule: str = Field(default="ALL_REQUIRED", max_length=16)
    # ALL_REQUIRED / ANY
    show_answer: bool = Field(default=False)

    # Anti-cheat
    random_question_order: bool = Field(default=False)
    random_option_order: bool = Field(default=False)

    # Ownership
    created_by: uuid.UUID = Field(foreign_key="user.id")

    # Lifecycle
    published_at: datetime | None = Field(
        default=None, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )


# =============================================================================
# Question
# =============================================================================

class Question(SQLModel, table=True):
    __tablename__ = "question"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    exam_id: uuid.UUID = Field(foreign_key="exam.id", index=True)

    question_type: str = Field(max_length=16)
    # SINGLE_CHOICE / MULTIPLE_CHOICE / TRUE_FALSE
    stem: str = Field(sa_column=Column(Text, nullable=False))
    score: float
    sort_no: int = Field(default=0)
    analysis: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )


# =============================================================================
# Question Option
# =============================================================================

class QuestionOption(SQLModel, table=True):
    __tablename__ = "question_option"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    question_id: uuid.UUID = Field(foreign_key="question.id", index=True)

    option_key: str = Field(max_length=4)   # A / B / C / D ...
    option_text: str = Field(sa_column=Column(Text, nullable=False))
    is_correct: bool = Field(default=False)
    sort_no: int = Field(default=0)

    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )


# =============================================================================
# Exam Participant
# =============================================================================

class ExamParticipant(SQLModel, table=True):
    __tablename__ = "exam_participant"
    __table_args__ = (
        UniqueConstraint("exam_id", "userid", name="uq_exam_participant_exam_userid"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    exam_id: uuid.UUID = Field(foreign_key="exam.id", index=True)
    userid: str = Field(max_length=64, index=True)

    # Snapshots (frozen at publish time)
    name_snapshot: str | None = Field(default=None, max_length=255)
    center_snapshot: str | None = Field(default=None, max_length=128)
    department_snapshot: str | None = Field(default=None, max_length=128)
    position_snapshot: str | None = Field(default=None, max_length=128)
    wecom_status_snapshot: int | None = Field(default=None)

    # Completion status
    completion_status: str = Field(default="NOT_STARTED", max_length=20)
    # NOT_STARTED / IN_PROGRESS / COMPLETED / NOT_COMPLETED
    final_score: float | None = Field(default=None)
    final_passed: bool = Field(default=False)
    final_attempt_id: uuid.UUID | None = Field(default=None, foreign_key="exam_attempt.id")
    completed_at: datetime | None = Field(
        default=None, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )

    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )


# =============================================================================
# Exam Attempt (Submission History)
# =============================================================================

class ExamAttempt(SQLModel, table=True):
    __tablename__ = "exam_attempt"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    exam_id: uuid.UUID = Field(foreign_key="exam.id", index=True)
    userid: str = Field(max_length=64, index=True)

    attempt_no: int = Field(default=1)
    status: str = Field(default="SUBMITTED", max_length=20)
    # IN_PROGRESS / SUBMITTED / AUTO_SUBMITTED / EXPIRED

    total_score: float
    max_score: float
    passed: bool
    correct_count: int
    total_count: int

    started_at: datetime | None = Field(
        default=None, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    expire_at: datetime | None = Field(
        default=None, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    submitted_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )

    # Random order snapshots
    question_order_snapshot: list[Any] | None = Field(default=None, sa_column=Column(JSON))
    option_order_snapshot: dict[str, list[Any]] | None = Field(default=None, sa_column=Column(JSON))


# =============================================================================
# Exam Answer (Individual answers within an attempt)
# =============================================================================

class ExamAnswer(SQLModel, table=True):
    __tablename__ = "exam_answer"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    attempt_id: uuid.UUID = Field(foreign_key="exam_attempt.id", index=True)
    question_id: uuid.UUID

    selected_option_ids: list[Any] = Field(sa_column=Column(JSON))
    is_correct: bool = Field(default=False)
    score_awarded: float = Field(default=0)

    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )


# =============================================================================
# Exam Paper Snapshot (Frozen at publish time)
# =============================================================================

class ExamPaperSnapshot(SQLModel, table=True):
    __tablename__ = "exam_paper_snapshot"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    exam_id: uuid.UUID = Field(foreign_key="exam.id", index=True)

    snapshot_json: dict[str, Any] = Field(sa_column=Column(JSON))
    total_score: float
    question_count: int

    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )


# =============================================================================
# Exam Paper (Docx generation tracking)
# =============================================================================

class ExamPaper(SQLModel, table=True):
    __tablename__ = "exam_paper"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    exam_id: uuid.UUID = Field(foreign_key="exam.id", index=True, unique=True)

    docx_path: str | None = Field(default=None, max_length=512)
    status: str = Field(default="PENDING", max_length=20)
    # PENDING / GENERATED / FAILED

    generated_at: datetime | None = Field(
        default=None, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )

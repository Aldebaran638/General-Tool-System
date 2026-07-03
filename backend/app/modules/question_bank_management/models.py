"""
Question Bank Management Module — DB Models

Tables:
  question_bank_set     — a reusable question bank set
  question_bank_question — a question inside a bank set
  question_bank_option   — an option belonging to a bank question
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# =============================================================================
# Question Bank Set
# =============================================================================

class QuestionBankSet(SQLModel, table=True):
    __tablename__ = "question_bank_set"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    name: str = Field(max_length=255)
    description: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )

    category_id: int | None = Field(
        default=None, foreign_key="exam_category.id", index=True
    )
    created_by: uuid.UUID = Field(foreign_key="user.id")

    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )


# =============================================================================
# Question Bank Question
# =============================================================================

class QuestionBankQuestion(SQLModel, table=True):
    __tablename__ = "question_bank_question"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    set_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("question_bank_set.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    question_type: str = Field(max_length=16)
    # SINGLE_CHOICE / MULTIPLE_CHOICE / TRUE_FALSE

    stem: str = Field(sa_column=Column(Text, nullable=False))
    score: float
    difficulty: str = Field(default="MEDIUM", max_length=10)
    # EASY / MEDIUM / HARD
    sort_no: int = Field(default=0)
    analysis: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )

    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )


# =============================================================================
# Question Bank Option
# =============================================================================

class QuestionBankOption(SQLModel, table=True):
    __tablename__ = "question_bank_option"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    question_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("question_bank_question.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    option_key: str = Field(max_length=4)
    option_text: str = Field(sa_column=Column(Text, nullable=False))
    is_correct: bool = Field(default=False)
    sort_no: int = Field(default=0)

    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )

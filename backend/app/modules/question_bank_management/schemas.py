"""
Question Bank Management Module — Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


# ─── Question Bank Set ──────────────────────────────────────────────────────

class QuestionBankSetCreate(BaseModel):
    name: str
    description: str | None = None
    category_id: int | None = None


class QuestionBankSetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category_id: int | None = None


class QuestionBankSetPublic(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    category_id: int | None
    created_by: uuid.UUID
    created_at: datetime | None
    updated_at: datetime | None


class QuestionBankSetsPublic(BaseModel):
    data: list[QuestionBankSetPublic]
    count: int


# ─── Bank Question Options ───────────────────────────────────────────────────

class BankOptionCreate(BaseModel):
    option_key: str
    option_text: str
    is_correct: bool = False
    sort_no: int = 0


class BankOptionPublic(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    option_key: str
    option_text: str
    is_correct: bool
    sort_no: int


# ─── Bank Questions ──────────────────────────────────────────────────────────

class BankQuestionCreate(BaseModel):
    question_type: str
    stem: str
    score: float
    difficulty: str = "MEDIUM"
    sort_no: int = 0
    analysis: str | None = None
    options: list[BankOptionCreate]


class BankQuestionUpdate(BaseModel):
    question_type: str | None = None
    stem: str | None = None
    score: float | None = None
    difficulty: str | None = None
    sort_no: int | None = None
    analysis: str | None = None
    options: list[BankOptionCreate] | None = None


class BankQuestionPublic(BaseModel):
    id: uuid.UUID
    set_id: uuid.UUID
    question_type: str
    stem: str
    score: float
    difficulty: str
    sort_no: int
    analysis: str | None
    options: list[BankOptionPublic]


# ─── Detail ──────────────────────────────────────────────────────────────────

class QuestionBankSetDetailPublic(QuestionBankSetPublic):
    questions: list[BankQuestionPublic]


# ─── Import into Exam ────────────────────────────────────────────────────────

class ImportQuestionBankRequest(BaseModel):
    bank_set_id: uuid.UUID
    mode: Literal["append", "overwrite"]

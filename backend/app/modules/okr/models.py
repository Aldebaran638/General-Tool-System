"""
OKR Module — DB Models

Tables:
  department — 一级部门
  objective  — OKR 目标
  key_result — 关键结果（KR），部门由负责人派生，不落列
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Column, DateTime, Text
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Department(SQLModel, table=True):
    __tablename__ = "department"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    name: str = Field(max_length=100, unique=True, index=True)
    description: str | None = Field(default=None, max_length=500)
    sort_order: int = Field(default=0)

    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )


class Objective(SQLModel, table=True):
    __tablename__ = "objective"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_by_id: uuid.UUID = Field(foreign_key="user.id")

    title: str = Field(max_length=255)
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )


class KeyResult(SQLModel, table=True):
    __tablename__ = "key_result"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    objective_id: uuid.UUID = Field(foreign_key="objective.id", index=True)
    assignee_id: uuid.UUID = Field(foreign_key="user.id", index=True)

    title: str = Field(max_length=255)
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    start_date: date
    deadline: date
    progress: int = Field(default=0, ge=0, le=100)

    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )

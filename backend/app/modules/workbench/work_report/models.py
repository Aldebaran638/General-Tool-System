from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Column, DateTime, Text
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WorkReport(SQLModel, table=True):
    __tablename__ = "work_report"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    reporter_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user.id",
        ondelete="SET NULL",
        index=True,
    )
    reporter_name: str | None = Field(default=None, max_length=255)
    reporter_email: str = Field(max_length=255)
    report_type: str = Field(max_length=16)
    period_start: date
    period_end: date
    title: str = Field(max_length=255)
    remarks: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    submitted_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )


class WorkPlan(SQLModel, table=True):
    __tablename__ = "work_plan"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    work_report_id: uuid.UUID = Field(
        foreign_key="work_report.id", ondelete="CASCADE", index=True
    )
    plan_content: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    planned_completion_date: date | None = None
    expected_result: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    support_needed: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    remarks: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    sort_order: int = 0


class TaskSummary(SQLModel, table=True):
    __tablename__ = "task_summary"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    work_report_id: uuid.UUID = Field(
        foreign_key="work_report.id", ondelete="CASCADE", index=True
    )
    work_goal: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    completion_date: date | None = None
    progress_description: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    progress: int | None = Field(default=None, ge=0, le=100)
    incomplete_reason: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    sort_order: int = 0


class WorkReview(SQLModel, table=True):
    __tablename__ = "work_review"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    work_report_id: uuid.UUID = Field(
        foreign_key="work_report.id", ondelete="CASCADE", index=True
    )
    review_module: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    review_content: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    sort_order: int = 0


class WorkReportFieldConfig(SQLModel, table=True):
    __tablename__ = "work_report_field_config"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    section: str = Field(max_length=32, index=True)
    field_key: str = Field(max_length=64)
    is_required: bool = False
    updated_by_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", ondelete="SET NULL"
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )

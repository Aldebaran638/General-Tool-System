from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import Column, DateTime, Text, UniqueConstraint
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


class WorkReportReminderRule(SQLModel, table=True):
    __tablename__ = "work_report_reminder_rule"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    report_type: str = Field(max_length=16, index=True)
    weekday: int | None = Field(default=None, ge=1, le=7)
    month_day: int | None = Field(default=None, ge=1, le=31)
    is_last_day: bool = False
    local_time: time
    timezone: str = Field(max_length=64)
    enabled: bool = True
    schedule_signature: str = Field(max_length=160, unique=True, index=True)
    created_by_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", ondelete="SET NULL"
    )
    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )


class WorkReportReminderRuleRecipient(SQLModel, table=True):
    __tablename__ = "work_report_reminder_rule_recipient"
    __table_args__ = (
        UniqueConstraint(
            "rule_id",
            "user_id",
            name="uq_work_report_reminder_rule_recipient",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    rule_id: uuid.UUID = Field(
        foreign_key="work_report_reminder_rule.id",
        ondelete="CASCADE",
        index=True,
    )
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        ondelete="CASCADE",
        index=True,
    )


class WorkReportReminderRun(SQLModel, table=True):
    __tablename__ = "work_report_reminder_run"
    __table_args__ = (
        UniqueConstraint(
            "rule_id",
            "scheduled_for",
            name="uq_work_report_reminder_run_schedule",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    rule_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="work_report_reminder_rule.id",
        ondelete="SET NULL",
        index=True,
    )
    report_type: str = Field(max_length=16)
    period_start: date
    period_end: date
    scheduled_for: datetime = Field(
        sa_type=DateTime(timezone=True),  # type: ignore[call-arg]
        index=True,
    )
    status: str = Field(default="running", max_length=16, index=True)
    target_count: int = 0
    sent_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    finished_at: datetime | None = Field(
        default=None, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )


class WorkReportReminderDelivery(SQLModel, table=True):
    __tablename__ = "work_report_reminder_delivery"
    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "user_id",
            name="uq_work_report_reminder_delivery_user",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    run_id: uuid.UUID = Field(
        foreign_key="work_report_reminder_run.id",
        ondelete="CASCADE",
        index=True,
    )
    user_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", ondelete="SET NULL", index=True
    )
    user_name: str | None = Field(default=None, max_length=255)
    receiver_open_id: str = Field(max_length=128)
    status: str = Field(default="pending", max_length=16, index=True)
    attempts: int = 0
    feishu_message_id: str | None = Field(default=None, max_length=128)
    error_code: str | None = Field(default=None, max_length=64)
    error_message: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    sent_at: datetime | None = Field(
        default=None, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )

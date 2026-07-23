from __future__ import annotations

import uuid
from datetime import date, datetime, time
from enum import Enum
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import ConfigDict, field_validator, model_validator
from sqlmodel import Field, SQLModel


class ReportType(str, Enum):
    weekly = "weekly"
    monthly = "monthly"


class WorkPlanInput(SQLModel):
    plan_content: str | None = None
    planned_completion_date: date | None = None
    expected_result: str | None = None
    support_needed: str | None = None
    remarks: str | None = None


class TaskSummaryInput(SQLModel):
    work_goal: str | None = None
    completion_date: date | None = None
    progress_description: str | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    incomplete_reason: str | None = None


class WorkReviewInput(SQLModel):
    review_module: str | None = None
    review_content: str | None = None


class WorkReportSubmit(SQLModel):
    model_config = ConfigDict(extra="forbid")

    report_type: ReportType
    period_key: str = Field(min_length=7, max_length=8)
    title: str = Field(min_length=1, max_length=255)
    remarks: str | None = None
    work_plans: list[WorkPlanInput] = Field(default_factory=list, max_length=100)
    task_summaries: list[TaskSummaryInput] = Field(
        default_factory=list, max_length=100
    )
    work_reviews: list[WorkReviewInput] = Field(default_factory=list, max_length=100)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title cannot be empty")
        return value


class ReporterBrief(SQLModel):
    id: uuid.UUID | None
    name: str | None
    email: str


class DetailCounts(SQLModel):
    work_plans: int
    task_summaries: int
    work_reviews: int


class WorkReportSubmissionResult(SQLModel):
    id: uuid.UUID
    reporter: ReporterBrief
    report_type: ReportType
    period_start: date
    period_end: date
    title: str
    remarks: str | None
    submitted_at: datetime
    submission_mode: Literal["created", "supplemented"]
    counts: DetailCounts


class WorkReportSummary(SQLModel):
    id: uuid.UUID
    reporter: ReporterBrief
    report_type: ReportType
    period_start: date
    period_end: date
    title: str
    remarks: str | None
    submitted_at: datetime
    counts: DetailCounts


class WorkReportsPublic(SQLModel):
    data: list[WorkReportSummary]
    count: int


class WorkPlanPublic(WorkPlanInput):
    id: uuid.UUID
    sort_order: int


class TaskSummaryPublic(TaskSummaryInput):
    id: uuid.UUID
    sort_order: int


class WorkReviewPublic(WorkReviewInput):
    id: uuid.UUID
    sort_order: int


class WorkReportDetail(WorkReportSummary):
    work_plans: list[WorkPlanPublic]
    task_summaries: list[TaskSummaryPublic]
    work_reviews: list[WorkReviewPublic]


class FieldConfigPublic(SQLModel):
    section: str
    field_key: str
    is_required: bool


class FieldConfigsPublic(SQLModel):
    data: list[FieldConfigPublic]


class FieldConfigUpdate(SQLModel):
    section: str = Field(max_length=32)
    field_key: str = Field(max_length=64)
    is_required: bool


class FieldConfigsUpdate(SQLModel):
    data: list[FieldConfigUpdate] = Field(min_length=1, max_length=20)


class ReminderRuleInput(SQLModel):
    report_type: ReportType
    weekday: int | None = Field(default=None, ge=1, le=7)
    month_day: int | None = Field(default=None, ge=1, le=31)
    is_last_day: bool = False
    local_time: time
    timezone: str = Field(default="Asia/Shanghai", min_length=1, max_length=64)
    enabled: bool = True
    recipient_user_ids: list[uuid.UUID] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_schedule(self) -> ReminderRuleInput:
        if self.report_type == ReportType.weekly:
            if self.weekday is None or self.month_day is not None or self.is_last_day:
                raise ValueError("Weekly reminders require only weekday")
        elif self.weekday is not None or (
            (self.month_day is None) == (not self.is_last_day)
        ):
            raise ValueError(
                "Monthly reminders require exactly one of month_day or is_last_day"
            )
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown IANA timezone") from exc
        if len(self.recipient_user_ids) != len(set(self.recipient_user_ids)):
            raise ValueError("Reminder recipients must not contain duplicates")
        return self


class ReminderRulePublic(ReminderRuleInput):
    # Legacy rules created before recipient targeting may have no recipients.
    # They remain visible, but create/update still requires at least one.
    recipient_user_ids: list[uuid.UUID] = Field(default_factory=list)
    id: uuid.UUID
    created_by_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ReminderRulesPublic(SQLModel):
    data: list[ReminderRulePublic]


class ReminderDeliveryPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    user_name: str | None
    status: str
    attempts: int
    error_code: str | None
    error_message: str | None
    sent_at: datetime | None


class ReminderRunPublic(SQLModel):
    id: uuid.UUID
    rule_id: uuid.UUID | None
    report_type: ReportType
    period_start: date
    period_end: date
    scheduled_for: datetime
    status: str
    target_count: int
    sent_count: int
    failed_count: int
    skipped_count: int
    created_at: datetime
    finished_at: datetime | None
    deliveries: list[ReminderDeliveryPublic]


class ReminderRunsPublic(SQLModel):
    data: list[ReminderRunPublic]
    count: int


class ReminderUnboundUser(SQLModel):
    id: uuid.UUID
    name: str | None
    email: str
    is_superuser: bool


class ReminderUnboundUsersPublic(SQLModel):
    data: list[ReminderUnboundUser]
    count: int


class ReminderTimezonesPublic(SQLModel):
    data: list[str]


class ReminderRecipient(SQLModel):
    id: uuid.UUID
    name: str | None
    email: str
    department_id: uuid.UUID | None
    is_feishu_linked: bool


class ReminderRecipientsPublic(SQLModel):
    data: list[ReminderRecipient]


class ReminderTestRequest(SQLModel):
    user_id: uuid.UUID


class ReminderTestRecipient(SQLModel):
    id: uuid.UUID
    name: str | None
    email: str


class ReminderTestRecipientsPublic(SQLModel):
    data: list[ReminderTestRecipient]


class ReminderTestResult(SQLModel):
    message_id: str

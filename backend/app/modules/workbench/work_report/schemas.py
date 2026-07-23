from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import ConfigDict, field_validator
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

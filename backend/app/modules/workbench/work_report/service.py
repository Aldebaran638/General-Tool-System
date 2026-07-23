from __future__ import annotations

import calendar
import re
from datetime import date, datetime, timezone
from typing import Any, Literal

from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from app.models_core import User
from app.modules.workbench.work_report.models import (
    TaskSummary,
    WorkPlan,
    WorkReport,
    WorkReportFieldConfig,
    WorkReview,
)
from app.modules.workbench.work_report.schemas import (
    DetailCounts,
    FieldConfigPublic,
    FieldConfigUpdate,
    ReporterBrief,
    ReportType,
    TaskSummaryInput,
    WorkPlanInput,
    WorkReportSubmissionResult,
    WorkReportSubmit,
    WorkReviewInput,
)

FIELD_DEFAULTS: tuple[tuple[str, str, bool], ...] = (
    ("work_plan", "plan_content", True),
    ("work_plan", "planned_completion_date", True),
    ("work_plan", "expected_result", False),
    ("work_plan", "support_needed", False),
    ("work_plan", "remarks", False),
    ("task_summary", "work_goal", True),
    ("task_summary", "completion_date", False),
    ("task_summary", "progress_description", True),
    ("task_summary", "progress", True),
    ("task_summary", "incomplete_reason", False),
    ("work_review", "review_module", True),
    ("work_review", "review_content", True),
)
SUPPORTED_FIELDS = {(section, field_key) for section, field_key, _ in FIELD_DEFAULTS}


def get_field_configs(session: Session) -> list[FieldConfigPublic]:
    configs = session.exec(
        select(WorkReportFieldConfig).order_by(
            WorkReportFieldConfig.section, WorkReportFieldConfig.field_key
        )
    ).all()
    stored = {(item.section, item.field_key): item for item in configs}
    return [
        FieldConfigPublic(
            section=section,
            field_key=field_key,
            is_required=(
                stored[(section, field_key)].is_required
                if (section, field_key) in stored
                else default_required
            ),
        )
        for section, field_key, default_required in FIELD_DEFAULTS
    ]


def update_field_configs(
    *, session: Session, updates: list[FieldConfigUpdate], current_user: User
) -> list[FieldConfigPublic]:
    keys = [(item.section, item.field_key) for item in updates]
    if len(keys) != len(set(keys)) or set(keys) != SUPPORTED_FIELDS:
        raise HTTPException(
            status_code=422,
            detail="Field configuration must contain every supported field exactly once",
        )

    existing = {
        (item.section, item.field_key): item
        for item in session.exec(select(WorkReportFieldConfig)).all()
    }
    now = datetime.now(timezone.utc)
    try:
        for update in updates:
            key = (update.section, update.field_key)
            config = existing.get(key)
            if config is None:
                config = WorkReportFieldConfig(
                    section=update.section, field_key=update.field_key
                )
            config.is_required = update.is_required
            config.updated_by_id = current_user.id
            config.updated_at = now
            session.add(config)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return get_field_configs(session)


def submit_work_report(
    *, session: Session, payload: WorkReportSubmit, current_user: User
) -> WorkReportSubmissionResult:
    period_start, period_end = _parse_period(payload.report_type, payload.period_key)
    config = {
        (item.section, item.field_key): item.is_required
        for item in get_field_configs(session)
    }
    _validate_rows(payload, config)

    try:
        # Serialize submissions by one employee so concurrent requests cannot create
        # two master rows for the same reporting period.
        session.exec(
            select(User).where(User.id == current_user.id).with_for_update()
        ).one()
        report = session.exec(
            select(WorkReport)
            .where(
                WorkReport.reporter_id == current_user.id,
                WorkReport.report_type == payload.report_type.value,
                WorkReport.period_start == period_start,
            )
            .with_for_update()
        ).first()
        submission_mode: Literal["created", "supplemented"]
        if report is None:
            report = WorkReport(
                reporter_id=current_user.id,
                reporter_name=current_user.full_name,
                reporter_email=str(current_user.email),
                report_type=payload.report_type.value,
                period_start=period_start,
                period_end=period_end,
                title=payload.title,
                remarks=_clean_text(payload.remarks),
            )
            session.add(report)
            session.flush()
            submission_mode = "created"
        else:
            report.reporter_name = current_user.full_name
            report.reporter_email = str(current_user.email)
            report.period_end = period_end
            report.title = payload.title
            report.remarks = _clean_text(payload.remarks)
            report.submitted_at = datetime.now(timezone.utc)
            session.add(report)
            submission_mode = "supplemented"

        plan_offset = _detail_count(session, WorkPlan, report.id)
        summary_offset = _detail_count(session, TaskSummary, report.id)
        review_offset = _detail_count(session, WorkReview, report.id)
        for index, row in enumerate(payload.work_plans, start=plan_offset):
            session.add(
                WorkPlan(
                    work_report_id=report.id,
                    sort_order=index,
                    **_clean_row(row),
                )
            )
        for index, row in enumerate(payload.task_summaries, start=summary_offset):
            session.add(
                TaskSummary(
                    work_report_id=report.id,
                    sort_order=index,
                    **_clean_row(row),
                )
            )
        for index, row in enumerate(payload.work_reviews, start=review_offset):
            session.add(
                WorkReview(
                    work_report_id=report.id,
                    sort_order=index,
                    **_clean_row(row),
                )
            )
        session.commit()
        session.refresh(report)
    except Exception:
        session.rollback()
        raise

    return WorkReportSubmissionResult(
        id=report.id,
        reporter=ReporterBrief(
            id=current_user.id,
            name=report.reporter_name,
            email=report.reporter_email,
        ),
        report_type=ReportType(report.report_type),
        period_start=report.period_start,
        period_end=report.period_end,
        title=report.title,
        remarks=report.remarks,
        submitted_at=report.submitted_at,
        submission_mode=submission_mode,
        counts=DetailCounts(
            work_plans=_detail_count(session, WorkPlan, report.id),
            task_summaries=_detail_count(session, TaskSummary, report.id),
            work_reviews=_detail_count(session, WorkReview, report.id),
        ),
    )


def _parse_period(report_type: ReportType, period_key: str) -> tuple[date, date]:
    try:
        if report_type == ReportType.weekly:
            match = re.fullmatch(r"(\d{4})-W(\d{2})", period_key)
            if not match:
                raise ValueError
            start = date.fromisocalendar(int(match.group(1)), int(match.group(2)), 1)
            return start, date.fromisocalendar(
                int(match.group(1)), int(match.group(2)), 7
            )
        match = re.fullmatch(r"(\d{4})-(\d{2})", period_key)
        if not match:
            raise ValueError
        year, month = int(match.group(1)), int(match.group(2))
        return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=422, detail="Invalid reporting period") from exc


def _validate_rows(
    payload: WorkReportSubmit, config: dict[tuple[str, str], bool]
) -> None:
    sections: tuple[tuple[str, list[Any]], ...] = (
        ("work_plan", list(payload.work_plans)),
        ("task_summary", list(payload.task_summaries)),
        ("work_review", list(payload.work_reviews)),
    )
    errors: list[dict[str, Any]] = []
    for section, rows in sections:
        fields = [field for cfg_section, field, _ in FIELD_DEFAULTS if cfg_section == section]
        for row_index, row in enumerate(rows):
            values = row.model_dump()
            if not any(_has_value(values.get(field)) for field in fields):
                errors.append(
                    {"section": section, "row": row_index, "field": None, "reason": "empty_row"}
                )
                continue
            for field in fields:
                if config[(section, field)] and not _has_value(values.get(field)):
                    errors.append(
                        {"section": section, "row": row_index, "field": field, "reason": "required"}
                    )
            if (
                section == "task_summary"
                and values.get("progress") is not None
                and values["progress"] < 100
                and not _has_value(values.get("incomplete_reason"))
            ):
                errors.append(
                    {
                        "section": section,
                        "row": row_index,
                        "field": "incomplete_reason",
                        "reason": "required_when_incomplete",
                    }
                )
    if errors:
        raise HTTPException(status_code=422, detail={"validation_errors": errors})


def _detail_count(session: Session, model: Any, report_id: Any) -> int:
    return int(
        session.exec(
            select(func.count()).select_from(model).where(model.work_report_id == report_id)
        ).one()
    )


def _has_value(value: Any) -> bool:
    return value is not None and (not isinstance(value, str) or bool(value.strip()))


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _clean_row(row: WorkPlanInput | TaskSummaryInput | WorkReviewInput) -> dict[str, Any]:
    return {
        key: _clean_text(value) if isinstance(value, str) else value
        for key, value in row.model_dump().items()
    }

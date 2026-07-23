from __future__ import annotations

import calendar
import time as time_module
import uuid
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, available_timezones

from fastapi import HTTPException
from loguru import logger
from sqlalchemy import delete, func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.config import settings
from app.models_core import User
from app.modules.workbench.work_report.models import (
    WorkReport,
    WorkReportReminderDelivery,
    WorkReportReminderRule,
    WorkReportReminderRuleRecipient,
    WorkReportReminderRun,
)
from app.modules.workbench.work_report.schemas import (
    ReminderDeliveryPublic,
    ReminderRecipient,
    ReminderRecipientsPublic,
    ReminderRuleInput,
    ReminderRulePublic,
    ReminderRulesPublic,
    ReminderRunPublic,
    ReminderRunsPublic,
    ReminderTestRecipient,
    ReminderTestRecipientsPublic,
    ReminderTestRequest,
    ReminderTestResult,
    ReminderUnboundUser,
    ReminderUnboundUsersPublic,
    ReportType,
)
from app.services.feishu_message import (
    FeishuMessageError,
    send_interactive_message,
)

REMINDER_GRACE = timedelta(hours=1)
MAX_SEND_ATTEMPTS = 3


def schedule_signature(payload: ReminderRuleInput) -> str:
    when = payload.local_time.isoformat(timespec="minutes")
    if payload.report_type == ReportType.weekly:
        schedule = f"weekday:{payload.weekday}"
    else:
        schedule = "last-day" if payload.is_last_day else f"month-day:{payload.month_day}"
    return f"{payload.report_type.value}:{schedule}:{when}:{payload.timezone}"


def _rule_public(
    session: Session, rule: WorkReportReminderRule
) -> ReminderRulePublic:
    recipient_user_ids = list(
        session.exec(
            select(WorkReportReminderRuleRecipient.user_id).where(
                WorkReportReminderRuleRecipient.rule_id == rule.id
            )
        ).all()
    )
    return ReminderRulePublic(
        id=rule.id,
        report_type=ReportType(rule.report_type),
        weekday=rule.weekday,
        month_day=rule.month_day,
        is_last_day=rule.is_last_day,
        local_time=rule.local_time,
        timezone=rule.timezone,
        enabled=rule.enabled,
        recipient_user_ids=recipient_user_ids,
        created_by_id=rule.created_by_id,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def list_rules(session: Session) -> ReminderRulesPublic:
    rules = session.exec(
        select(WorkReportReminderRule).order_by(
            WorkReportReminderRule.report_type,
            WorkReportReminderRule.local_time,
        )
    ).all()
    return ReminderRulesPublic(
        data=[_rule_public(session, rule) for rule in rules]
    )


def _validate_recipient_ids(
    session: Session, recipient_user_ids: list[uuid.UUID]
) -> None:
    found_ids = set(
        session.exec(
            select(User.id).where(
                User.id.in_(recipient_user_ids),
                User.is_active,
                User.feishu_open_id.is_not(None),
            )
        ).all()
    )
    if found_ids != set(recipient_user_ids):
        raise HTTPException(
            status_code=422,
            detail="All reminder recipients must be active Feishu-linked users",
        )


def _replace_rule_recipients(
    session: Session,
    rule_id: uuid.UUID,
    recipient_user_ids: list[uuid.UUID],
) -> None:
    session.exec(
        delete(WorkReportReminderRuleRecipient).where(
            WorkReportReminderRuleRecipient.rule_id == rule_id
        )
    )
    for user_id in recipient_user_ids:
        session.add(
            WorkReportReminderRuleRecipient(
                rule_id=rule_id,
                user_id=user_id,
            )
        )


def create_rule(
    *, session: Session, payload: ReminderRuleInput, current_user: User
) -> ReminderRulePublic:
    _validate_recipient_ids(session, payload.recipient_user_ids)
    rule = WorkReportReminderRule(
        **payload.model_dump(exclude={"recipient_user_ids"}),
        schedule_signature=schedule_signature(payload),
        created_by_id=current_user.id,
    )
    session.add(rule)
    try:
        session.flush()
        _replace_rule_recipients(
            session,
            rule.id,
            payload.recipient_user_ids,
        )
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="Reminder schedule already exists") from exc
    session.refresh(rule)
    return _rule_public(session, rule)


def update_rule(
    *,
    session: Session,
    rule_id: uuid.UUID,
    payload: ReminderRuleInput,
) -> ReminderRulePublic:
    rule = session.get(WorkReportReminderRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Reminder rule not found")
    _validate_recipient_ids(session, payload.recipient_user_ids)
    for key, value in payload.model_dump(
        exclude={"recipient_user_ids"}
    ).items():
        setattr(rule, key, value)
    rule.schedule_signature = schedule_signature(payload)
    rule.updated_at = datetime.now(timezone.utc)
    session.add(rule)
    try:
        _replace_rule_recipients(
            session,
            rule.id,
            payload.recipient_user_ids,
        )
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="Reminder schedule already exists") from exc
    session.refresh(rule)
    return _rule_public(session, rule)


def delete_rule(*, session: Session, rule_id: uuid.UUID) -> None:
    rule = session.get(WorkReportReminderRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Reminder rule not found")
    session.delete(rule)
    session.commit()


def list_unbound_users(session: Session) -> ReminderUnboundUsersPublic:
    users = session.exec(
        select(User)
        .where(User.is_active, User.feishu_open_id.is_(None))
        .order_by(User.full_name, User.email)
    ).all()
    data = [
        ReminderUnboundUser(
            id=user.id,
            name=user.full_name,
            email=str(user.email),
            is_superuser=user.is_superuser,
        )
        for user in users
    ]
    return ReminderUnboundUsersPublic(data=data, count=len(data))


def list_recipients(session: Session) -> ReminderRecipientsPublic:
    users = session.exec(
        select(User)
        .where(User.is_active, User.feishu_open_id.is_not(None))
        .order_by(User.full_name, User.email)
    ).all()
    return ReminderRecipientsPublic(
        data=[
            ReminderRecipient(
                id=user.id,
                name=user.full_name,
                email=str(user.email),
                department_id=user.department_id,
                is_feishu_linked=bool(user.feishu_open_id),
            )
            for user in users
        ]
    )


def timezone_names() -> list[str]:
    names = sorted(available_timezones())
    if "Asia/Shanghai" in names:
        names.remove("Asia/Shanghai")
        names.insert(0, "Asia/Shanghai")
    return names


def list_test_recipients(session: Session) -> ReminderTestRecipientsPublic:
    users = session.exec(
        select(User)
        .where(User.is_active, User.feishu_open_id.is_not(None))
        .order_by(User.full_name, User.email)
    ).all()
    return ReminderTestRecipientsPublic(
        data=[
            ReminderTestRecipient(
                id=user.id,
                name=user.full_name,
                email=str(user.email),
            )
            for user in users
        ]
    )


def send_test_reminder(
    *, session: Session, payload: ReminderTestRequest
) -> ReminderTestResult:
    recipient = session.get(User, payload.user_id)
    if not recipient or not recipient.is_active:
        raise HTTPException(status_code=404, detail="Test recipient not found")
    if not recipient.feishu_open_id:
        raise HTTPException(
            status_code=400,
            detail="Test recipient has not linked a Feishu account",
        )
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    start, end = _report_period(ReportType.weekly, now.date())
    card = _build_card(
        report_type=ReportType.weekly,
        period_start=start,
        period_end=end,
        test=True,
    )
    try:
        message_id = send_interactive_message(
            open_id=recipient.feishu_open_id,
            card=card,
            idempotency_key=f"test-{uuid.uuid4()}",
        )
    except FeishuMessageError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ReminderTestResult(message_id=message_id)


def list_runs(
    *, session: Session, skip: int, limit: int
) -> ReminderRunsPublic:
    count = int(
        session.exec(
            select(func.count()).select_from(WorkReportReminderRun)
        ).one()
    )
    runs = session.exec(
        select(WorkReportReminderRun)
        .order_by(WorkReportReminderRun.scheduled_for.desc())
        .offset(skip)
        .limit(limit)
    ).all()
    run_ids = [run.id for run in runs]
    deliveries = (
        session.exec(
            select(WorkReportReminderDelivery)
            .where(WorkReportReminderDelivery.run_id.in_(run_ids))
            .order_by(WorkReportReminderDelivery.created_at)
        ).all()
        if run_ids
        else []
    )
    delivery_map: dict[uuid.UUID, list[ReminderDeliveryPublic]] = {}
    for item in deliveries:
        delivery_map.setdefault(item.run_id, []).append(
            ReminderDeliveryPublic(
                id=item.id,
                user_id=item.user_id,
                user_name=item.user_name,
                status=item.status,
                attempts=item.attempts,
                error_code=item.error_code,
                error_message=item.error_message,
                sent_at=item.sent_at,
            )
        )
    return ReminderRunsPublic(
        data=[
            ReminderRunPublic(
                id=run.id,
                rule_id=run.rule_id,
                report_type=ReportType(run.report_type),
                period_start=run.period_start,
                period_end=run.period_end,
                scheduled_for=run.scheduled_for,
                status=run.status,
                target_count=run.target_count,
                sent_count=run.sent_count,
                failed_count=run.failed_count,
                skipped_count=run.skipped_count,
                created_at=run.created_at,
                finished_at=run.finished_at,
                deliveries=delivery_map.get(run.id, []),
            )
            for run in runs
        ],
        count=count,
    )


def scan_due_rules(*, session: Session, now_utc: datetime | None = None) -> None:
    now_utc = now_utc or datetime.now(timezone.utc)
    rules = session.exec(
        select(WorkReportReminderRule).where(WorkReportReminderRule.enabled)
    ).all()
    for rule in rules:
        scheduled_for = _due_occurrence(rule, now_utc)
        if scheduled_for is None:
            continue
        try:
            dispatch_rule(
                session=session,
                rule=rule,
                scheduled_for=scheduled_for,
            )
        except Exception:
            session.rollback()
            logger.exception("Failed to dispatch reminder rule {}", rule.id)


def _due_occurrence(
    rule: WorkReportReminderRule, now_utc: datetime
) -> datetime | None:
    zone = ZoneInfo(rule.timezone)
    local_now = now_utc.astimezone(zone)
    for candidate_date in (local_now.date(), local_now.date() - timedelta(days=1)):
        if not _matches_date(rule, candidate_date):
            continue
        candidate_local = datetime.combine(
            candidate_date, rule.local_time, tzinfo=zone
        )
        candidate_utc = candidate_local.astimezone(timezone.utc)
        elapsed = now_utc - candidate_utc
        if timedelta(0) <= elapsed <= REMINDER_GRACE:
            return candidate_utc
    return None


def _matches_date(rule: WorkReportReminderRule, value: date) -> bool:
    if rule.report_type == ReportType.weekly.value:
        return value.isoweekday() == rule.weekday
    last_day = calendar.monthrange(value.year, value.month)[1]
    target_day = last_day if rule.is_last_day else min(rule.month_day or 1, last_day)
    return value.day == target_day


def _report_period(report_type: ReportType, value: date) -> tuple[date, date]:
    if report_type == ReportType.weekly:
        start = value - timedelta(days=value.isoweekday() - 1)
        return start, start + timedelta(days=6)
    return (
        value.replace(day=1),
        value.replace(day=calendar.monthrange(value.year, value.month)[1]),
    )


def dispatch_rule(
    *,
    session: Session,
    rule: WorkReportReminderRule,
    scheduled_for: datetime,
) -> None:
    existing = session.exec(
        select(WorkReportReminderRun).where(
            WorkReportReminderRun.rule_id == rule.id,
            WorkReportReminderRun.scheduled_for == scheduled_for,
        )
    ).first()
    if existing and existing.status == "completed":
        return

    local_date = scheduled_for.astimezone(ZoneInfo(rule.timezone)).date()
    report_type = ReportType(rule.report_type)
    period_start, period_end = _report_period(report_type, local_date)
    run = existing or WorkReportReminderRun(
        rule_id=rule.id,
        report_type=rule.report_type,
        period_start=period_start,
        period_end=period_end,
        scheduled_for=scheduled_for,
    )
    if not existing:
        session.add(run)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return
        session.refresh(run)
        _create_deliveries(session=session, run=run)

    pending = session.exec(
        select(WorkReportReminderDelivery).where(
            WorkReportReminderDelivery.run_id == run.id,
            WorkReportReminderDelivery.status.in_(["pending", "failed"]),
            WorkReportReminderDelivery.attempts < MAX_SEND_ATTEMPTS,
        )
    ).all()
    for delivery in pending:
        _send_delivery(
            session=session,
            run=run,
            delivery=delivery,
            report_type=report_type,
        )
    _finish_run(session=session, run=run)


def _create_deliveries(*, session: Session, run: WorkReportReminderRun) -> None:
    recipient_ids = list(
        session.exec(
            select(WorkReportReminderRuleRecipient.user_id).where(
                WorkReportReminderRuleRecipient.rule_id == run.rule_id
            )
        ).all()
    )
    if not recipient_ids:
        run.target_count = 0
        session.add(run)
        session.commit()
        return
    users = session.exec(
        select(User).where(
            User.is_active,
            User.id.in_(recipient_ids),
        )
    ).all()
    targets = [
        user
        for user in users
        if not _has_report(
            session=session,
            user_id=user.id,
            report_type=ReportType(run.report_type),
            period_start=run.period_start,
        )
    ]
    for user in targets:
        is_linked = bool(user.feishu_open_id)
        session.add(
            WorkReportReminderDelivery(
                run_id=run.id,
                user_id=user.id,
                user_name=user.full_name or str(user.email),
                receiver_open_id=user.feishu_open_id or "",
                status="pending" if is_linked else "skipped",
                error_message=(
                    None
                    if is_linked
                    else "User has not linked a Feishu account"
                ),
            )
        )
    run.target_count = len(targets)
    session.add(run)
    session.commit()


def _has_report(
    *,
    session: Session,
    user_id: uuid.UUID,
    report_type: ReportType,
    period_start: date,
) -> bool:
    return (
        session.exec(
            select(WorkReport.id).where(
                WorkReport.reporter_id == user_id,
                WorkReport.report_type == report_type.value,
                WorkReport.period_start == period_start,
            )
        ).first()
        is not None
    )


def _send_delivery(
    *,
    session: Session,
    run: WorkReportReminderRun,
    delivery: WorkReportReminderDelivery,
    report_type: ReportType,
) -> None:
    if delivery.user_id and _has_report(
        session=session,
        user_id=delivery.user_id,
        report_type=report_type,
        period_start=run.period_start,
    ):
        delivery.status = "skipped"
        session.add(delivery)
        session.commit()
        return

    card = _build_card(
        report_type=report_type,
        period_start=run.period_start,
        period_end=run.period_end,
    )
    for attempt in range(delivery.attempts + 1, MAX_SEND_ATTEMPTS + 1):
        delivery.attempts = attempt
        try:
            delivery.feishu_message_id = send_interactive_message(
                open_id=delivery.receiver_open_id,
                card=card,
                idempotency_key=str(delivery.id),
            )
            delivery.status = "sent"
            delivery.sent_at = datetime.now(timezone.utc)
            delivery.error_code = None
            delivery.error_message = None
            session.add(delivery)
            session.commit()
            return
        except FeishuMessageError as exc:
            delivery.status = "failed"
            delivery.error_code = exc.code
            delivery.error_message = str(exc)
            session.add(delivery)
            session.commit()
            if not exc.retryable or attempt == MAX_SEND_ATTEMPTS:
                return
            time_module.sleep(attempt)


def _finish_run(*, session: Session, run: WorkReportReminderRun) -> None:
    deliveries = session.exec(
        select(WorkReportReminderDelivery).where(
            WorkReportReminderDelivery.run_id == run.id
        )
    ).all()
    run.sent_count = sum(item.status == "sent" for item in deliveries)
    run.failed_count = sum(item.status == "failed" for item in deliveries)
    run.skipped_count = sum(item.status == "skipped" for item in deliveries)
    run.status = "completed" if run.failed_count == 0 else "partial"
    run.finished_at = datetime.now(timezone.utc)
    session.add(run)
    session.commit()


def _build_card(
    *,
    report_type: ReportType,
    period_start: date,
    period_end: date,
    test: bool = False,
) -> dict[str, object]:
    label = "周报" if report_type == ReportType.weekly else "月报"
    period_key = (
        f"{period_start.isocalendar().year}-W{period_start.isocalendar().week:02d}"
        if report_type == ReportType.weekly
        else period_start.strftime("%Y-%m")
    )
    url = (
        f"{settings.FRONTEND_HOST.rstrip('/')}/work-reports/new"
        f"?reportType={report_type.value}&periodKey={period_key}"
    )
    title_prefix = "测试：" if test else ""
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "orange",
            "title": {
                "tag": "plain_text",
                "content": f"{title_prefix}{label}待提交提醒",
            },
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        f"当前尚未检测到你提交的 **{period_start:%Y-%m-%d}"
                        f" 至 {period_end:%Y-%m-%d} {label}**。"
                    ),
                },
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "type": "primary",
                        "text": {"tag": "plain_text", "content": "立即填写"},
                        "url": url,
                    }
                ],
            },
        ],
    }

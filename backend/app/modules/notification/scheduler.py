"""
Notification Module — APScheduler setup for auto reminders

Schedules:
  • Every 5 minutes → exam upcoming reminders (1 hour before start)
  • Every 1 minute  → exam started reminders
  • Every 5 minutes → exam incomplete reminders (50% duration elapsed)

The scheduler is started/stopped via the FastAPI lifespan in main.py.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import Session, select

from app.core.db import engine
from app.core.user_resolver import resolve_user_id
from app.modules.exam_management.models import Exam, ExamParticipant
from app.modules.notification.service import bulk_create_notifications, bulk_has_notification

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _send_reminders(
    session: Session,
    exam: Exam,
    notification_type: str,
    participant_filter: str | None,
    title: str,
    content: str,
) -> int:
    """Build and send reminders for an exam's participants. Returns count sent."""
    query = select(ExamParticipant).where(ExamParticipant.exam_id == exam.id)
    if participant_filter:
        query = query.where(ExamParticipant.completion_status == participant_filter)
    else:
        query = query.where(ExamParticipant.completion_status != "COMPLETED")

    participants = session.exec(query).all()

    # Resolve user_ids (individual lookup needed: may be UUID or wecom_userid)
    user_id_map: dict[str, uuid.UUID | None] = {}
    for p in participants:
        user_id = resolve_user_id(session, p.userid)
        if user_id is None:
            logger.warning(
                "[notification-scheduler] cannot resolve user_id for userid=%s, skipping",
                p.userid,
            )
            continue
        user_id_map[p.userid] = user_id

    # Batch deduplication check
    resolved_ids = [uid for uid in user_id_map.values() if uid is not None]
    already_notified = bulk_has_notification(
        session, notification_type, exam.id, resolved_ids
    )

    notifications_data = []
    for p in participants:
        user_id = user_id_map.get(p.userid)
        if user_id is None or user_id in already_notified:
            continue

        notifications_data.append(
            {
                "user_id": user_id,
                "title": title,
                "content": content,
                "notification_type": notification_type,
                "exam_id": exam.id,
                "exam_name": exam.name,
            }
        )

    if notifications_data:
        return bulk_create_notifications(session, notifications_data)
    return 0


# ─── Upcoming reminder (1 hour before exam start) ────────────────────────────

async def _run_upcoming_reminders() -> None:
    """Send reminders for exams starting in about 1 hour."""
    now = _now()
    window_start = now + timedelta(minutes=55)
    window_end = now + timedelta(minutes=65)

    logger.info("[notification-scheduler] checking upcoming exam reminders")

    try:
        with Session(engine) as session:
            exams = session.exec(
                select(Exam)
                .where(Exam.status == "PUBLISHED")
                .where(Exam.start_at >= window_start)
                .where(Exam.start_at <= window_end)
            ).all()

            for exam in exams:
                count = _send_reminders(
                    session,
                    exam,
                    "EXAM_UPCOMING",
                    "NOT_STARTED",
                    title=f"考试提醒：{exam.name}",
                    content=(
                        f"您参与的考试「{exam.name}」将在约1小时后开始，"
                        f"开始时间：{exam.start_at.strftime('%Y-%m-%d %H:%M')}，"
                        f"请做好准备。"
                    ),
                )
                if count:
                    logger.info(
                        "[notification-scheduler] sent %d upcoming reminders for exam %s (%s)",
                        count,
                        exam.id,
                        exam.name,
                    )

    except Exception:
        logger.exception("[notification-scheduler] error during upcoming reminders")


# ─── Started reminder (when exam starts) ─────────────────────────────────────

async def _run_started_reminders() -> None:
    """Send reminders when exams start."""
    now = _now()
    window_start = now - timedelta(minutes=3)
    window_end = now + timedelta(minutes=3)

    logger.info("[notification-scheduler] checking started exam reminders")

    try:
        with Session(engine) as session:
            exams = session.exec(
                select(Exam)
                .where(Exam.status == "PUBLISHED")
                .where(Exam.start_at >= window_start)
                .where(Exam.start_at <= window_end)
            ).all()

            for exam in exams:
                count = _send_reminders(
                    session,
                    exam,
                    "EXAM_STARTED",
                    "NOT_STARTED",
                    title=f"考试已开始：{exam.name}",
                    content=(
                        f"您参与的考试「{exam.name}」已经开始，"
                        f"结束时间：{exam.end_at.strftime('%Y-%m-%d %H:%M')}，"
                        f"请尽快进入考试。"
                    ),
                )
                if count:
                    logger.info(
                        "[notification-scheduler] sent %d started reminders for exam %s (%s)",
                        count,
                        exam.id,
                        exam.name,
                    )

    except Exception:
        logger.exception("[notification-scheduler] error during started reminders")


# ─── Incomplete reminder (50% duration elapsed) ──────────────────────────────

async def _run_incomplete_reminders() -> None:
    """Send reminders for exams where 50% of duration has elapsed."""
    now = _now()

    logger.info("[notification-scheduler] checking incomplete exam reminders")

    try:
        with Session(engine) as session:
            # Find currently in-progress exams
            exams = session.exec(
                select(Exam)
                .where(Exam.status == "PUBLISHED")
                .where(Exam.start_at <= now)
                .where(Exam.end_at > now)
            ).all()

            for exam in exams:
                # Check if exam has been running for >= 50% of its duration
                elapsed = now - exam.start_at
                half_duration = timedelta(minutes=exam.duration_minutes / 2)

                if elapsed < half_duration:
                    continue

                count = _send_reminders(
                    session,
                    exam,
                    "EXAM_INCOMPLETE",
                    None,  # filter: completion_status != "COMPLETED"
                    title=f"考试进行中：请尽快完成「{exam.name}」",
                    content=(
                        f"您参与的考试「{exam.name}」已进行超过50%，"
                        f"结束时间：{exam.end_at.strftime('%Y-%m-%d %H:%M')}，"
                        f"请尽快完成考试。"
                    ),
                )
                if count:
                    logger.info(
                        "[notification-scheduler] sent %d incomplete reminders for exam %s (%s)",
                        count,
                        exam.id,
                        exam.name,
                    )

    except Exception:
        logger.exception("[notification-scheduler] error during incomplete reminders")


# ─── Scheduler lifecycle ─────────────────────────────────────────────────────

def start_notification_scheduler() -> AsyncIOScheduler:
    """Start the notification reminder scheduler."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

    # Upcoming reminders: every 5 minutes
    _scheduler.add_job(
        _run_upcoming_reminders,
        trigger="interval",
        minutes=5,
        id="notification_upcoming",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Started reminders: every 1 minute
    _scheduler.add_job(
        _run_started_reminders,
        trigger="interval",
        minutes=1,
        id="notification_started",
        replace_existing=True,
        misfire_grace_time=60,
    )

    # Incomplete reminders: every 5 minutes
    _scheduler.add_job(
        _run_incomplete_reminders,
        trigger="interval",
        minutes=5,
        id="notification_incomplete",
        replace_existing=True,
        misfire_grace_time=300,
    )

    _scheduler.start()
    logger.info(
        "[notification-scheduler] scheduler started "
        "(upcoming=5min, started=1min, incomplete=5min)"
    )
    return _scheduler


def stop_notification_scheduler() -> None:
    """Stop the notification reminder scheduler."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[notification-scheduler] scheduler stopped")
    _scheduler = None

"""
Exam Management Module — APScheduler setup

Schedules:
  • Every 10 minutes → check for expired exams and generate docx papers

The scheduler is started/stopped via the FastAPI lifespan in main.py.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import Session

from app.core.db import engine

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _run_paper_generation() -> None:
    """Check for expired exams and generate docx papers."""
    from app.modules.exam_management.service import check_and_generate_expired_exam_papers

    logger.info("[exam-management] checking for expired exams to generate papers")
    try:
        with Session(engine) as session:
            check_and_generate_expired_exam_papers(session)
        logger.info("[exam-management] expired exam paper check done")
    except Exception:
        logger.exception("[exam-management] error during paper generation check")


def start_paper_scheduler() -> AsyncIOScheduler:
    """Start the exam paper generation scheduler."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

    # Check every 10 minutes for expired exams
    _scheduler.add_job(
        _run_paper_generation,
        trigger="interval",
        minutes=10,
        id="exam_paper_generation",
        replace_existing=True,
        misfire_grace_time=300,
    )

    _scheduler.start()
    logger.info("[exam-management] paper generation scheduler started (interval=10min)")
    return _scheduler


def stop_paper_scheduler() -> None:
    """Stop the exam paper generation scheduler."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[exam-management] paper generation scheduler stopped")
    _scheduler = None

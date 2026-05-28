"""
Data Sync Module — APScheduler setup

Schedules:
  • Every 30 minutes  → incremental sync (dept + member)
  • Every day 02:00   → full sync (dept + member)

The scheduler is started/stopped via the FastAPI lifespan in main.py.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import Session

from app.core.db import engine
from app.modules.data_sync.service import sync_departments, sync_members

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _run_incremental() -> None:
    logger.info("[data-sync] scheduled incremental sync starting")
    with Session(engine) as session:
        await sync_departments(session, mode="incremental", trigger_type="scheduled")
    with Session(engine) as session:
        await sync_members(session, mode="incremental", trigger_type="scheduled")
    logger.info("[data-sync] scheduled incremental sync done")


async def _run_full() -> None:
    logger.info("[data-sync] scheduled full sync starting")
    with Session(engine) as session:
        await sync_departments(session, mode="full", trigger_type="scheduled")
    with Session(engine) as session:
        await sync_members(session, mode="full", trigger_type="scheduled")
    logger.info("[data-sync] scheduled full sync done")


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

    # Incremental: every 30 minutes
    _scheduler.add_job(
        _run_incremental,
        trigger="interval",
        minutes=30,
        id="data_sync_incremental",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Full: every day at 02:00 (Shanghai time)
    _scheduler.add_job(
        _run_full,
        trigger="cron",
        hour=2,
        minute=0,
        id="data_sync_full",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    _scheduler.start()
    logger.info("[data-sync] scheduler started (incremental=30min, full=daily@02:00)")
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[data-sync] scheduler stopped")
    _scheduler = None

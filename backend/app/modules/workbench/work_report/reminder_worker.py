from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger
from sqlmodel import Session

from app.core.db import engine
from app.modules.workbench.work_report.reminder_service import scan_due_rules


def check_reminders() -> None:
    with Session(engine) as session:
        scan_due_rules(session=session)


def main() -> None:
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        check_reminders,
        "interval",
        seconds=30,
        id="work-report-reminders",
        max_instances=1,
        coalesce=True,
    )
    logger.info("Work report reminder worker started")
    check_reminders()
    scheduler.start()


if __name__ == "__main__":
    main()

"""
Public endpoints that do not require authentication.

Used by the login page and other public-facing surfaces.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.modules.data_sync.models import WecomDepartment, WecomMember
from app.modules.exam_management.models import Exam, ExamParticipant
from sqlmodel import Session

router = APIRouter(prefix="/public", tags=["public"])


class PublicStats(BaseModel):
    total_trainees: int
    total_exams: int
    passed_exams: int
    total_departments: int


def _scalar_count(session: Session, stmt) -> int:
    """Execute a COUNT() query and return the integer scalar value."""
    result = session.exec(stmt).scalar_one()
    return result or 0


@router.get("/stats", response_model=PublicStats)
def get_public_stats(session: SessionDep) -> PublicStats:
    """
    Return public platform statistics for the login page.

    These aggregates are intentionally public so the login page can display
    live numbers without requiring authentication.
    """
    total_trainees = _scalar_count(
        session,
        select(func.count())
        .select_from(WecomMember)
        .where(WecomMember.status == 1)
        .where(WecomMember.removed_at.is_(None)),
    )

    total_exams = _scalar_count(
        session,
        select(func.count())
        .select_from(Exam)
        .where(Exam.status == "PUBLISHED"),
    )

    passed_exams = _scalar_count(
        session,
        select(func.count())
        .select_from(ExamParticipant)
        .where(ExamParticipant.final_passed.is_(True)),
    )

    total_departments = _scalar_count(
        session,
        select(func.count())
        .select_from(WecomDepartment)
        .where(WecomDepartment.level > 0),
    )

    return PublicStats(
        total_trainees=total_trainees,
        total_exams=total_exams,
        passed_exams=passed_exams,
        total_departments=total_departments,
    )

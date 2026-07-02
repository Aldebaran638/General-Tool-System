from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models_core import User
from app.modules.data_sync.models import WecomDepartment, WecomMember
from app.modules.exam_management.models import Exam, ExamParticipant


def test_get_public_stats_empty(client: TestClient) -> None:
    """Public stats endpoint should return zeros when no data exists."""
    r = client.get(f"{settings.API_V1_STR}/public/stats")
    assert r.status_code == 200
    data = r.json()
    assert data == {
        "total_trainees": 0,
        "total_exams": 0,
        "passed_exams": 0,
        "total_departments": 0,
    }


def test_get_public_stats_with_data(client: TestClient, db: Session) -> None:
    """Public stats endpoint should reflect inserted test data."""
    # Re-use the seeded superuser for exam ownership.
    superuser = db.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)  # type: ignore[arg-type]
    ).first()
    assert superuser is not None

    now = datetime.now(timezone.utc)

    # Insert members
    db.add(
        WecomMember(
            userid="member_a",
            name="Member A",
            department=[],
            status=1,
        )
    )
    db.add(
        WecomMember(
            userid="member_b",
            name="Member B",
            department=[],
            status=1,
        )
    )
    # Inactive / removed members should be excluded
    db.add(
        WecomMember(
            userid="member_c",
            name="Member C",
            department=[],
            status=4,
            removed_at=now,
        )
    )

    # Insert departments (level > 0 only should count)
    db.add(WecomDepartment(id=1, name="Root", level=0))
    db.add(WecomDepartment(id=2, name="Center A", level=1))
    db.add(WecomDepartment(id=3, name="Dept B", level=2))

    # Insert exams (only PUBLISHED should count)
    draft_exam = Exam(
        name="Draft Exam",
        status="DRAFT",
        start_at=now,
        end_at=now,
        duration_minutes=30,
        pass_score=60,
        created_by=superuser.id,
    )
    published_exam = Exam(
        name="Published Exam",
        status="PUBLISHED",
        start_at=now,
        end_at=now,
        duration_minutes=30,
        pass_score=60,
        created_by=superuser.id,
    )
    db.add(draft_exam)
    db.add(published_exam)

    db.commit()
    db.refresh(published_exam)

    # Insert participants (one passed, one not)
    db.add(
        ExamParticipant(
            exam_id=published_exam.id,
            userid="member_a",
            final_passed=True,
        )
    )
    db.add(
        ExamParticipant(
            exam_id=published_exam.id,
            userid="member_b",
            final_passed=False,
        )
    )

    db.commit()

    r = client.get(f"{settings.API_V1_STR}/public/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["total_trainees"] == 2
    assert data["total_exams"] == 1
    assert data["passed_exams"] == 1
    assert data["total_departments"] == 2

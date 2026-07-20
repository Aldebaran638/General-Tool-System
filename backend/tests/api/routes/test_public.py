from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models_core import User


def test_get_public_stats_empty(client: TestClient, db: Session) -> None:
    """Public stats endpoint returns zeros for project/task counters.

    total_members reflects the number of active users currently in the test db.
    """
    active_count = db.exec(select(User.id).where(User.is_active.is_(True))).all()

    r = client.get(f"{settings.API_V1_STR}/public/stats")
    assert r.status_code == 200
    data = r.json()
    assert data == {
        "total_projects": 0,
        "total_tasks": 0,
        "completed_tasks": 0,
        "total_members": len(active_count),
    }


def test_get_public_stats_counts_active_users(client: TestClient, db: Session) -> None:
    """total_members should only count active users."""
    active_before = len(db.exec(select(User.id).where(User.is_active.is_(True))).all())

    # Add an inactive user
    inactive_user = User(
        email="inactive@example.com",
        hashed_password="secret",
        is_active=False,
    )
    db.add(inactive_user)
    db.commit()

    r = client.get(f"{settings.API_V1_STR}/public/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["total_projects"] == 0
    assert data["total_tasks"] == 0
    assert data["completed_tasks"] == 0
    # Inactive user should not change the count.
    assert data["total_members"] == active_before

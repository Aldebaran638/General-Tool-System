from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models_core import User


def test_get_public_stats_empty(client: TestClient) -> None:
    """Public stats endpoint returns zeros for project/task counters.

    total_members reflects the seeded superuser created by init_db.
    """
    r = client.get(f"{settings.API_V1_STR}/public/stats")
    assert r.status_code == 200
    data = r.json()
    assert data == {
        "total_projects": 0,
        "total_tasks": 0,
        "completed_tasks": 0,
        "total_members": 1,
    }


def test_get_public_stats_counts_active_users(client: TestClient, db: Session) -> None:
    """total_members should only count active users."""
    superuser = db.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)  # type: ignore[arg-type]
    ).first()
    assert superuser is not None

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
    # Only the seeded superuser is active.
    assert data["total_members"] == 1

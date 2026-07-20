from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.api.deps import get_db
from app.models_core import User

router = APIRouter()


@router.get("/stats")
def get_public_stats(db: Session = Depends(get_db)) -> dict[str, int]:
    """Return public-facing platform statistics for the auth landing page.

    Project and task counts are placeholders until the project-management
    module is implemented; active user count is returned for team members.
    """
    total_members = db.exec(select(User.id).where(User.is_active.is_(True))).all()
    return {
        "total_projects": 0,
        "total_tasks": 0,
        "completed_tasks": 0,
        "total_members": len(total_members),
    }

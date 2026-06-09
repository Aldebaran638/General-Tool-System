"""User ID resolution utilities.

Maps ExamParticipant.userid (wecom_userid or user UUID string) to User.id (UUID).
"""

from __future__ import annotations

import uuid

from sqlmodel import Session, select

from app.models_core import User


def resolve_user_id(session: Session, userid: str) -> uuid.UUID | None:
    """Map ExamParticipant.userid to User.id (UUID).

    First try parsing userid as a UUID (for direct user.id references).
    If that fails, look up by wecom_userid.
    """
    try:
        return uuid.UUID(userid)
    except ValueError:
        user = session.exec(
            select(User).where(User.wecom_userid == userid)
        ).first()
        return user.id if user else None

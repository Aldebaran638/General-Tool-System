"""
Notification Module — Service layer
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from app.modules.notification.models import Notification


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ─── CRUD ────────────────────────────────────────────────────────────────────

def list_notifications(
    session: Session,
    user_id: uuid.UUID,
    *,
    page: int = 1,
    limit: int = 20,
    is_read: bool | None = None,
) -> tuple[list[Notification], int]:
    """Return notifications for a user, ordered by created_at desc."""
    base = select(Notification).where(Notification.user_id == user_id)
    count_base = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id)
    )

    if is_read is not None:
        base = base.where(Notification.is_read == is_read)
        count_base = count_base.where(Notification.is_read == is_read)

    count = session.exec(count_base).one()
    offset = (page - 1) * limit
    rows = session.exec(
        base.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
    ).all()
    return list(rows), count


def get_notification(
    session: Session,
    notification_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Notification | None:
    """Get a single notification belonging to the given user."""
    return session.exec(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    ).first()


def mark_as_read(
    session: Session,
    notification: Notification,
) -> Notification:
    """Mark a notification as read."""
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = _now()
        session.add(notification)
        session.commit()
        session.refresh(notification)
    return notification


def mark_all_as_read(session: Session, user_id: uuid.UUID) -> int:
    """Mark all unread notifications for a user as read. Returns count updated."""
    now = _now()
    notifications = session.exec(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
    ).all()

    for n in notifications:
        n.is_read = True
        n.read_at = now
        session.add(n)

    if notifications:
        session.commit()
    return len(notifications)


def delete_notification(session: Session, notification: Notification) -> None:
    """Delete a notification."""
    session.delete(notification)
    session.commit()


def get_unread_count(session: Session, user_id: uuid.UUID) -> int:
    """Get the number of unread notifications for a user."""
    return session.exec(
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
    ).one()


# ─── Batch creation (used by admin actions) ─────────────────────────────────

def create_notification(
    session: Session,
    *,
    user_id: uuid.UUID,
    title: str,
    content: str,
    notification_type: str,
) -> Notification:
    """Create a single notification."""
    notification = Notification(
        user_id=user_id,
        title=title,
        content=content,
        notification_type=notification_type,
    )
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification


def bulk_create_notifications(
    session: Session,
    notifications_data: list[dict],
) -> int:
    """Bulk create notifications. Each dict must contain:
    user_id, title, content, notification_type.

    Returns count created.
    """
    notifications = []
    for data in notifications_data:
        n = Notification(
            user_id=data["user_id"],
            title=data["title"],
            content=data["content"],
            notification_type=data["notification_type"],
        )
        notifications.append(n)

    session.add_all(notifications)
    session.commit()
    return len(notifications)


# ─── Deduplication helpers ───────────────────────────────────────────────────

def has_notification(
    session: Session,
    user_id: uuid.UUID,
    notification_type: str,
) -> bool:
    """Check if a notification of the given type already exists for the user."""
    stmt = select(Notification).where(
        Notification.user_id == user_id,
        Notification.notification_type == notification_type,
    )
    return session.exec(stmt).first() is not None


def bulk_has_notification(
    session: Session,
    notification_type: str,
    user_ids: list[uuid.UUID],
) -> set[uuid.UUID]:
    """Return the set of user_ids that already have notifications of the given type."""
    if not user_ids:
        return set()

    stmt = select(Notification.user_id).where(
        Notification.notification_type == notification_type,
        Notification.user_id.in_(user_ids),
    )

    results = session.exec(stmt).all()
    return set(results)

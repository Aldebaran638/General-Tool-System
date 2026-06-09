"""
Notification Module — API Router  (/api/v1/notifications/*)

Endpoints:
  GET    /notifications           — list notifications (paginated, filterable)
  POST   /notifications/{id}/read — mark single notification as read
  POST   /notifications/read-all  — mark all notifications as read
  DELETE /notifications/{id}      — delete single notification
  GET    /notifications/unread-count — get unread count (for badge)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUser, SessionDep
from app.modules.notification.schemas import NotificationPublic, NotificationsPublic, UnreadCountResponse
from app.modules.notification.service import (
    delete_notification,
    get_notification,
    get_unread_count,
    list_notifications,
    mark_all_as_read,
    mark_as_read,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _to_public(n) -> NotificationPublic:
    return NotificationPublic(
        id=n.id,
        title=n.title,
        content=n.content,
        notification_type=n.notification_type,
        is_read=n.is_read,
        exam_id=n.exam_id,
        exam_name=n.exam_name,
        created_at=n.created_at,
        read_at=n.read_at,
    )


@router.get("", response_model=NotificationsPublic, summary="通知列表")
def list_notifications_endpoint(
    session: SessionDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    is_read: bool | None = Query(default=None, description="筛选已读/未读"),
) -> NotificationsPublic:
    notifications, count = list_notifications(
        session,
        user_id=current_user.id,
        page=page,
        limit=limit,
        is_read=is_read,
    )
    return NotificationsPublic(
        data=[_to_public(n) for n in notifications],
        count=count,
    )


@router.post("/{notification_id}/read", response_model=NotificationPublic, summary="标记已读")
def mark_read_endpoint(
    session: SessionDep,
    current_user: CurrentUser,
    notification_id: uuid.UUID,
) -> NotificationPublic:
    notification = get_notification(session, notification_id, user_id=current_user.id)
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    updated = mark_as_read(session, notification)
    return _to_public(updated)


@router.post("/read-all", summary="标记全部已读")
def mark_all_read_endpoint(
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    count = mark_all_as_read(session, user_id=current_user.id)
    return {"marked_as_read": count}


@router.delete("/{notification_id}", status_code=204, summary="删除通知")
def delete_notification_endpoint(
    session: SessionDep,
    current_user: CurrentUser,
    notification_id: uuid.UUID,
):
    notification = get_notification(session, notification_id, user_id=current_user.id)
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    delete_notification(session, notification)


@router.get("/unread-count", response_model=UnreadCountResponse, summary="未读通知数量")
def unread_count_endpoint(
    session: SessionDep,
    current_user: CurrentUser,
) -> UnreadCountResponse:
    count = get_unread_count(session, user_id=current_user.id)
    return UnreadCountResponse(count=count)

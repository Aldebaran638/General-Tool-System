"""
Notification Module — Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationPublic(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    notification_type: str
    is_read: bool
    created_at: datetime
    read_at: datetime | None


class NotificationsPublic(BaseModel):
    data: list[NotificationPublic]
    count: int


class UnreadCountResponse(BaseModel):
    count: int

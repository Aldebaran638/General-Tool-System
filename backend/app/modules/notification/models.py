"""
Notification Module — DB Models

Tables:
  notification — user notifications / in-app messages
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Text
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Notification(SQLModel, table=True):
    __tablename__ = "notification"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)

    title: str = Field(max_length=255)
    content: str = Field(sa_column=Column(Text, nullable=False))
    notification_type: str = Field(max_length=32, index=True)

    is_read: bool = Field(default=False)

    created_at: datetime = Field(
        default_factory=_utcnow, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )
    read_at: datetime | None = Field(
        default=None, sa_type=DateTime(timezone=True)  # type: ignore[call-arg]
    )

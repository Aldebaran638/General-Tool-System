"""
AI Assistant Thread metadata model.

The actual conversation state is persisted by LangGraph's PostgresSaver
(checkpoints, checkpoint_blobs, checkpoint_writes tables). This table only
keeps lightweight metadata so the application knows whether a thread exists
and when it was last active.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class AIAssistantThread(SQLModel, table=True):
    __tablename__ = "ai_assistant_thread"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True, nullable=False)
    exam_id: uuid.UUID = Field(index=True, nullable=False)
    thread_id: str = Field(max_length=128, nullable=False, unique=True)
    created_at: datetime | None = Field(
        default_factory=_now_utc,
        sa_type=DateTime(timezone=True),  # type: ignore[call-arg]
    )
    updated_at: datetime | None = Field(
        default_factory=_now_utc,
        sa_type=DateTime(timezone=True),  # type: ignore[call-arg]
    )

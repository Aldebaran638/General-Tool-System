"""
Data Sync Module — DB Models

Tables:
  wecom_department  — snapshot of WeCom department tree
  wecom_member      — snapshot of WeCom member list
  sync_task         — one record per sync execution (audit log)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Text
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# =============================================================================
# WeCom Department snapshot
# =============================================================================

class WecomDepartment(SQLModel, table=True):
    __tablename__ = "wecom_department"

    # WeCom native fields
    id: int = Field(primary_key=True)          # WeCom dept ID (integer, not UUID)
    name: str = Field(max_length=128)
    name_en: str | None = Field(default=None, max_length=128)
    parentid: int | None = Field(default=None, index=True)
    order: int = Field(default=0)

    # Hierarchy level: 1 = root child (center), 2 = first-level child (department),
    # 3+ = deeper levels (invalid for our use case). Defaults to 0 until computed.
    level: int = Field(default=0)

    # Our metadata
    synced_at: datetime = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),        # type: ignore[call-arg]
    )


# =============================================================================
# WeCom Member snapshot
# =============================================================================

class WecomMember(SQLModel, table=True):
    __tablename__ = "wecom_member"

    # WeCom native fields
    userid: str = Field(primary_key=True, max_length=64)
    name: str = Field(max_length=64)
    department: list[int] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, server_default="[]"),
    )
    avatar: str | None = Field(default=None, max_length=512)
    status: int = Field(default=1)   # 1=active  4=disabled  5=pending

    # Our metadata
    synced_at: datetime = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),        # type: ignore[call-arg]
    )
    # Null = currently in WeCom.
    # Non-null = disappeared from WeCom API on this timestamp (left/deleted).
    removed_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),        # type: ignore[call-arg]
    )


# =============================================================================
# Sync Task (execution log)
# =============================================================================

class SyncTask(SQLModel, table=True):
    __tablename__ = "sync_task"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Classification
    entity_type: str = Field(max_length=32)   # wecom_department | wecom_member
    sync_mode: str = Field(max_length=16)     # full | incremental
    trigger_type: str = Field(max_length=16)  # manual | scheduled

    # Lifecycle
    status: str = Field(default="pending", max_length=16)
    # pending → running → success | failed
    started_at: datetime = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),        # type: ignore[call-arg]
    )
    finished_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),        # type: ignore[call-arg]
    )

    # Stats (null until task finishes)
    fetched_count: int | None = Field(default=None)
    created_count: int | None = Field(default=None)
    updated_count: int | None = Field(default=None)
    deleted_count: int | None = Field(default=None)

    # Error info
    error_message: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Who triggered (null = scheduled)
    triggered_by_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user.id",
    )

    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),        # type: ignore[call-arg]
    )

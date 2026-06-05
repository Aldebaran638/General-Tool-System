"""
Data Sync Module — Pydantic response schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import SQLModel


class SyncTriggerRequest(SQLModel):
    mode: str = "full"   # "full" | "incremental"


class SyncTaskPublic(SQLModel):
    id: uuid.UUID
    entity_type: str
    sync_mode: str
    trigger_type: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    fetched_count: int | None = None
    created_count: int | None = None
    updated_count: int | None = None
    deleted_count: int | None = None
    error_message: str | None = None
    triggered_by_id: uuid.UUID | None = None
    created_at: datetime


class SyncTasksPublic(SQLModel):
    data: list[SyncTaskPublic]
    count: int


class SyncStatusPublic(SQLModel):
    """Latest task status + whether a task is currently running."""
    latest: SyncTaskPublic | None = None
    is_running: bool = False
    next_incremental_sync: datetime | None = None
    next_full_sync: datetime | None = None


class WecomDepartmentPublic(SQLModel):
    id: int
    name: str
    name_en: str | None = None
    parentid: int | None = None
    order: int = 0
    level: int = 0
    synced_at: datetime


class WecomDepartmentsPublic(SQLModel):
    data: list[WecomDepartmentPublic]
    count: int


class WecomMemberPublic(SQLModel):
    userid: str
    name: str
    is_active: bool = True
    created_at: datetime | None = None

    @classmethod
    def from_user(cls, user) -> "WecomMemberPublic":
        return cls(
            userid=user.wecom_userid or "",
            name=user.full_name or user.wecom_userid or "",
            is_active=user.is_active,
            created_at=user.created_at,
        )


class WecomMembersPublic(SQLModel):
    data: list[WecomMemberPublic]
    count: int

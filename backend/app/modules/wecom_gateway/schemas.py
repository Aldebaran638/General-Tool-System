"""Pydantic schemas for the WeCom Gateway module."""

from pydantic import BaseModel


class WecomStatusResponse(BaseModel):
    configured: bool
    token_ok: bool = False
    corp_id: str | None = None
    agent_id: str | None = None
    error: str | None = None


class WecomDepartment(BaseModel):
    id: int
    name: str
    parentid: int
    order: int = 0


class WecomSyncResult(BaseModel):
    departments_synced: int = 0
    users_synced: int = 0
    errors: list[str] = []

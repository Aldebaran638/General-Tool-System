"""
Data Sync Module — Sync service

Implements full and incremental sync for:
  • wecom_department  (企微部门)
  • wecom_member      (企微成员)

Both functions:
  1. Create a SyncTask row (status=running).
  2. Fetch from WeCom API.
  3. Upsert to DB.  Full sync also handles soft-deletions.
  4. Update the SyncTask row with results/error.
  5. Return the completed SyncTask.

Design note — incremental vs full:
  WeCom has no cursor/delta API available without special webhook permissions.
  "Incremental" here means: pull all data from WeCom and upsert, but skip
  the deletion/removal step.  It runs faster in wall-clock time only if the
  DB write phase dominates; the WeCom API call takes the same time either way.
  The distinction is useful for high-frequency scheduled runs that should not
  mark members as removed (which could race with the nightly full sync).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.core.security import get_password_hash
from app.models import User
from app.modules.data_sync.models import SyncTask, WecomDepartment
from app.services.wecom import WecomAPIError, WecomNotConfiguredError, get_wecom_client


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ─── Department sync ──────────────────────────────────────────────────────────

async def sync_departments(
    session: Session,
    *,
    mode: str = "full",
    trigger_type: str = "manual",
    triggered_by_id: uuid.UUID | None = None,
) -> SyncTask:
    """Pull WeCom department tree and upsert into wecom_department table."""

    task = SyncTask(
        entity_type="wecom_department",
        sync_mode=mode,
        trigger_type=trigger_type,
        status="running",
        triggered_by_id=triggered_by_id,
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    created = updated = deleted = 0

    try:
        client = get_wecom_client()
        departments = await client.list_departments()
        task.fetched_count = len(departments)

        now = _now()
        api_ids: set[int] = set()

        for d in departments:
            dept_id: int = d["id"]
            api_ids.add(dept_id)

            existing = session.get(WecomDepartment, dept_id)
            if existing is None:
                session.add(WecomDepartment(
                    id=dept_id,
                    name=d["name"],
                    name_en=d.get("name_en"),
                    parentid=d.get("parentid"),
                    order=d.get("order", 0),
                    synced_at=now,
                ))
                created += 1
            else:
                existing.name = d["name"]
                existing.name_en = d.get("name_en")
                existing.parentid = d.get("parentid")
                existing.order = d.get("order", 0)
                existing.synced_at = now
                session.add(existing)
                updated += 1

        # Full sync: hard-delete departments no longer in WeCom
        if mode == "full":
            all_local = session.exec(select(WecomDepartment)).all()
            for dept in all_local:
                if dept.id not in api_ids:
                    session.delete(dept)
                    deleted += 1

        session.commit()

        task.status = "success"
        task.finished_at = _now()
        task.created_count = created
        task.updated_count = updated
        task.deleted_count = deleted

    except (WecomNotConfiguredError, WecomAPIError, Exception) as exc:
        session.rollback()
        task.status = "failed"
        task.finished_at = _now()
        task.error_message = str(exc)

    session.add(task)
    session.commit()
    session.refresh(task)
    return task


# ─── Member sync ──────────────────────────────────────────────────────────────

async def sync_members(
    session: Session,
    *,
    mode: str = "full",
    trigger_type: str = "manual",
    triggered_by_id: uuid.UUID | None = None,
) -> SyncTask:
    """Pull WeCom member list and upsert into User table.

    Only touches users with wecom_userid set (i.e. WeCom-origin users).
    Local users (wecom_userid IS NULL) are never modified.
    """

    task = SyncTask(
        entity_type="wecom_member",
        sync_mode=mode,
        trigger_type=trigger_type,
        status="running",
        triggered_by_id=triggered_by_id,
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    created = updated = deleted = 0

    try:
        client = get_wecom_client()
        members = await client.list_department_users(department_id=1, fetch_child=1)
        task.fetched_count = len(members)

        api_userids: set[str] = set()

        for m in members:
            userid: str = m["userid"]
            api_userids.add(userid)

            existing = session.exec(
                select(User).where(User.wecom_userid == userid)
            ).first()

            if existing is None:
                session.add(User(
                    email=f"wecom_{userid}@wechat.work",
                    full_name=m.get("name") or userid,
                    wecom_userid=userid,
                    hashed_password=get_password_hash(uuid.uuid4().hex),
                    is_active=True,
                    is_superuser=False,
                ))
                created += 1
            else:
                existing.full_name = m.get("name") or existing.full_name
                if not existing.is_active:
                    existing.is_active = True
                session.add(existing)
                updated += 1

        # Full sync only: deactivate WeCom users no longer in API
        if mode == "full":
            active_wecom = session.exec(
                select(User).where(
                    User.wecom_userid.is_not(None),  # type: ignore[union-attr]
                    User.is_active == True,  # noqa: E712
                )
            ).all()
            for user in active_wecom:
                if user.wecom_userid not in api_userids:
                    user.is_active = False
                    session.add(user)
                    deleted += 1

        session.commit()

        task.status = "success"
        task.finished_at = _now()
        task.created_count = created
        task.updated_count = updated
        task.deleted_count = deleted

    except (WecomNotConfiguredError, WecomAPIError, Exception) as exc:
        session.rollback()
        task.status = "failed"
        task.finished_at = _now()
        task.error_message = str(exc)

    session.add(task)
    session.commit()
    session.refresh(task)
    return task

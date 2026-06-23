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
from app.modules.data_sync.models import SyncTask, WecomDepartment, WecomMember
from app.services.wecom import WecomAPIError, WecomNotConfiguredError, get_wecom_client


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ─── Department sync ──────────────────────────────────────────────────────────

def _compute_department_levels(
    departments: list[dict],
) -> dict[int, int]:
    """Compute hierarchy level for each department.

    Rules:
      - Root department (parentid is None or 0): level = 0
      - Direct child of root: level = 1 (center)
      - Child of level 1: level = 2 (department)
      - Anything deeper: level = 3 (invalid)
    """
    parent_map = {d["id"]: d.get("parentid") for d in departments}

    def _level(dept_id: int, visited: set[int] | None = None) -> int:
        if visited is None:
            visited = set()
        if dept_id in visited:
            return 3  # cycle guard
        visited.add(dept_id)

        parent_id = parent_map.get(dept_id)
        if parent_id is None or parent_id == 0:
            return 0

        parent_level = _level(parent_id, visited.copy())
        if parent_level == 0:
            return 1
        elif parent_level == 1:
            return 2
        else:
            return 3

    return {d["id"]: _level(d["id"]) for d in departments}


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

        # Pre-compute hierarchy levels for all departments
        level_map = _compute_department_levels(departments)

        now = _now()
        api_ids: set[int] = set()

        for d in departments:
            dept_id: int = d["id"]
            api_ids.add(dept_id)
            level = level_map.get(dept_id, 0)

            existing = session.get(WecomDepartment, dept_id)
            if existing is None:
                session.add(WecomDepartment(
                    id=dept_id,
                    name=d["name"],
                    name_en=d.get("name_en"),
                    parentid=d.get("parentid"),
                    order=d.get("order", 0),
                    level=level,
                    synced_at=now,
                ))
                created += 1
            else:
                existing.name = d["name"]
                existing.name_en = d.get("name_en")
                existing.parentid = d.get("parentid")
                existing.order = d.get("order", 0)
                existing.level = level
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
    """Pull WeCom member list and upsert into User and WecomMember tables.

    Only touches users with wecom_userid set (i.e. WeCom-origin users).
    Local users (wecom_userid IS NULL) are never modified.

    Member department lists are filtered to only retain department IDs whose
    level is 1 (center) or 2 (department).
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

        # Load valid department IDs (level 1 or 2) for filtering
        valid_dept_rows = session.exec(
            select(WecomDepartment.id).where(
                WecomDepartment.level.in_([1, 2])  # type: ignore[union-attr]
            )
        ).all()
        valid_dept_ids: set[int] = set(valid_dept_rows)

        now = _now()
        api_userids: set[str] = set()

        for m in members:
            userid: str = m["userid"]
            api_userids.add(userid)

            # --- Sync User ---
            existing_user = session.exec(
                select(User).where(User.wecom_userid == userid)
            ).first()

            if existing_user is None:
                session.add(User(
                    email=f"wecom_{userid}@wechat.work",
                    full_name=m.get("name") or userid,
                    wecom_userid=userid,
                    hashed_password=get_password_hash("123456"),
                    is_active=True,
                    is_superuser=False,
                ))
                created += 1
            else:
                existing_user.full_name = m.get("name") or existing_user.full_name
                if not existing_user.is_active:
                    existing_user.is_active = True
                session.add(existing_user)
                updated += 1

            # --- Sync WecomMember (with filtered departments) ---
            raw_depts: list[int] = m.get("department", [])
            filtered_depts = [d for d in raw_depts if d in valid_dept_ids]

            existing_member = session.get(WecomMember, userid)
            if existing_member is None:
                session.add(WecomMember(
                    userid=userid,
                    name=m.get("name") or userid,
                    department=filtered_depts,
                    avatar=m.get("avatar"),
                    status=m.get("status", 1),
                    synced_at=now,
                    removed_at=None,
                ))
            else:
                existing_member.name = m.get("name") or existing_member.name
                existing_member.department = filtered_depts
                existing_member.avatar = m.get("avatar")
                existing_member.status = m.get("status", 1)
                existing_member.synced_at = now
                existing_member.removed_at = None
                session.add(existing_member)

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

            # Also mark removed WecomMembers
            all_members = session.exec(select(WecomMember)).all()
            for member in all_members:
                if member.userid not in api_userids:
                    member.removed_at = now
                    session.add(member)

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

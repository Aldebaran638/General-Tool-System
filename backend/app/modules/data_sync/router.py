"""
Data Sync Module — API Router  (/api/v1/data-sync/*)

Endpoints:
  POST /data-sync/wecom-department/trigger   — manual sync trigger
  GET  /data-sync/wecom-department/tasks     — sync history (paginated)
  GET  /data-sync/wecom-department/status    — latest task + is_running flag

  POST /data-sync/wecom-member/trigger
  GET  /data-sync/wecom-member/tasks
  GET  /data-sync/wecom-member/status

All endpoints require superuser.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import func
from sqlmodel import select

from typing import Annotated

from fastapi import Depends

from app.api.deps import SessionDep, get_current_active_superuser
from app.models import User
from app.models import User
from app.modules.data_sync.models import SyncTask, WecomDepartment
from app.modules.data_sync.schemas import (
    SyncStatusPublic,
    SyncTaskPublic,
    SyncTasksPublic,
    SyncTriggerRequest,
    WecomDepartmentPublic,
    WecomDepartmentsPublic,
    WecomMemberPublic,
    WecomMembersPublic,
)
from app.modules.data_sync.service import sync_departments, sync_members
from app.modules.data_sync.scheduler import get_next_sync_times

RequireSuperuser = Annotated[User, Depends(get_current_active_superuser)]

router = APIRouter(prefix="/data-sync", tags=["data-sync"])


# ─── helpers ──────────────────────────────────────────────────────────────────

def _to_public(task: SyncTask) -> SyncTaskPublic:
    return SyncTaskPublic(
        id=task.id,
        entity_type=task.entity_type,
        sync_mode=task.sync_mode,
        trigger_type=task.trigger_type,
        status=task.status,
        started_at=task.started_at,
        finished_at=task.finished_at,
        fetched_count=task.fetched_count,
        created_count=task.created_count,
        updated_count=task.updated_count,
        deleted_count=task.deleted_count,
        error_message=task.error_message,
        triggered_by_id=task.triggered_by_id,
        created_at=task.created_at,
    )


def _latest_task(session: SessionDep, entity_type: str) -> SyncTask | None:
    return session.exec(
        select(SyncTask)
        .where(SyncTask.entity_type == entity_type)
        .order_by(SyncTask.started_at.desc())  # type: ignore[arg-type]
        .limit(1)
    ).first()


# ─── Department endpoints ─────────────────────────────────────────────────────

@router.post(
    "/wecom-department/trigger",
    response_model=SyncTaskPublic,
    summary="手动触发企微部门同步",
)
async def trigger_department_sync(
    session: SessionDep,
    current_user: RequireSuperuser,
    body: SyncTriggerRequest,
) -> SyncTaskPublic:
    task = await sync_departments(
        session=session,
        mode=body.mode,
        trigger_type="manual",
        triggered_by_id=current_user.id,
    )
    return _to_public(task)


@router.get(
    "/wecom-department/tasks",
    response_model=SyncTasksPublic,
    summary="查询企微部门同步历史",
)
def list_department_tasks(
    session: SessionDep,
    current_user: RequireSuperuser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> SyncTasksPublic:
    offset = (page - 1) * limit
    tasks = session.exec(
        select(SyncTask)
        .where(SyncTask.entity_type == "wecom_department")
        .order_by(SyncTask.started_at.desc())  # type: ignore[arg-type]
        .offset(offset)
        .limit(limit)
    ).all()
    count = session.exec(
        select(func.count()).select_from(SyncTask)
        .where(SyncTask.entity_type == "wecom_department")
    ).one()
    return SyncTasksPublic(data=[_to_public(t) for t in tasks], count=count)


@router.get(
    "/wecom-department/status",
    response_model=SyncStatusPublic,
    summary="企微部门同步最新状态",
)
def department_sync_status(
    session: SessionDep,
    current_user: RequireSuperuser,
) -> SyncStatusPublic:
    task = _latest_task(session, "wecom_department")
    is_running = task is not None and task.status == "running"
    next_sync_times = get_next_sync_times()
    return SyncStatusPublic(
        latest=_to_public(task) if task else None,
        is_running=is_running,
        next_incremental_sync=next_sync_times["next_incremental_sync"],
        next_full_sync=next_sync_times["next_full_sync"],
    )


# ─── Member endpoints ─────────────────────────────────────────────────────────

@router.post(
    "/wecom-member/trigger",
    response_model=SyncTaskPublic,
    summary="手动触发企微成员同步",
)
async def trigger_member_sync(
    session: SessionDep,
    current_user: RequireSuperuser,
    body: SyncTriggerRequest,
) -> SyncTaskPublic:
    task = await sync_members(
        session=session,
        mode=body.mode,
        trigger_type="manual",
        triggered_by_id=current_user.id,
    )
    return _to_public(task)


@router.get(
    "/wecom-member/tasks",
    response_model=SyncTasksPublic,
    summary="查询企微成员同步历史",
)
def list_member_tasks(
    session: SessionDep,
    current_user: RequireSuperuser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> SyncTasksPublic:
    offset = (page - 1) * limit
    tasks = session.exec(
        select(SyncTask)
        .where(SyncTask.entity_type == "wecom_member")
        .order_by(SyncTask.started_at.desc())  # type: ignore[arg-type]
        .offset(offset)
        .limit(limit)
    ).all()
    count = session.exec(
        select(func.count()).select_from(SyncTask)
        .where(SyncTask.entity_type == "wecom_member")
    ).one()
    return SyncTasksPublic(data=[_to_public(t) for t in tasks], count=count)


@router.get(
    "/wecom-member/status",
    response_model=SyncStatusPublic,
    summary="企微成员同步最新状态",
)
def member_sync_status(
    session: SessionDep,
    current_user: RequireSuperuser,
) -> SyncStatusPublic:
    task = _latest_task(session, "wecom_member")
    is_running = task is not None and task.status == "running"
    next_sync_times = get_next_sync_times()
    return SyncStatusPublic(
        latest=_to_public(task) if task else None,
        is_running=is_running,
        next_incremental_sync=next_sync_times["next_incremental_sync"],
        next_full_sync=next_sync_times["next_full_sync"],
    )


# ─── Synced data endpoints ───────────────────────────────────────────────────

@router.get(
    "/wecom-departments",
    response_model=WecomDepartmentsPublic,
    summary="已同步的企微部门列表",
)
def list_departments(
    session: SessionDep,
    current_user: RequireSuperuser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> WecomDepartmentsPublic:
    offset = (page - 1) * limit
    count = session.exec(select(func.count()).select_from(WecomDepartment)).one()
    rows = session.exec(
        select(WecomDepartment)
        .order_by(WecomDepartment.synced_at.desc())  # type: ignore[arg-type]
        .offset(offset)
        .limit(limit)
    ).all()
    return WecomDepartmentsPublic(
        data=[WecomDepartmentPublic.model_validate(r, from_attributes=True) for r in rows],
        count=count,
    )


@router.get(
    "/wecom-members",
    response_model=WecomMembersPublic,
    summary="已同步的企微成员列表",
)
def list_members(
    session: SessionDep,
    current_user: RequireSuperuser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, description="按姓名或 userid 搜索"),
) -> WecomMembersPublic:
    offset = (page - 1) * limit
    base = select(User).where(User.wecom_userid.is_not(None))  # type: ignore[union-attr]
    count_base = select(func.count()).select_from(User).where(User.wecom_userid.is_not(None))  # type: ignore[union-attr]
    if q:
        like = f"%{q}%"
        base = base.where(
            User.full_name.ilike(like) | User.wecom_userid.ilike(like)  # type: ignore[union-attr]
        )
        count_base = count_base.where(
            User.full_name.ilike(like) | User.wecom_userid.ilike(like)  # type: ignore[union-attr]
        )
    count = session.exec(count_base).one()
    rows = session.exec(
        base.order_by(User.created_at.desc())  # type: ignore[arg-type]
        .offset(offset)
        .limit(limit)
    ).all()
    return WecomMembersPublic(
        data=[WecomMemberPublic.from_user(r) for r in rows],
        count=count,
    )

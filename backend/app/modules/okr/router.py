"""
OKR Module — Router

端点：
  部门 CRUD + 排序（超管）
  Objective CRUD（写：超管；删除时有 KR → 409）
  KR CRUD（超管）
  我的任务：/krs/my 筛选 + /krs/{id}/progress（成员只能改自己的进度）
  聚合视图：/stats/by-department、/stats/by-user（超管）
"""

from __future__ import annotations

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models_core import Message, User
from app.modules.okr import crud
from app.modules.okr.models import Department, KeyResult
from app.modules.okr.schemas import (
    DepartmentBrief,
    DepartmentCreate,
    DepartmentPublic,
    DepartmentReorder,
    DepartmentStats,
    DepartmentStatsList,
    DepartmentUpdate,
    DepartmentsPublic,
    KeyResultCreate,
    KeyResultProgressUpdate,
    KeyResultPublic,
    KeyResultUpdate,
    KeyResultsPublic,
    ObjectiveCreate,
    ObjectiveKrsGroup,
    ObjectivePublic,
    ObjectiveUpdate,
    ObjectivesPublic,
    UserStats,
    UserStatsList,
    AssigneeBrief,
)

router = APIRouter(prefix="/okr", tags=["okr"])

SuperUser = Annotated[User, Depends(get_current_active_superuser)]

KrFilter = Literal["all", "active", "done", "due_soon", "overdue"]


# =============================================================================
# Department（全超管）
# =============================================================================

@router.get(
    "/departments",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=DepartmentsPublic,
)
def read_departments(session: SessionDep) -> DepartmentsPublic:
    departments = crud.get_departments(session=session)
    return DepartmentsPublic(
        data=[DepartmentPublic(**d.model_dump()) for d in departments],
        count=len(departments),
    )


@router.post(
    "/departments",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=DepartmentPublic,
)
def create_department(
    *, session: SessionDep, department_in: DepartmentCreate
) -> Department:
    existing = session.exec(
        select(Department).where(Department.name == department_in.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department name already exists")
    return crud.create_department(session=session, department_in=department_in)


@router.patch(
    "/departments/{department_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=DepartmentPublic,
)
def update_department(
    *, session: SessionDep, department_id: uuid.UUID, department_in: DepartmentUpdate
) -> Department:
    db_department = crud.get_department(session=session, department_id=department_id)
    if not db_department:
        raise HTTPException(status_code=404, detail="Department not found")
    if department_in.name and department_in.name != db_department.name:
        existing = session.exec(
            select(Department).where(Department.name == department_in.name)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Department name already exists")
    return crud.update_department(
        session=session, db_department=db_department, department_in=department_in
    )


@router.delete(
    "/departments/{department_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def delete_department(*, session: SessionDep, department_id: uuid.UUID) -> Message:
    db_department = crud.get_department(session=session, department_id=department_id)
    if not db_department:
        raise HTTPException(status_code=404, detail="Department not found")
    member_count = crud.count_department_members(
        session=session, department_id=department_id
    )
    if member_count > 0:
        # KR 的部门由成员派生——部门有成员就可能有 KR，一并阻止
        raise HTTPException(
            status_code=409,
            detail="Department still has members; reassign them before deleting",
        )
    crud.delete_department(session=session, db_department=db_department)
    return Message(message="Department deleted successfully")


@router.post(
    "/departments/reorder",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def reorder_departments(
    *, session: SessionDep, reorder_in: DepartmentReorder
) -> Message:
    crud.reorder_departments(session=session, ids=reorder_in.ids)
    return Message(message="Departments reordered successfully")


# =============================================================================
# Objective
# =============================================================================

@router.get(
    "/objectives",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=ObjectivesPublic,
)
def read_objectives(session: SessionDep) -> ObjectivesPublic:
    objectives = crud.get_objectives(session=session)
    return ObjectivesPublic(
        data=[
            crud.build_objective_public(session=session, objective=o)
            for o in objectives
        ],
        count=len(objectives),
    )


@router.post("/objectives", response_model=ObjectivePublic)
def create_objective(
    *, session: SessionDep, current_user: SuperUser, objective_in: ObjectiveCreate
) -> ObjectivePublic:
    objective = crud.create_objective(
        session=session, objective_in=objective_in, created_by_id=current_user.id
    )
    return crud.build_objective_public(session=session, objective=objective)


@router.patch(
    "/objectives/{objective_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=ObjectivePublic,
)
def update_objective(
    *, session: SessionDep, objective_id: uuid.UUID, objective_in: ObjectiveUpdate
) -> ObjectivePublic:
    db_objective = crud.get_objective(session=session, objective_id=objective_id)
    if not db_objective:
        raise HTTPException(status_code=404, detail="Objective not found")
    objective = crud.update_objective(
        session=session, db_objective=db_objective, objective_in=objective_in
    )
    return crud.build_objective_public(session=session, objective=objective)


@router.delete(
    "/objectives/{objective_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def delete_objective(*, session: SessionDep, objective_id: uuid.UUID) -> Message:
    db_objective = crud.get_objective(session=session, objective_id=objective_id)
    if not db_objective:
        raise HTTPException(status_code=404, detail="Objective not found")
    kr_count = crud.count_objective_krs(session=session, objective_id=objective_id)
    if kr_count > 0:
        raise HTTPException(
            status_code=409,
            detail="Objective still has key results; delete them first",
        )
    crud.delete_objective(session=session, db_objective=db_objective)
    return Message(message="Objective deleted successfully")


# =============================================================================
# KeyResult — 超管管理
# =============================================================================

@router.get(
    "/objectives/{objective_id}/krs",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=KeyResultsPublic,
)
def read_objective_krs(
    *, session: SessionDep, objective_id: uuid.UUID
) -> KeyResultsPublic:
    if not crud.get_objective(session=session, objective_id=objective_id):
        raise HTTPException(status_code=404, detail="Objective not found")
    krs = crud.get_krs_by_objective(session=session, objective_id=objective_id)
    return KeyResultsPublic(
        data=[crud.build_kr_public(session=session, kr=kr) for kr in krs],
        count=len(krs),
    )


@router.post(
    "/krs",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=KeyResultPublic,
)
def create_key_result(*, session: SessionDep, kr_in: KeyResultCreate) -> KeyResultPublic:
    if not crud.get_objective(session=session, objective_id=kr_in.objective_id):
        raise HTTPException(status_code=404, detail="Objective not found")
    if not session.get(User, kr_in.assignee_id):
        raise HTTPException(status_code=404, detail="Assignee not found")
    kr = crud.create_key_result(session=session, kr_in=kr_in)
    return crud.build_kr_public(session=session, kr=kr)


@router.patch(
    "/krs/{kr_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=KeyResultPublic,
)
def update_key_result(
    *, session: SessionDep, kr_id: uuid.UUID, kr_in: KeyResultUpdate
) -> KeyResultPublic:
    db_kr = crud.get_key_result(session=session, kr_id=kr_id)
    if not db_kr:
        raise HTTPException(status_code=404, detail="Key result not found")
    if kr_in.objective_id and not crud.get_objective(
        session=session, objective_id=kr_in.objective_id
    ):
        raise HTTPException(status_code=404, detail="Objective not found")
    if kr_in.assignee_id and not session.get(User, kr_in.assignee_id):
        raise HTTPException(status_code=404, detail="Assignee not found")
    kr = crud.update_key_result(session=session, db_kr=db_kr, kr_in=kr_in)
    return crud.build_kr_public(session=session, kr=kr)


@router.delete(
    "/krs/{kr_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def delete_key_result(*, session: SessionDep, kr_id: uuid.UUID) -> Message:
    db_kr = crud.get_key_result(session=session, kr_id=kr_id)
    if not db_kr:
        raise HTTPException(status_code=404, detail="Key result not found")
    crud.delete_key_result(session=session, db_kr=db_kr)
    return Message(message="Key result deleted successfully")


# =============================================================================
# KeyResult — 成员（我的任务）
# 注意：/krs/my 必须声明在 /krs/{kr_id} 之前，避免 "my" 被当作 uuid 匹配
# =============================================================================

@router.get("/krs/my", response_model=KeyResultsPublic)
def read_my_krs(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    kr_filter: Annotated[KrFilter, Query(alias="filter")] = "all",
) -> KeyResultsPublic:
    krs = crud.get_krs_by_assignee(
        session=session, assignee_id=current_user.id, kr_filter=kr_filter
    )
    return KeyResultsPublic(
        data=[crud.build_kr_public(session=session, kr=kr) for kr in krs],
        count=len(krs),
    )


@router.patch("/krs/{kr_id}/progress", response_model=KeyResultPublic)
def update_kr_progress(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    kr_id: uuid.UUID,
    progress_in: KeyResultProgressUpdate,
) -> KeyResultPublic:
    db_kr = crud.get_key_result(session=session, kr_id=kr_id)
    if not db_kr:
        raise HTTPException(status_code=404, detail="Key result not found")
    if not current_user.is_superuser and db_kr.assignee_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You can only update your own key results"
        )
    kr = crud.update_kr_progress(
        session=session, db_kr=db_kr, progress=progress_in.progress
    )
    return crud.build_kr_public(session=session, kr=kr)


# =============================================================================
# 聚合视图（超管）
# =============================================================================

@router.get(
    "/stats/by-department",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=DepartmentStatsList,
)
def read_stats_by_department(session: SessionDep) -> DepartmentStatsList:
    departments = crud.get_departments(session=session)
    result: list[DepartmentStats] = []
    for department in departments:
        members = list(
            session.exec(
                select(User).where(User.department_id == department.id)
            ).all()
        )
        member_ids = {m.id for m in members}
        dept_krs = [
            kr
            for kr in crud.get_all_krs(session=session)
            if kr.assignee_id in member_ids
        ]
        avg_progress = (
            round(sum(kr.progress for kr in dept_krs) / len(dept_krs))
            if dept_krs
            else 0
        )
        # KR 按 Objective 分组
        groups: dict[uuid.UUID, ObjectiveKrsGroup] = {}
        for kr in dept_krs:
            group = groups.get(kr.objective_id)
            if group is None:
                objective = crud.get_objective(
                    session=session, objective_id=kr.objective_id
                )
                group = ObjectiveKrsGroup(
                    objective_id=kr.objective_id,
                    objective_title=objective.title if objective else "",
                    krs=[],
                )
                groups[kr.objective_id] = group
            group.krs.append(crud.build_kr_public(session=session, kr=kr))
        result.append(
            DepartmentStats(
                department=DepartmentBrief(id=department.id, name=department.name),
                member_count=len(members),
                kr_count=len(dept_krs),
                avg_progress=avg_progress,
                objective_count=len(groups),
                objectives=list(groups.values()),
            )
        )
    return DepartmentStatsList(data=result)


@router.get(
    "/stats/by-user",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserStatsList,
)
def read_stats_by_user(session: SessionDep) -> UserStatsList:
    users = crud.get_active_members(session=session)
    result: list[UserStats] = []
    for user in users:
        krs = crud.get_krs_by_assignee(session=session, assignee_id=user.id)
        avg_progress = (
            round(sum(kr.progress for kr in krs) / len(krs)) if krs else 0
        )
        department_brief = None
        if user.department_id:
            department = crud.get_department(
                session=session, department_id=user.department_id
            )
            if department:
                department_brief = DepartmentBrief(
                    id=department.id, name=department.name
                )
        result.append(
            UserStats(
                user=AssigneeBrief(
                    id=user.id, full_name=user.full_name, email=user.email
                ),
                department=department_brief,
                kr_count=len(krs),
                avg_progress=avg_progress,
                krs=[crud.build_kr_public(session=session, kr=kr) for kr in krs],
            )
        )
    return UserStatsList(data=result)

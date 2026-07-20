"""
OKR Module — Overview Router

OKR 总览家族：Objective CRUD、Objective 下 KR 列表，
以及总览下两个看板的数据端点：
  GET /overview/departments — 部门项目管理（按部门聚合）
  GET /overview/members     — 人员项目管理（按成员聚合）
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep, get_current_active_superuser
from app.models_core import Message, User
from app.modules.okr import crud
from app.modules.okr.schemas import (
    AssigneeBrief,
    DepartmentBrief,
    DepartmentStats,
    DepartmentStatsList,
    KeyResultsPublic,
    ObjectiveCreate,
    ObjectiveKrsGroup,
    ObjectivePublic,
    ObjectivesPublic,
    ObjectiveUpdate,
    UserStats,
    UserStatsList,
)

router = APIRouter()

SuperUser = Annotated[User, Depends(get_current_active_superuser)]


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


# =============================================================================
# 看板聚合视图（超管）：OKR 总览 → 部门/人员项目管理
# =============================================================================

@router.get(
    "/overview/departments",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=DepartmentStatsList,
)
def read_overview_departments(session: SessionDep) -> DepartmentStatsList:
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
    "/overview/members",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserStatsList,
)
def read_overview_members(session: SessionDep) -> UserStatsList:
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

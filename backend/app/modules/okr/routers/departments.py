"""
OKR Module — Department Router

部门 CRUD + 排序（全部仅超管）。
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep, get_current_active_superuser
from app.models_core import Message
from app.modules.okr import crud
from app.modules.okr.models import Department
from app.modules.okr.schemas import (
    DepartmentCreate,
    DepartmentPublic,
    DepartmentReorder,
    DepartmentsPublic,
    DepartmentUpdate,
)

router = APIRouter()


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

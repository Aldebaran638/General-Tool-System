"""
OKR Module — CRUD

函数式 CRUD，风格参照 app/crud.py。
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlmodel import Session, func, select

from app.models_core import User
from app.modules.okr.models import Department, KeyResult, Objective
from app.modules.okr.schemas import (
    AssigneeBrief,
    DepartmentBrief,
    DepartmentCreate,
    DepartmentUpdate,
    KeyResultCreate,
    KeyResultPublic,
    KeyResultUpdate,
    ObjectiveCreate,
    ObjectivePublic,
    ObjectiveTimeRange,
    ObjectiveUpdate,
)

DUE_SOON_DAYS = 3  # “即将到期”阈值：3 天内


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# =============================================================================
# Department
# =============================================================================

def get_departments(*, session: Session) -> list[Department]:
    return list(
        session.exec(select(Department).order_by(Department.sort_order)).all()
    )


def get_department(*, session: Session, department_id: uuid.UUID) -> Department | None:
    return session.get(Department, department_id)


def create_department(*, session: Session, department_in: DepartmentCreate) -> Department:
    max_order = session.exec(select(func.max(Department.sort_order))).one()
    db_obj = Department.model_validate(
        department_in, update={"sort_order": (max_order or 0) + 1}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_department(
    *, session: Session, db_department: Department, department_in: DepartmentUpdate
) -> Department:
    data = department_in.model_dump(exclude_unset=True)
    db_department.sqlmodel_update(data)
    session.add(db_department)
    session.commit()
    session.refresh(db_department)
    return db_department


def count_department_members(*, session: Session, department_id: uuid.UUID) -> int:
    return session.exec(
        select(func.count())
        .select_from(User)
        .where(User.department_id == department_id)
    ).one()


def delete_department(*, session: Session, db_department: Department) -> None:
    session.delete(db_department)
    session.commit()


def reorder_departments(*, session: Session, ids: list[uuid.UUID]) -> None:
    for index, department_id in enumerate(ids):
        db_obj = session.get(Department, department_id)
        if db_obj:
            db_obj.sort_order = index
            session.add(db_obj)
    session.commit()


# =============================================================================
# Objective
# =============================================================================

def get_objectives(*, session: Session) -> list[Objective]:
    return list(session.exec(select(Objective).order_by(Objective.created_at)).all())


def get_objective(*, session: Session, objective_id: uuid.UUID) -> Objective | None:
    return session.get(Objective, objective_id)


def create_objective(
    *, session: Session, objective_in: ObjectiveCreate, created_by_id: uuid.UUID
) -> Objective:
    db_obj = Objective.model_validate(
        objective_in, update={"created_by_id": created_by_id}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_objective(
    *, session: Session, db_objective: Objective, objective_in: ObjectiveUpdate
) -> Objective:
    data = objective_in.model_dump(exclude_unset=True)
    db_objective.sqlmodel_update(data, update={"updated_at": _utcnow()})
    session.add(db_objective)
    session.commit()
    session.refresh(db_objective)
    return db_objective


def count_objective_krs(*, session: Session, objective_id: uuid.UUID) -> int:
    return session.exec(
        select(func.count())
        .select_from(KeyResult)
        .where(KeyResult.objective_id == objective_id)
    ).one()


def delete_objective(*, session: Session, db_objective: Objective) -> None:
    session.delete(db_objective)
    session.commit()


def build_objective_public(*, session: Session, objective: Objective) -> ObjectivePublic:
    """附计算字段：progress（KR 均值）、kr_count、time_range"""
    stats = session.exec(
        select(
            func.count(),
            func.coalesce(func.avg(KeyResult.progress), 0),
            func.min(KeyResult.start_date),
            func.max(KeyResult.deadline),
        ).where(KeyResult.objective_id == objective.id)
    ).one()
    kr_count, avg_progress, min_start, max_deadline = stats
    time_range = None
    if kr_count > 0 and min_start and max_deadline:
        time_range = ObjectiveTimeRange(start=min_start, end=max_deadline)
    return ObjectivePublic(
        **objective.model_dump(),
        progress=round(avg_progress),
        kr_count=kr_count,
        time_range=time_range,
    )


# =============================================================================
# KeyResult
# =============================================================================

def get_key_result(*, session: Session, kr_id: uuid.UUID) -> KeyResult | None:
    return session.get(KeyResult, kr_id)


def get_krs_by_objective(*, session: Session, objective_id: uuid.UUID) -> list[KeyResult]:
    return list(
        session.exec(
            select(KeyResult)
            .where(KeyResult.objective_id == objective_id)
            .order_by(KeyResult.created_at)
        ).all()
    )


def get_krs_by_assignee(
    *, session: Session, assignee_id: uuid.UUID, kr_filter: str = "all"
) -> list[KeyResult]:
    statement = select(KeyResult).where(KeyResult.assignee_id == assignee_id)
    today = date.today()
    if kr_filter == "active":  # 未到 100%
        statement = statement.where(KeyResult.progress < 100)
    elif kr_filter == "done":  # 已达 100%
        statement = statement.where(KeyResult.progress >= 100)
    elif kr_filter == "due_soon":  # 即将到期：3 天内且未到 100%
        statement = statement.where(
            KeyResult.progress < 100,
            KeyResult.deadline >= today,
            KeyResult.deadline <= today + timedelta(days=DUE_SOON_DAYS),
        )
    elif kr_filter == "overdue":  # 已超期：过了 DDL 且未到 100%
        statement = statement.where(
            KeyResult.progress < 100, KeyResult.deadline < today
        )
    return list(session.exec(statement.order_by(KeyResult.deadline)).all())


def create_key_result(*, session: Session, kr_in: KeyResultCreate) -> KeyResult:
    db_obj = KeyResult.model_validate(kr_in)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_key_result(
    *, session: Session, db_kr: KeyResult, kr_in: KeyResultUpdate
) -> KeyResult:
    data = kr_in.model_dump(exclude_unset=True)
    db_kr.sqlmodel_update(data, update={"updated_at": _utcnow()})
    session.add(db_kr)
    session.commit()
    session.refresh(db_kr)
    return db_kr


def update_kr_progress(
    *, session: Session, db_kr: KeyResult, progress: int
) -> KeyResult:
    db_kr.progress = progress
    db_kr.updated_at = _utcnow()
    session.add(db_kr)
    session.commit()
    session.refresh(db_kr)
    return db_kr


def delete_key_result(*, session: Session, db_kr: KeyResult) -> None:
    session.delete(db_kr)
    session.commit()


def build_kr_public(*, session: Session, kr: KeyResult) -> KeyResultPublic:
    """拼装 KR 响应：assignee 快照 + department 从负责人当前部门派生"""
    assignee = session.get(User, kr.assignee_id)
    if assignee is None:  # 负责人被删除的兜底（外键未加 ON DELETE 约束时防御）
        assignee_brief = AssigneeBrief(id=kr.assignee_id, full_name=None, email="")
        department_brief = None
    else:
        assignee_brief = AssigneeBrief(
            id=assignee.id, full_name=assignee.full_name, email=assignee.email
        )
        department_brief = None
        if assignee.department_id:
            department = session.get(Department, assignee.department_id)
            if department:
                department_brief = DepartmentBrief(
                    id=department.id, name=department.name
                )
    return KeyResultPublic(
        **kr.model_dump(), assignee=assignee_brief, department=department_brief
    )


# =============================================================================
# 聚合视图
# =============================================================================

def get_all_krs(*, session: Session) -> list[KeyResult]:
    return list(session.exec(select(KeyResult)).all())


def get_active_members(*, session: Session) -> list[User]:
    """参与人员视角统计的成员：普通成员 + 超管（有 KR 或所属部门的都会出现）"""
    return list(session.exec(select(User).order_by(User.created_at)).all())

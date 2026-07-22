"""
OKR Module — API Schemas (non-table models)
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlmodel import Field, SQLModel

# =============================================================================
# Department
# =============================================================================

class DepartmentBase(SQLModel):
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class DepartmentPublic(DepartmentBase):
    id: uuid.UUID
    sort_order: int
    created_at: datetime


class DepartmentsPublic(SQLModel):
    data: list[DepartmentPublic]
    count: int


class DepartmentReorder(SQLModel):
    """按数组顺序重排部门 sort_order"""

    ids: list[uuid.UUID]


# =============================================================================
# Objective
# =============================================================================

class ObjectiveBase(SQLModel):
    title: str = Field(max_length=255)
    description: str | None = None


class ObjectiveCreate(ObjectiveBase):
    pass


class ObjectiveUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None


class ObjectiveTimeRange(SQLModel):
    """由 KR 计算出的时间范围；无 KR 时为 null"""

    start: date
    end: date


class ObjectivePublic(ObjectiveBase):
    id: uuid.UUID
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    # 计算字段
    progress: int = 0
    kr_count: int = 0
    time_range: ObjectiveTimeRange | None = None


class ObjectivesPublic(SQLModel):
    data: list[ObjectivePublic]
    count: int


# =============================================================================
# KeyResult
# =============================================================================

class KeyResultBase(SQLModel):
    title: str = Field(max_length=255)
    description: str | None = None
    start_date: date
    deadline: date
    progress: int = Field(default=0, ge=0, le=100)


class KeyResultCreate(KeyResultBase):
    objective_id: uuid.UUID
    assignee_id: uuid.UUID


class KeyResultUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    start_date: date | None = None
    deadline: date | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    objective_id: uuid.UUID | None = None
    assignee_id: uuid.UUID | None = None


class KeyResultProgressUpdate(SQLModel):
    """成员更新自己 KR 进度的专用 schema——只放行 progress 字段"""

    progress: int = Field(ge=0, le=100)


class AssigneeBrief(SQLModel):
    id: uuid.UUID
    full_name: str | None
    email: str


class DepartmentBrief(SQLModel):
    id: uuid.UUID
    name: str


class KeyResultPublic(KeyResultBase):
    id: uuid.UUID
    objective_id: uuid.UUID
    assignee: AssigneeBrief
    department: DepartmentBrief | None = None  # 由负责人派生
    created_at: datetime
    updated_at: datetime


class KeyResultsPublic(SQLModel):
    data: list[KeyResultPublic]
    count: int


# =============================================================================
# 聚合视图
# =============================================================================

class ObjectiveKrsGroup(SQLModel):
    """部门视角：某个 Objective 下属于该部门的 KR"""

    objective_id: uuid.UUID
    objective_title: str
    krs: list[KeyResultPublic]


class DepartmentStats(SQLModel):
    department: DepartmentBrief
    member_count: int
    kr_count: int
    avg_progress: int
    objective_count: int
    objectives: list[ObjectiveKrsGroup]


class DepartmentStatsList(SQLModel):
    data: list[DepartmentStats]


class UserStats(SQLModel):
    user: AssigneeBrief
    department: DepartmentBrief | None
    kr_count: int
    avg_progress: int
    krs: list[KeyResultPublic]


class UserStatsList(SQLModel):
    data: list[UserStats]

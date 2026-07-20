"""
OKR Module — KeyResult Router

KR 管理（超管）+ 我的任务（成员）：/krs/my 筛选、/krs/{id}/progress 进度更新。
"""

from __future__ import annotations

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models_core import Message, User
from app.modules.okr import crud
from app.modules.okr.schemas import (
    KeyResultCreate,
    KeyResultProgressUpdate,
    KeyResultPublic,
    KeyResultsPublic,
    KeyResultUpdate,
)

router = APIRouter()

KrFilter = Literal["all", "active", "done", "due_soon", "overdue"]


# =============================================================================
# KeyResult — 超管管理
# =============================================================================

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

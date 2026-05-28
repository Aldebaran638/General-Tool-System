"""
Exam Management Module — API Router  (/api/v1/exams/*)

Endpoints:
  CRUD:
    GET    /exams                 — list exams (paginated, filterable)
    POST   /exams                 — create exam
    GET    /exams/{id}            — get exam detail
    PUT    /exams/{id}            — update exam
    DELETE /exams/{id}            — delete exam

  Lifecycle:
    POST   /exams/{id}/publish    — publish exam (with validation)
    POST   /exams/{id}/archive    — archive exam

  Paper:
    GET    /exams/{id}/paper      — get paper (questions + options)
    PUT    /exams/{id}/paper      — save paper (replace all)

  Participants:
    GET    /exams/{id}/participants                — list participants
    POST   /exams/{id}/participants/by-centers     — add by center IDs
    POST   /exams/{id}/participants/by-departments — add by department IDs
    POST   /exams/{id}/participants/by-users       — add by userids
    DELETE /exams/{id}/participants/{userid}       — remove participant

All endpoints require exam admin or superuser.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import SessionDep
from app.modules.wecom_gateway.deps import RequireExamAdmin
from app.modules.exam_management.models import Exam
from app.modules.exam_management.schemas import (
    AddByCentersRequest,
    AddByDepartmentsRequest,
    AddByUsersRequest,
    ExamCreate,
    ExamPublic,
    ExamUpdate,
    ExamsPublic,
    PaperPublic,
    PaperSaveRequest,
    ParticipantPublic,
    ParticipantsPublic,
    PublishValidation,
)
from app.modules.exam_management.service import (
    add_participants_by_centers,
    add_participants_by_departments,
    add_participants_by_users,
    archive_exam,
    create_exam,
    delete_exam,
    get_exam,
    get_paper,
    list_exams,
    list_participants,
    publish_exam,
    remove_participant,
    save_paper,
    update_exam,
    validate_publish,
)

router = APIRouter(prefix="/exams", tags=["exams"])


# ─── helpers ─────────────────────────────────────────────────────────────────

def _to_public(exam: Exam) -> ExamPublic:
    return ExamPublic(
        id=exam.id,
        name=exam.name,
        description=exam.description,
        status=exam.status,
        start_at=exam.start_at,
        end_at=exam.end_at,
        duration_minutes=exam.duration_minutes,
        attempt_limit_type=exam.attempt_limit_type,
        attempt_limit_count=exam.attempt_limit_count,
        pass_score=exam.pass_score,
        submit_rule=exam.submit_rule,
        show_answer=exam.show_answer,
        random_question_order=exam.random_question_order,
        random_option_order=exam.random_option_order,
        created_by=exam.created_by,
        published_at=exam.published_at,
        created_at=exam.created_at,
        updated_at=exam.updated_at,
    )


def _get_exam_or_404(session: SessionDep, exam_id: uuid.UUID) -> Exam:
    exam = get_exam(session, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    return exam


# ─── Exam CRUD ───────────────────────────────────────────────────────────────

@router.get("", response_model=ExamsPublic, summary="考试列表")
def list_exams_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, description="按考试名称搜索"),
) -> ExamsPublic:
    exams, count = list_exams(session, page=page, limit=limit, status=status_filter, q=q)
    return ExamsPublic(data=[_to_public(e) for e in exams], count=count)


@router.post("", response_model=ExamPublic, status_code=201, summary="创建考试")
def create_exam_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    body: ExamCreate,
) -> ExamPublic:
    exam = create_exam(session, body, created_by=current_user.id)
    return _to_public(exam)


@router.get("/{exam_id}", response_model=ExamPublic, summary="考试详情")
def get_exam_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
) -> ExamPublic:
    exam = _get_exam_or_404(session, exam_id)
    return _to_public(exam)


@router.put("/{exam_id}", response_model=ExamPublic, summary="编辑考试")
def update_exam_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
    body: ExamUpdate,
) -> ExamPublic:
    exam = _get_exam_or_404(session, exam_id)
    try:
        updated = update_exam(session, exam, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_public(updated)


@router.delete("/{exam_id}", status_code=204, summary="删除考试")
def delete_exam_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
):
    exam = _get_exam_or_404(session, exam_id)
    try:
        delete_exam(session, exam)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Lifecycle ───────────────────────────────────────────────────────────────

@router.post("/{exam_id}/publish", response_model=ExamPublic, summary="发布考试")
def publish_exam_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
) -> ExamPublic:
    exam = _get_exam_or_404(session, exam_id)
    try:
        published = publish_exam(session, exam)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_public(published)


@router.post(
    "/{exam_id}/validate",
    response_model=PublishValidation,
    summary="校验考试是否可以发布",
)
def validate_exam_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
) -> PublishValidation:
    exam = _get_exam_or_404(session, exam_id)
    return validate_publish(session, exam)


@router.post("/{exam_id}/archive", response_model=ExamPublic, summary="归档考试")
def archive_exam_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
) -> ExamPublic:
    exam = _get_exam_or_404(session, exam_id)
    try:
        archived = archive_exam(session, exam)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_public(archived)


# ─── Paper ───────────────────────────────────────────────────────────────────

@router.get("/{exam_id}/paper", response_model=PaperPublic, summary="获取试卷")
def get_paper_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
) -> PaperPublic:
    _get_exam_or_404(session, exam_id)
    paper = get_paper(session, exam_id)
    return PaperPublic(**paper)


@router.put("/{exam_id}/paper", status_code=204, summary="保存试卷")
def save_paper_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
    body: PaperSaveRequest,
):
    exam = _get_exam_or_404(session, exam_id)
    try:
        save_paper(session, exam, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Participants ────────────────────────────────────────────────────────────

@router.get(
    "/{exam_id}/participants",
    response_model=ParticipantsPublic,
    summary="考试人员列表",
)
def list_participants_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, description="按姓名或 userid 搜索"),
) -> ParticipantsPublic:
    _get_exam_or_404(session, exam_id)
    participants, count = list_participants(
        session, exam_id, page=page, limit=limit, q=q
    )
    return ParticipantsPublic(
        data=[
            ParticipantPublic(
                id=p.id,
                exam_id=p.exam_id,
                userid=p.userid,
                name_snapshot=p.name_snapshot,
                center_snapshot=p.center_snapshot,
                department_snapshot=p.department_snapshot,
                position_snapshot=p.position_snapshot,
                wecom_status_snapshot=p.wecom_status_snapshot,
                created_at=p.created_at,
            )
            for p in participants
        ],
        count=count,
    )


@router.post(
    "/{exam_id}/participants/by-centers",
    summary="按中心添加学员",
)
def add_by_centers_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
    body: AddByCentersRequest,
) -> dict:
    _get_exam_or_404(session, exam_id)
    added = add_participants_by_centers(session, exam_id, body.center_ids)
    return {"added": added}


@router.post(
    "/{exam_id}/participants/by-departments",
    summary="按部门添加学员",
)
def add_by_departments_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
    body: AddByDepartmentsRequest,
) -> dict:
    _get_exam_or_404(session, exam_id)
    added = add_participants_by_departments(session, exam_id, body.department_ids)
    return {"added": added}


@router.post(
    "/{exam_id}/participants/by-users",
    summary="按人员添加学员",
)
def add_by_users_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
    body: AddByUsersRequest,
) -> dict:
    _get_exam_or_404(session, exam_id)
    added = add_participants_by_users(session, exam_id, body.userids)
    return {"added": added}


@router.delete(
    "/{exam_id}/participants/{userid}",
    status_code=204,
    summary="移除学员",
)
def remove_participant_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
    userid: str,
):
    _get_exam_or_404(session, exam_id)
    removed = remove_participant(session, exam_id, userid)
    if not removed:
        raise HTTPException(status_code=404, detail="学员不存在")

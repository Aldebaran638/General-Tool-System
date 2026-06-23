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
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.modules.wecom_gateway.deps import RequireExamAdmin
from app.modules.exam_management.models import Exam, ExamCategory, ExamPaper, ExamParticipant
from app.modules.exam_management.schemas import (
    AddByCentersRequest,
    AddByDepartmentsRequest,
    AddByUsersRequest,
    ExamCategoriesPublic,
    ExamCategoryCreate,
    ExamCategoryPublic,
    ExamCategoryUpdate,
    ExamCreate,
    ExamPublic,
    ExamStatistics,
    ExamUpdate,
    ExamsPublic,
    PaperPublic,
    PaperSaveRequest,
    ParticipantDetail,
    ParticipantListResponse,
    ParticipantPublic,
    ParticipantsPublic,
    PublishValidation,
    QuestionBankDetail,
    QuestionBankPublic,
    SystemDashboardStats,
    TrainerInfo,
    TrainerSummaryResponse,
)
from app.modules.exam_management.service import (
    add_participants_by_centers,
    add_participants_by_departments,
    add_participants_by_users,
    archive_exam,
    create_category,
    create_exam,
    delete_category,
    delete_exam,
    generate_paper_for_exam,
    get_category,
    get_exam,
    get_exam_statistics,
    get_paper,
    get_question_bank_detail,
    get_system_stats,
    get_trainer_summary,
    list_categories,
    list_exams,
    list_participants,
    list_question_bank,
    publish_exam,
    remove_participant,
    save_paper,
    update_category,
    update_exam,
    validate_publish,
)

router = APIRouter(prefix="/exams", tags=["exams"])


# ─── helpers ─────────────────────────────────────────────────────────────────

def _to_public(
    exam: Exam,
    category_name: str | None = None,
    session: SessionDep | None = None,
) -> ExamPublic:
    trainers: list[TrainerInfo] = []
    if exam.trainer_ids and session:
        from app.models import User
        for uid in exam.trainer_ids:
            try:
                user = session.get(User, uuid.UUID(uid))
                if user:
                    trainers.append(TrainerInfo(id=uid, name=user.full_name or user.wecom_userid))
            except (ValueError, AttributeError):
                pass
    return ExamPublic(
        id=exam.id,
        name=exam.name,
        trainer_ids=exam.trainer_ids,
        trainers=trainers,
        status=exam.status,
        category_id=exam.category_id,
        category_name=category_name,
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


# ─── Exam Category ───────────────────────────────────────────────────────────
# NOTE: Category routes MUST be defined before /{exam_id} to avoid route conflicts.

@router.get("/categories", response_model=ExamCategoriesPublic, summary="分类列表")
def list_categories_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
) -> ExamCategoriesPublic:
    categories, count = list_categories(session)
    return ExamCategoriesPublic(
        data=[
            ExamCategoryPublic(
                id=c.id,
                name=c.name,
                sort_order=c.sort_order,
                created_at=c.created_at,
            )
            for c in categories
        ],
        count=count,
    )


@router.post(
    "/categories",
    response_model=ExamCategoryPublic,
    status_code=201,
    summary="创建分类",
)
def create_category_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    body: ExamCategoryCreate,
) -> ExamCategoryPublic:
    try:
        category = create_category(session, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ExamCategoryPublic(
        id=category.id,
        name=category.name,
        sort_order=category.sort_order,
        created_at=category.created_at,
    )


@router.put(
    "/categories/{category_id}",
    response_model=ExamCategoryPublic,
    summary="更新分类",
)
def update_category_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    category_id: int,
    body: ExamCategoryUpdate,
) -> ExamCategoryPublic:
    category = get_category(session, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    try:
        updated = update_category(session, category, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ExamCategoryPublic(
        id=updated.id,
        name=updated.name,
        sort_order=updated.sort_order,
        created_at=updated.created_at,
    )


@router.delete("/categories/{category_id}", status_code=204, summary="删除分类")
def delete_category_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    category_id: int,
):
    category = get_category(session, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    try:
        delete_category(session, category)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── System Dashboard ───────────────────────────────────────────────────────
# NOTE: This route MUST be defined before /{exam_id} to avoid route conflicts.

@router.get(
    "/admin/dashboard/stats",
    response_model=SystemDashboardStats,
    summary="系统总览看板数据",
)
def get_system_dashboard_stats(
    session: SessionDep,
    current_user: RequireExamAdmin,
    start_date: datetime | None = Query(default=None, description="筛选开始日期 (YYYY-MM-DD)"),
    end_date: datetime | None = Query(default=None, description="筛选结束日期 (YYYY-MM-DD)"),
) -> SystemDashboardStats:
    return get_system_stats(session, start_date=start_date, end_date=end_date)


@router.get(
    "/admin/trainers/summary",
    response_model=TrainerSummaryResponse,
    summary="培训讲师汇总",
)
def get_trainer_summary_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    q: str | None = Query(default=None, description="搜索讲师姓名或课程名称"),
    start_date: datetime | None = Query(default=None, description="考试开始时间下限"),
    end_date: datetime | None = Query(default=None, description="考试开始时间上限"),
) -> TrainerSummaryResponse:
    return get_trainer_summary(session, q=q, start_date=start_date, end_date=end_date)


# ─── Question Bank ───────────────────────────────────────────────────────────
# NOTE: Question bank routes MUST be defined before /{exam_id} to avoid route conflicts.

def _parse_category_ids(value: str | None) -> list[int] | None:
    """Parse category_ids from query string.

    Supports both comma-separated (?category_ids=1,2,3) and repeated
    (?category_ids=1&category_ids=2) styles.
    """
    if not value:
        return None
    try:
        return [int(v.strip()) for v in value.split(",") if v.strip()]
    except ValueError:
        return None


@router.get(
    "/question-bank",
    response_model=QuestionBankPublic,
    summary="试题库列表",
)
def list_question_bank_endpoint(
    session: SessionDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    category_ids: str | None = Query(default=None),
) -> QuestionBankPublic:
    parsed_category_ids = _parse_category_ids(category_ids)
    data, count = list_question_bank(
        session,
        page=page,
        limit=limit,
        category_ids=parsed_category_ids,
    )
    return QuestionBankPublic(data=data, count=count)


@router.get(
    "/question-bank/{exam_id}",
    response_model=QuestionBankDetail,
    summary="试卷详情（在线预览）",
)
def get_question_bank_detail_endpoint(
    session: SessionDep,
    current_user: CurrentUser,
    exam_id: uuid.UUID,
) -> QuestionBankDetail:
    detail = get_question_bank_detail(session, exam_id)
    if not detail:
        raise HTTPException(status_code=404, detail="试卷不存在或未生成")
    return QuestionBankDetail(**detail)


@router.get(
    "/question-bank/{exam_id}/download",
    summary="下载试卷docx",
)
def download_question_bank_endpoint(
    session: SessionDep,
    current_user: CurrentUser,
    exam_id: uuid.UUID,
):
    from fastapi.responses import FileResponse
    from app.core.storage import resolve_upload_dir

    paper = session.exec(
        select(ExamPaper).where(ExamPaper.exam_id == exam_id)
    ).first()
    if not paper or paper.status != "GENERATED" or not paper.docx_path:
        raise HTTPException(status_code=404, detail="试卷文件未生成")

    file_path = resolve_upload_dir() / paper.docx_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="试卷文件不存在")

    exam = session.get(Exam, exam_id)
    filename = f"{exam.name}.docx" if exam else "exam_paper.docx"
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


# ─── Exam CRUD ───────────────────────────────────────────────────────────────

def _resolve_category_name(session: SessionDep, category_id: int | None) -> str | None:
    """Look up category name by id; returns None if not set or not found."""
    if category_id is None:
        return None
    cat = get_category(session, category_id)
    return cat.name if cat else None


@router.get("", response_model=ExamsPublic, summary="考试列表")
def list_exams_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    category_id: int | None = Query(default=None, description="按分类筛选"),
    q: str | None = Query(default=None, description="按考试名称搜索"),
) -> ExamsPublic:
    exams, count = list_exams(
        session, page=page, limit=limit, status=status_filter,
        category_id=category_id, q=q,
    )
    # Batch-load category names to avoid N+1
    cat_ids = {e.category_id for e in exams if e.category_id is not None}
    cat_map: dict[int, str] = {}
    if cat_ids:
        categories = session.exec(
            select(ExamCategory).where(ExamCategory.id.in_(cat_ids))
        ).all()
        cat_map = {c.id: c.name for c in categories}

    return ExamsPublic(
        data=[
            _to_public(e, category_name=cat_map.get(e.category_id), session=session)
            for e in exams
        ],
        count=count,
    )


@router.post("", response_model=ExamPublic, status_code=201, summary="创建考试")
def create_exam_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    body: ExamCreate,
) -> ExamPublic:
    exam = create_exam(session, body, created_by=current_user.id)
    cat_name = _resolve_category_name(session, exam.category_id)
    return _to_public(exam, category_name=cat_name, session=session)


@router.get("/{exam_id}", response_model=ExamPublic, summary="考试详情")
def get_exam_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
) -> ExamPublic:
    exam = _get_exam_or_404(session, exam_id)
    cat_name = _resolve_category_name(session, exam.category_id)
    return _to_public(exam, category_name=cat_name, session=session)


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
    cat_name = _resolve_category_name(session, updated.category_id)
    return _to_public(updated, category_name=cat_name, session=session)


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

@router.get(
    "/{exam_id}/statistics",
    response_model=ExamStatistics,
    summary="考试统计",
)
def get_exam_statistics_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
) -> ExamStatistics:
    exam = _get_exam_or_404(session, exam_id)
    return get_exam_statistics(session, exam.id)


@router.get(
    "/{exam_id}/participants/by-status",
    response_model=ParticipantListResponse,
    summary="按状态查询参与人员详情",
)
def get_participants_by_status_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
    status: str = Query(..., description="状态: ALL / NOT_STARTED / IN_PROGRESS / COMPLETED / NOT_COMPLETED"),
) -> ParticipantListResponse:
    exam = _get_exam_or_404(session, exam_id)
    query = (
        select(ExamParticipant)
        .where(ExamParticipant.exam_id == exam.id)
        .order_by(ExamParticipant.name_snapshot)
    )
    if status != "ALL":
        query = query.where(ExamParticipant.completion_status == status)

    participants = session.exec(query).all()

    data = [
        ParticipantDetail(
            id=p.id,
            userid=p.userid,
            name_snapshot=p.name_snapshot,
            center_snapshot=p.center_snapshot,
            department_snapshot=p.department_snapshot,
            position_snapshot=p.position_snapshot,
            completion_status=p.completion_status,
            final_score=p.final_score,
            final_passed=p.final_passed,
            completed_at=p.completed_at,
        )
        for p in participants
    ]
    return ParticipantListResponse(data=data, count=len(data))


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
    cat_name = _resolve_category_name(session, published.category_id)
    return _to_public(published, category_name=cat_name, session=session)


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
    cat_name = _resolve_category_name(session, archived.category_id)
    return _to_public(archived, category_name=cat_name, session=session)


@router.post("/{exam_id}/generate-paper", summary="手动触发试题库生成")
def generate_paper_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    exam_id: uuid.UUID,
) -> dict:
    """Manually trigger docx generation for a published or archived exam.
    Idempotent — safe to call multiple times; re-generates only if previous attempt failed.
    """
    _get_exam_or_404(session, exam_id)
    try:
        paper = generate_paper_for_exam(session, exam_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": paper.status, "docx_path": paper.docx_path, "generated_at": paper.generated_at}


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

"""
Exam Management Module — Service layer
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete as sql_delete, func
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from app.models import User
from app.modules.data_sync.models import WecomDepartment
from app.modules.exam_management.models import (
    Exam,
    ExamAnswer,
    ExamAttempt,
    ExamCategory,
    ExamPaper,
    ExamPaperSnapshot,
    ExamParticipant,
    Question,
    QuestionOption,
)
from app.modules.exam_management.schemas import (
    DeviceTypeCount,
    DifficultyCount,
    ExamCategoryCreate,
    ExamCategoryUpdate,
    ExamCreate,
    ExamStatistics,
    ExamUpdate,
    PaperSaveRequest,
    PublishValidation,
    QuestionTypeCount,
    ScoreDistribution,
    SystemDashboardStats,
)


EXAM_TOTAL_SCORE = 100.0
SCORE_TOLERANCE = 0.001


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ─── Exam Category CRUD ─────────────────────────────────────────────────────

def list_categories(session: Session) -> tuple[list[ExamCategory], int]:
    """Return all categories ordered by sort_order."""
    rows = session.exec(
        select(ExamCategory).order_by(ExamCategory.sort_order, ExamCategory.id)
    ).all()
    return list(rows), len(rows)


def create_category(session: Session, data: ExamCategoryCreate) -> ExamCategory:
    """Create a new category; raises ValueError if name already exists."""
    existing = session.exec(
        select(ExamCategory).where(ExamCategory.name == data.name)
    ).first()
    if existing:
        raise ValueError("分类名称已存在")
    category = ExamCategory(**data.model_dump())
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def get_category(session: Session, category_id: int) -> ExamCategory | None:
    return session.get(ExamCategory, category_id)


def update_category(
    session: Session,
    category: ExamCategory,
    data: ExamCategoryUpdate,
) -> ExamCategory:
    """Update category fields; raises ValueError if new name conflicts."""
    update_data = data.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] is not None:
        dup = session.exec(
            select(ExamCategory).where(
                ExamCategory.name == update_data["name"],
                ExamCategory.id != category.id,
            )
        ).first()
        if dup:
            raise ValueError("分类名称已存在")
    for field, value in update_data.items():
        setattr(category, field, value)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def delete_category(session: Session, category: ExamCategory) -> None:
    """Delete a category; raises ValueError if exams reference it."""
    exam_count = session.exec(
        select(func.count()).select_from(Exam).where(Exam.category_id == category.id)
    ).one()
    if exam_count > 0:
        raise ValueError(f"该分类下有 {exam_count} 个考试，无法删除")
    session.delete(category)
    session.commit()


# ─── Exam CRUD ───────────────────────────────────────────────────────────────

def create_exam(
    session: Session,
    data: ExamCreate,
    created_by: uuid.UUID,
) -> Exam:
    exam = Exam(**data.model_dump(), created_by=created_by)
    session.add(exam)
    session.commit()
    session.refresh(exam)
    return exam


def get_exam(session: Session, exam_id: uuid.UUID) -> Exam | None:
    return session.get(Exam, exam_id)


def list_exams(
    session: Session,
    *,
    page: int = 1,
    limit: int = 20,
    status: str | None = None,
    category_id: int | None = None,
    q: str | None = None,
) -> tuple[list[Exam], int]:
    base = select(Exam)
    count_base = select(func.count()).select_from(Exam)

    if status:
        base = base.where(Exam.status == status)
        count_base = count_base.where(Exam.status == status)
    if category_id is not None:
        base = base.where(Exam.category_id == category_id)
        count_base = count_base.where(Exam.category_id == category_id)
    if q:
        like = f"%{q}%"
        base = base.where(Exam.name.ilike(like))
        count_base = count_base.where(Exam.name.ilike(like))

    count = session.exec(count_base).one()
    offset = (page - 1) * limit
    rows = session.exec(
        base.order_by(Exam.created_at.desc()).offset(offset).limit(limit)
    ).all()
    return list(rows), count


def update_exam(
    session: Session,
    exam: Exam,
    data: ExamUpdate,
) -> Exam:
    if exam.status != "DRAFT":
        raise ValueError("只能编辑未发布的考试")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(exam, field, value)
    exam.updated_at = _now()
    session.add(exam)
    session.commit()
    session.refresh(exam)
    return exam


def delete_exam(session: Session, exam: Exam) -> None:
    if exam.status == "PUBLISHED":
        raise ValueError("已发布的考试不能删除，请先归档")

    # All deletes in a single transaction — commit at the end, rollback on any failure
    try:
        # Batch delete exam answers (via subquery on attempt_ids)
        attempt_ids = session.exec(
            select(ExamAttempt.id).where(ExamAttempt.exam_id == exam.id)
        ).all()
        if attempt_ids:
            session.exec(
                sql_delete(ExamAnswer).where(ExamAnswer.attempt_id.in_(attempt_ids))
            )

        # Batch delete attempts
        session.exec(
            sql_delete(ExamAttempt).where(ExamAttempt.exam_id == exam.id)
        )

        # Batch delete options (via subquery on question_ids)
        question_ids = session.exec(
            select(Question.id).where(Question.exam_id == exam.id)
        ).all()
        if question_ids:
            session.exec(
                sql_delete(QuestionOption).where(QuestionOption.question_id.in_(question_ids))
            )

        # Batch delete questions
        session.exec(
            sql_delete(Question).where(Question.exam_id == exam.id)
        )

        # Batch delete participants
        session.exec(
            sql_delete(ExamParticipant).where(ExamParticipant.exam_id == exam.id)
        )

        # Batch delete paper snapshots
        session.exec(
            sql_delete(ExamPaperSnapshot).where(ExamPaperSnapshot.exam_id == exam.id)
        )

        # Batch delete exam papers (docx tracking)
        session.exec(
            sql_delete(ExamPaper).where(ExamPaper.exam_id == exam.id)
        )

        session.delete(exam)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise


# ─── Paper (Questions + Options) ─────────────────────────────────────────────

def save_paper(
    session: Session,
    exam: Exam,
    data: PaperSaveRequest,
) -> None:
    """Replace all questions/options for an exam."""
    if exam.status != "DRAFT":
        raise ValueError("只能编辑未发布考试的试卷")

    # Batch delete existing options and questions
    old_question_ids = session.exec(
        select(Question.id).where(Question.exam_id == exam.id)
    ).all()
    if old_question_ids:
        session.exec(
            sql_delete(QuestionOption).where(QuestionOption.question_id.in_(old_question_ids))
        )
    session.exec(
        sql_delete(Question).where(Question.exam_id == exam.id)
    )

    # Insert new
    for qdata in data.questions:
        question = Question(
            exam_id=exam.id,
            question_type=qdata.question_type,
            stem=qdata.stem,
            score=qdata.score,
            sort_no=qdata.sort_no,
            analysis=qdata.analysis,
        )
        session.add(question)
        session.flush()  # get question.id

        for odata in qdata.options:
            option = QuestionOption(
                question_id=question.id,
                option_key=odata.option_key,
                option_text=odata.option_text,
                is_correct=odata.is_correct,
                sort_no=odata.sort_no,
            )
            session.add(option)

    exam.updated_at = _now()
    session.add(exam)
    session.commit()


def get_paper(session: Session, exam_id: uuid.UUID) -> dict:
    """Return questions + options for an exam."""
    questions = session.exec(
        select(Question)
        .where(Question.exam_id == exam_id)
        .order_by(Question.sort_no)
    ).all()

    if not questions:
        return {"questions": [], "total_score": 0.0, "question_count": 0}

    # Batch load all options to avoid N+1 query
    question_ids = [q.id for q in questions]
    all_options = session.exec(
        select(QuestionOption)
        .where(QuestionOption.question_id.in_(question_ids))
        .order_by(QuestionOption.sort_no)
    ).all()
    options_by_question: dict[uuid.UUID, list[QuestionOption]] = {}
    for opt in all_options:
        options_by_question.setdefault(opt.question_id, []).append(opt)

    result = []
    total_score = 0.0
    for q in questions:
        total_score += q.score
        options = options_by_question.get(q.id, [])
        result.append({
            "id": q.id,
            "exam_id": q.exam_id,
            "question_type": q.question_type,
            "stem": q.stem,
            "score": q.score,
            "sort_no": q.sort_no,
            "analysis": q.analysis,
            "options": [
                {
                    "id": o.id,
                    "question_id": o.question_id,
                    "option_key": o.option_key,
                    "option_text": o.option_text,
                    "is_correct": o.is_correct,
                    "sort_no": o.sort_no,
                }
                for o in options
            ],
        })

    return {
        "questions": result,
        "total_score": total_score,
        "question_count": len(result),
    }


# ─── Publish / Archive ──────────────────────────────────────────────────────

def validate_publish(session: Session, exam: Exam) -> PublishValidation:
    errors: list[str] = []

    if not exam.name or not exam.name.strip():
        errors.append("考试名称不能为空")
    if exam.start_at >= exam.end_at:
        errors.append("结束时间必须晚于开始时间")
    if exam.duration_minutes <= 0:
        errors.append("考试时长必须大于 0")
    if exam.pass_score <= 0:
        errors.append("及格线必须大于 0")
    if exam.pass_score > EXAM_TOTAL_SCORE:
        errors.append(f"及格线不能超过 {EXAM_TOTAL_SCORE:g} 分")
    if exam.attempt_limit_type == "LIMITED" and (
        exam.attempt_limit_count is None or exam.attempt_limit_count <= 0
    ):
        errors.append("限制考试次数时，次数必须大于 0")

    # Check questions
    questions = session.exec(
        select(Question).where(Question.exam_id == exam.id)
    ).all()
    if not questions:
        errors.append("试卷至少需要 1 道题")
    else:
        # Batch load all options to avoid N+1 query
        question_ids = [q.id for q in questions]
        all_options = session.exec(
            select(QuestionOption).where(QuestionOption.question_id.in_(question_ids))
        ).all()
        options_by_question: dict[uuid.UUID, list[QuestionOption]] = {}
        for opt in all_options:
            options_by_question.setdefault(opt.question_id, []).append(opt)

        for q in questions:
            if not q.stem or not q.stem.strip():
                errors.append(f"题号 {q.sort_no} 缺少题干")
            if q.score <= 0:
                errors.append(f"题号 {q.sort_no} 分数必须大于 0")

            options = options_by_question.get(q.id, [])
            correct_count = sum(1 for o in options if o.is_correct)

            if q.question_type == "SINGLE_CHOICE":
                if correct_count != 1:
                    errors.append(f"题号 {q.sort_no}（单选题）必须有且仅有 1 个正确答案")
            elif q.question_type == "MULTIPLE_CHOICE":
                if correct_count < 2:
                    errors.append(f"题号 {q.sort_no}（多选题）至少需要 2 个正确答案")
            elif q.question_type == "TRUE_FALSE":
                if correct_count != 1:
                    errors.append(f"题号 {q.sort_no}（判断题）必须有且仅有 1 个正确答案")

    # Check participants
    participant_count = session.exec(
        select(func.count()).select_from(ExamParticipant)
        .where(ExamParticipant.exam_id == exam.id)
    ).one()
    if participant_count == 0:
        errors.append("至少需要 1 名学员")

    total_score = sum(q.score for q in questions)
    if total_score <= 0:
        errors.append("试卷总分必须大于 0")
    total_score_matches_policy = abs(total_score - EXAM_TOTAL_SCORE) <= SCORE_TOLERANCE
    if not total_score_matches_policy:
        errors.append(f"试卷总分必须等于 {EXAM_TOTAL_SCORE:g} 分，当前为 {total_score:g} 分")
    if total_score_matches_policy and exam.pass_score > total_score:
        errors.append(f"及格线 ({exam.pass_score}) 不能超过试卷总分 ({total_score})")

    return PublishValidation(valid=len(errors) == 0, errors=errors)


def publish_exam(session: Session, exam: Exam) -> Exam:
    validation = validate_publish(session, exam)
    if not validation.valid:
        raise ValueError("发布校验失败: " + "; ".join(validation.errors))

    # Create paper snapshot
    from app.modules.exam_management.models import ExamPaperSnapshot, Question, QuestionOption

    questions = session.exec(
        select(Question).where(Question.exam_id == exam.id).order_by(Question.sort_no)
    ).all()

    # Batch load all options to avoid N+1 query
    question_ids = [q.id for q in questions]
    all_options = session.exec(
        select(QuestionOption)
        .where(QuestionOption.question_id.in_(question_ids))
        .order_by(QuestionOption.sort_no)
    ).all()
    options_by_question: dict[uuid.UUID, list[QuestionOption]] = {}
    for opt in all_options:
        options_by_question.setdefault(opt.question_id, []).append(opt)

    snapshot_questions = []
    total_score = 0
    for q in questions:
        total_score += q.score
        options = options_by_question.get(q.id, [])

        snapshot_questions.append({
            "id": str(q.id),
            "question_type": q.question_type,
            "stem": q.stem,
            "score": q.score,
            "sort_no": q.sort_no,
            "analysis": q.analysis,
            "options": [
                {
                    "id": str(o.id),
                    "option_key": o.option_key,
                    "option_text": o.option_text,
                    "is_correct": o.is_correct,
                    "sort_no": o.sort_no,
                }
                for o in options
            ],
        })

    snapshot = ExamPaperSnapshot(
        exam_id=exam.id,
        snapshot_json={"questions": snapshot_questions},
        total_score=total_score,
        question_count=len(questions),
    )
    session.add(snapshot)
    session.flush()  # Get snapshot.id

    # Update exam with snapshot reference
    exam.status = "PUBLISHED"
    exam.published_at = _now()
    exam.updated_at = _now()
    session.add(exam)
    session.commit()
    session.refresh(exam)
    return exam


def _generate_paper_if_needed(session: Session, exam: Exam) -> None:
    """Generate docx paper for an exam if one doesn't already exist."""
    existing = session.exec(
        select(ExamPaper).where(ExamPaper.exam_id == exam.id)
    ).first()
    if existing:
        return

    now = _now()
    try:
        from app.modules.exam_management.docx_generator import generate_exam_paper_docx
        docx_path = generate_exam_paper_docx(exam.id, session)
        paper = ExamPaper(
            exam_id=exam.id,
            docx_path=docx_path,
            status="GENERATED",
            generated_at=now,
        )
    except Exception:
        paper = ExamPaper(exam_id=exam.id, status="FAILED")
    session.add(paper)
    session.commit()


def archive_exam(session: Session, exam: Exam) -> Exam:
    if exam.status == "DRAFT":
        raise ValueError("未发布的考试不能归档")
    exam.status = "ARCHIVED"
    exam.updated_at = _now()
    session.add(exam)
    session.commit()
    session.refresh(exam)
    # Trigger docx generation synchronously on archive
    _generate_paper_if_needed(session, exam)
    return exam


def generate_paper_for_exam(session: Session, exam_id: uuid.UUID) -> ExamPaper:
    """Manually trigger docx generation for an exam (admin use).

    Idempotent: if a GENERATED paper already exists, returns it unchanged.
    If a FAILED paper exists, retries generation.
    """
    exam = session.get(Exam, exam_id)
    if not exam:
        raise ValueError("考试不存在")
    if exam.status not in ("PUBLISHED", "ARCHIVED"):
        raise ValueError("只能为已发布或已归档的考试生成试题库")

    now = _now()
    existing = session.exec(
        select(ExamPaper).where(ExamPaper.exam_id == exam_id)
    ).first()

    if existing and existing.status == "GENERATED":
        return existing

    try:
        from app.modules.exam_management.docx_generator import generate_exam_paper_docx
        docx_path = generate_exam_paper_docx(exam_id, session)
        if existing:
            existing.docx_path = docx_path
            existing.status = "GENERATED"
            existing.generated_at = now
            session.add(existing)
        else:
            existing = ExamPaper(
                exam_id=exam_id,
                docx_path=docx_path,
                status="GENERATED",
                generated_at=now,
            )
            session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    except Exception as exc:
        if not existing:
            existing = ExamPaper(exam_id=exam_id, status="FAILED")
            session.add(existing)
        else:
            existing.status = "FAILED"
            session.add(existing)
        session.commit()
        raise ValueError(f"试题库生成失败: {exc}") from exc


# ─── Participants ────────────────────────────────────────────────────────────

def _add_participants(
    session: Session,
    exam_id: uuid.UUID,
    users: list[User],
) -> int:
    """Add users as participants, skip duplicates. Returns count added."""
    # Pre-check pattern: load existing userids first, skip in Python.
    # Using IntegrityError + session.rollback() is unsafe here because
    # rollback() would discard all previously-flushed inserts in the batch.
    existing = session.exec(
        select(ExamParticipant.userid).where(ExamParticipant.exam_id == exam_id)
    ).all()
    existing_set = set(existing)

    added = 0
    for user in users:
        # Use wecom_userid if available, otherwise use user UUID as identifier
        userid = user.wecom_userid or str(user.id)
        if userid in existing_set:
            continue

        # Create snapshot with available user info
        participant = ExamParticipant(
            exam_id=exam_id,
            userid=userid,
            name_snapshot=user.full_name,
        )
        session.add(participant)
        existing_set.add(userid)  # prevent duplicate adds within same batch
        added += 1

    session.commit()
    return added


def add_participants_by_centers(
    session: Session,
    exam_id: uuid.UUID,
    center_ids: list[int],
) -> int:
    """Add all users belonging to the given center departments."""
    # Find all department IDs under these centers (including the center itself)
    all_dept_ids: set[int] = set()
    for cid in center_ids:
        all_dept_ids.add(cid)
        _collect_child_departments(session, cid, all_dept_ids)

    # Find users whose wecom department list overlaps
    users = session.exec(
        select(User).where(User.wecom_userid.is_not(None), User.is_active == True)  # type: ignore[union-attr]  # noqa: E712
    ).all()

    # Filter users by department membership
    # We need to check the wecom_member table for department associations
    from app.modules.data_sync.models import WecomMember

    matching_userids: set[str] = set()
    members = session.exec(
        select(WecomMember).where(WecomMember.removed_at.is_(None))  # type: ignore[union-attr]
    ).all()
    for m in members:
        if any(dept_id in all_dept_ids for dept_id in (m.department or [])):
            matching_userids.add(m.userid)

    matching_users = [u for u in users if u.wecom_userid in matching_userids]
    return _add_participants(session, exam_id, matching_users)


def add_participants_by_departments(
    session: Session,
    exam_id: uuid.UUID,
    department_ids: list[int],
) -> int:
    """Add all users belonging to the given departments (including sub-departments)."""
    all_dept_ids: set[int] = set()
    for did in department_ids:
        all_dept_ids.add(did)
        _collect_child_departments(session, did, all_dept_ids)

    from app.modules.data_sync.models import WecomMember

    users = session.exec(
        select(User).where(User.wecom_userid.is_not(None), User.is_active == True)  # type: ignore[union-attr]  # noqa: E712
    ).all()

    matching_userids: set[str] = set()
    members = session.exec(
        select(WecomMember).where(WecomMember.removed_at.is_(None))  # type: ignore[union-attr]
    ).all()
    for m in members:
        if any(dept_id in all_dept_ids for dept_id in (m.department or [])):
            matching_userids.add(m.userid)

    matching_users = [u for u in users if u.wecom_userid in matching_userids]
    return _add_participants(session, exam_id, matching_users)


def add_participants_by_users(
    session: Session,
    exam_id: uuid.UUID,
    userids: list[str],
) -> int:
    """Add specific users by userid (supports both wecom_userid and user UUID)."""
    from sqlalchemy import or_

    # Try to parse as UUIDs
    uuid_list = []
    str_list = []
    for uid in userids:
        try:
            uuid_list.append(uuid.UUID(uid))
        except ValueError:
            str_list.append(uid)

    # Query by wecom_userid OR user id (UUID)
    conditions = []
    if str_list:
        conditions.append(User.wecom_userid.in_(str_list))  # type: ignore[union-attr]
    if uuid_list:
        conditions.append(User.id.in_(uuid_list))  # type: ignore[union-attr]

    if not conditions:
        return 0

    users = session.exec(
        select(User).where(
            or_(*conditions),
            User.is_active == True,  # noqa: E712
        )
    ).all()
    return _add_participants(session, exam_id, users)


def remove_participant(
    session: Session,
    exam_id: uuid.UUID,
    userid: str,
) -> bool:
    participant = session.exec(
        select(ExamParticipant).where(
            ExamParticipant.exam_id == exam_id,
            ExamParticipant.userid == userid,
        )
    ).first()
    if not participant:
        return False
    session.delete(participant)
    session.commit()
    return True


def list_participants(
    session: Session,
    exam_id: uuid.UUID,
    *,
    page: int = 1,
    limit: int = 20,
    q: str | None = None,
) -> tuple[list[ExamParticipant], int]:
    base = select(ExamParticipant).where(ExamParticipant.exam_id == exam_id)
    count_base = (
        select(func.count()).select_from(ExamParticipant)
        .where(ExamParticipant.exam_id == exam_id)
    )

    if q:
        like = f"%{q}%"
        base = base.where(
            ExamParticipant.name_snapshot.ilike(like)  # type: ignore[union-attr]
            | ExamParticipant.userid.ilike(like)       # type: ignore[union-attr]
        )
        count_base = count_base.where(
            ExamParticipant.name_snapshot.ilike(like)  # type: ignore[union-attr]
            | ExamParticipant.userid.ilike(like)       # type: ignore[union-attr]
        )

    count = session.exec(count_base).one()
    offset = (page - 1) * limit
    rows = session.exec(
        base.order_by(ExamParticipant.created_at.desc()).offset(offset).limit(limit)
    ).all()
    return list(rows), count


# ─── Exam Statistics ─────────────────────────────────────────────────────────

def get_exam_statistics(session: Session, exam_id: uuid.UUID) -> ExamStatistics:
    """Get statistics for a single exam."""
    participants = session.exec(
        select(ExamParticipant).where(ExamParticipant.exam_id == exam_id)
    ).all()

    total = len(participants)
    completed = [p for p in participants if p.completion_status == "COMPLETED"]
    passed = [p for p in completed if p.final_passed]
    failed = [p for p in completed if not p.final_passed]
    not_started = [p for p in participants if p.completion_status == "NOT_STARTED"]
    in_progress = [p for p in participants if p.completion_status == "IN_PROGRESS"]

    # Pass rate (percentage)
    pass_rate = (len(passed) / len(completed) * 100) if completed else 0.0

    # Score statistics (only from completed participants)
    scores = [p.final_score for p in completed if p.final_score is not None]
    avg_score = sum(scores) / len(scores) if scores else None
    max_score = max(scores) if scores else None
    min_score = min(scores) if scores else None

    distribution = _calculate_score_distribution(scores)

    return ExamStatistics(
        total_participants=total,
        completed_count=len(completed),
        passed_count=len(passed),
        failed_count=len(failed),
        not_started_count=len(not_started),
        in_progress_count=len(in_progress),
        pass_rate=round(pass_rate, 1),
        avg_score=round(avg_score, 1) if avg_score is not None else None,
        max_score=max_score,
        min_score=min_score,
        score_distribution=distribution,
    )


def _calculate_score_distribution(scores: list[float]) -> list[ScoreDistribution]:
    """Calculate score distribution across fixed ranges."""
    ranges = [
        ("0-59", 0, 59),
        ("60-69", 60, 69),
        ("70-79", 70, 79),
        ("80-89", 80, 89),
        ("90-100", 90, 100),
    ]
    distribution = []
    for label, low, high in ranges:
        count = sum(1 for s in scores if low <= s <= high)
        distribution.append(ScoreDistribution(range_label=label, count=count))
    return distribution


# ─── System Dashboard ───────────────────────────────────────────────────────

def get_system_stats(session: Session) -> SystemDashboardStats:
    """Get system-level dashboard statistics for admins."""

    # Exam count
    exam_count = session.exec(select(func.count()).select_from(Exam)).one()

    # Total participation count
    total_participation = session.exec(
        select(func.count()).select_from(ExamParticipant)
    ).one()

    # Pass rate — based on completed participants only
    completed_count = session.exec(
        select(func.count()).select_from(ExamParticipant)
        .where(ExamParticipant.completion_status == "COMPLETED")
    ).one()
    passed_count = session.exec(
        select(func.count()).select_from(ExamParticipant)
        .where(
            ExamParticipant.completion_status == "COMPLETED",
            ExamParticipant.final_passed == True,  # noqa: E712
        )
    ).one()
    pass_rate = (passed_count / completed_count * 100) if completed_count else 0.0

    # Question count
    question_count = session.exec(select(func.count()).select_from(Question)).one()

    # Paper snapshot count
    paper_count = session.exec(
        select(func.count()).select_from(ExamPaperSnapshot)
    ).one()

    # Question type distribution
    type_rows = session.exec(
        select(Question.question_type, func.count())
        .group_by(Question.question_type)
    ).all()
    type_distribution = [
        QuestionTypeCount(question_type=qt, count=c) for qt, c in type_rows
    ]

    # Device type distribution
    device_rows = session.exec(
        select(ExamAttempt.device_type, func.count())
        .where(ExamAttempt.device_type.isnot(None))
        .group_by(ExamAttempt.device_type)
    ).all()
    device_distribution = [
        DeviceTypeCount(device_type=dt or "UNKNOWN", count=c) for dt, c in device_rows
    ]

    # Difficulty distribution
    difficulty_rows = session.exec(
        select(Question.difficulty, func.count())
        .where(Question.difficulty.isnot(None))
        .group_by(Question.difficulty)
    ).all()
    difficulty_distribution = [
        DifficultyCount(difficulty=d or "MEDIUM", count=c) for d, c in difficulty_rows
    ]

    return SystemDashboardStats(
        exam_count=exam_count,
        total_participation=total_participation,
        overall_pass_rate=round(pass_rate, 1),
        question_count=question_count,
        paper_count=paper_count,
        question_type_distribution=type_distribution,
        device_type_distribution=device_distribution,
        difficulty_distribution=difficulty_distribution,
    )


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _collect_child_departments(
    session: Session,
    parent_id: int,
    result: set[int],
) -> None:
    """Recursively collect all child department IDs."""
    children = session.exec(
        select(WecomDepartment.id).where(WecomDepartment.parentid == parent_id)
    ).all()
    for child_id in children:
        result.add(child_id)
        _collect_child_departments(session, child_id, result)


# ─── Question Bank ──────────────────────────────────────────────────────────

def list_question_bank(
    session: Session,
    *,
    page: int = 1,
    limit: int = 20,
    category_id: int | None = None,
) -> tuple[list[dict], int]:
    """List exams that have generated papers (question bank)."""
    from app.modules.exam_management.schemas import QuestionBankItem

    base = (
        select(
            Exam,
            ExamPaper.status.label("paper_status"),
            ExamPaper.generated_at.label("paper_generated_at"),
        )
        .join(ExamPaper, ExamPaper.exam_id == Exam.id)
        .where(Exam.status.in_(["PUBLISHED", "ARCHIVED"]))
    )
    count_base = (
        select(func.count())
        .select_from(Exam)
        .join(ExamPaper, ExamPaper.exam_id == Exam.id)
        .where(Exam.status.in_(["PUBLISHED", "ARCHIVED"]))
    )

    if category_id is not None:
        base = base.where(Exam.category_id == category_id)
        count_base = count_base.where(Exam.category_id == category_id)

    count = session.exec(count_base).one()
    offset = (page - 1) * limit
    rows = session.exec(
        base.order_by(ExamPaper.created_at.desc()).offset(offset).limit(limit)
    ).all()

    # Batch-load category names
    cat_ids = {row[0].category_id for row in rows if row[0].category_id is not None}
    cat_map: dict[int, str] = {}
    if cat_ids:
        categories = session.exec(
            select(ExamCategory).where(ExamCategory.id.in_(cat_ids))
        ).all()
        cat_map = {c.id: c.name for c in categories}

    # Batch-load question counts and total scores
    exam_ids = [row[0].id for row in rows]
    question_stats: dict[uuid.UUID, tuple[int, float]] = {}
    if exam_ids:
        q_rows = session.exec(
            select(
                Question.exam_id,
                func.count().label("cnt"),
                func.coalesce(func.sum(Question.score), 0).label("total"),
            )
            .where(Question.exam_id.in_(exam_ids))
            .group_by(Question.exam_id)
        ).all()
        question_stats = {r.exam_id: (r.cnt, float(r.total)) for r in q_rows}

    result = []
    for exam, paper_status, paper_generated_at in rows:
        q_count, q_total = question_stats.get(exam.id, (0, 0.0))
        result.append(
            QuestionBankItem(
                exam_id=exam.id,
                exam_name=exam.name,
                category_id=exam.category_id,
                category_name=cat_map.get(exam.category_id),
                status=paper_status,
                generated_at=paper_generated_at,
                question_count=q_count,
                total_score=q_total,
            )
        )

    return result, count


def get_question_bank_detail(
    session: Session,
    exam_id: uuid.UUID,
) -> dict | None:
    """Get exam paper detail for question bank preview."""
    exam = session.get(Exam, exam_id)
    if not exam:
        return None

    # Check if paper has been generated
    paper = session.exec(
        select(ExamPaper).where(ExamPaper.exam_id == exam_id)
    ).first()
    if not paper:
        return None

    # Reuse existing get_paper function
    paper_data = get_paper(session, exam_id)
    return {
        "exam_id": exam.id,
        "exam_name": exam.name,
        "questions": paper_data["questions"],
        "total_score": paper_data["total_score"],
        "question_count": paper_data["question_count"],
    }


# ─── Docx Generation Scheduler ─────────────────────────────────────────────

def check_and_generate_expired_exam_papers(session: Session) -> None:
    """Check for exams that need docx papers and generate them.

    Covers two cases:
    1. PUBLISHED exams whose end_at has passed (time-based expiry).
    2. ARCHIVED exams (explicitly archived by admin, regardless of time).

    Both cases are idempotent via _generate_paper_if_needed.
    """
    now = datetime.now(timezone.utc)

    # Case 1: published exams whose window has closed
    expired_published = session.exec(
        select(Exam)
        .where(Exam.end_at <= now)
        .where(Exam.status == "PUBLISHED")
    ).all()

    # Case 2: archived exams (may have been archived before end_at)
    archived_exams = session.exec(
        select(Exam).where(Exam.status == "ARCHIVED")
    ).all()

    seen: set[uuid.UUID] = set()
    for exam in [*expired_published, *archived_exams]:
        if exam.id in seen:
            continue
        seen.add(exam.id)
        _generate_paper_if_needed(session, exam)

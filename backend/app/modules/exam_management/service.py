"""
Exam Management Module — Service layer
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from app.models import User
from app.modules.data_sync.models import WecomDepartment
from app.modules.exam_management.models import (
    Exam,
    ExamParticipant,
    Question,
    QuestionOption,
)
from app.modules.exam_management.schemas import (
    ExamCreate,
    ExamUpdate,
    PaperSaveRequest,
    PublishValidation,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


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
    q: str | None = None,
) -> tuple[list[Exam], int]:
    base = select(Exam)
    count_base = select(func.count()).select_from(Exam)

    if status:
        base = base.where(Exam.status == status)
        count_base = count_base.where(Exam.status == status)
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
    # Cascade: questions, options, participants
    questions = session.exec(
        select(Question).where(Question.exam_id == exam.id)
    ).all()
    for q in questions:
        opts = session.exec(
            select(QuestionOption).where(QuestionOption.question_id == q.id)
        ).all()
        for o in opts:
            session.delete(o)
        session.delete(q)

    participants = session.exec(
        select(ExamParticipant).where(ExamParticipant.exam_id == exam.id)
    ).all()
    for p in participants:
        session.delete(p)

    session.delete(exam)
    session.commit()


# ─── Paper (Questions + Options) ─────────────────────────────────────────────

def save_paper(
    session: Session,
    exam: Exam,
    data: PaperSaveRequest,
) -> None:
    """Replace all questions/options for an exam."""
    if exam.status != "DRAFT":
        raise ValueError("只能编辑未发布考试的试卷")

    # Delete existing
    old_questions = session.exec(
        select(Question).where(Question.exam_id == exam.id)
    ).all()
    for q in old_questions:
        old_opts = session.exec(
            select(QuestionOption).where(QuestionOption.question_id == q.id)
        ).all()
        for o in old_opts:
            session.delete(o)
        session.delete(q)

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

    result = []
    total_score = 0.0
    for q in questions:
        total_score += q.score
        options = session.exec(
            select(QuestionOption)
            .where(QuestionOption.question_id == q.id)
            .order_by(QuestionOption.sort_no)
        ).all()
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
        for q in questions:
            if not q.stem or not q.stem.strip():
                errors.append(f"题号 {q.sort_no} 缺少题干")
            if q.score <= 0:
                errors.append(f"题号 {q.sort_no} 分数必须大于 0")

            options = session.exec(
                select(QuestionOption).where(QuestionOption.question_id == q.id)
            ).all()
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
    if exam.pass_score > total_score:
        errors.append(f"及格线 ({exam.pass_score}) 不能超过试卷总分 ({total_score})")

    return PublishValidation(valid=len(errors) == 0, errors=errors)


def publish_exam(session: Session, exam: Exam) -> Exam:
    validation = validate_publish(session, exam)
    if not validation.valid:
        raise ValueError("发布校验失败: " + "; ".join(validation.errors))

    exam.status = "PUBLISHED"
    exam.published_at = _now()
    exam.updated_at = _now()
    session.add(exam)
    session.commit()
    session.refresh(exam)
    return exam


def archive_exam(session: Session, exam: Exam) -> Exam:
    if exam.status == "DRAFT":
        raise ValueError("未发布的考试不能归档")
    exam.status = "ARCHIVED"
    exam.updated_at = _now()
    session.add(exam)
    session.commit()
    session.refresh(exam)
    return exam


# ─── Participants ────────────────────────────────────────────────────────────

def _add_participants(
    session: Session,
    exam_id: uuid.UUID,
    users: list[User],
) -> int:
    """Add users as participants, skip duplicates. Returns count added."""
    existing = session.exec(
        select(ExamParticipant.userid).where(ExamParticipant.exam_id == exam_id)
    ).all()
    existing_set = set(existing)

    added = 0
    for user in users:
        if user.wecom_userid in existing_set:
            continue
        participant = ExamParticipant(
            exam_id=exam_id,
            userid=user.wecom_userid or "",
            name_snapshot=user.full_name,
        )
        session.add(participant)
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
    """Add specific users by userid."""
    users = session.exec(
        select(User).where(
            User.wecom_userid.in_(userids),  # type: ignore[union-attr]
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

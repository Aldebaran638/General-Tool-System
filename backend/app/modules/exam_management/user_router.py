"""
Exam Module — User-facing API Router  (/api/v1/my-exams/*)

Endpoints for regular users (no admin required):
  GET    /my-exams                — list exams I'm enrolled in
  GET    /my-exams/{id}           — get exam detail (if enrolled)
  GET    /my-exams/{id}/paper     — get exam paper for taking
  POST   /my-exams/{id}/submit    — submit exam answers
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select, func

from app.api.deps import CurrentUser, SessionDep
from app.modules.exam_management.models import (
    Exam,
    ExamAnswer,
    ExamAttempt,
    ExamParticipant,
    Question,
    QuestionOption,
)
from app.modules.exam_management.schemas import ExamPublic


router = APIRouter(prefix="/my-exams", tags=["my-exams"])


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_user_identifiers(user: CurrentUser) -> list[str]:
    """Get all possible user identifiers for matching (wecom_userid, email, UUID)."""
    ids = []
    if user.wecom_userid:
        ids.append(user.wecom_userid)
    if user.email:
        ids.append(user.email)
    ids.append(str(user.id))  # Always include UUID
    return ids


# ─── Schemas ─────────────────────────────────────────────────────────────────

from pydantic import BaseModel


class MyExamPublic(BaseModel):
    """Exam info for regular users."""
    id: uuid.UUID
    name: str
    description: str | None
    status: str
    start_at: datetime
    end_at: datetime
    duration_minutes: int
    pass_score: float
    show_answer: bool
    created_at: datetime
    # Attempt stats
    attempt_count: int = 0
    best_score: float | None = None
    last_score: float | None = None
    passed: bool = False
    completion_status: str = "NOT_STARTED"  # NOT_STARTED / IN_PROGRESS / COMPLETED / NOT_COMPLETED
    can_attempt: bool = True


class MyExamsPublic(BaseModel):
    data: list[MyExamPublic]
    count: int


class ExamQuestionOption(BaseModel):
    id: uuid.UUID
    option_key: str
    option_text: str


class ExamQuestion(BaseModel):
    id: uuid.UUID
    question_type: str
    stem: str
    score: float
    sort_no: int
    options: list[ExamQuestionOption]


class ExamPaper(BaseModel):
    exam_id: uuid.UUID
    exam_name: str
    duration_minutes: int
    pass_score: float
    questions: list[ExamQuestion]


class SubmitAnswer(BaseModel):
    question_id: uuid.UUID
    selected_option_ids: list[uuid.UUID]


class SubmitRequest(BaseModel):
    attempt_id: uuid.UUID
    answers: list[SubmitAnswer]


class SubmitResult(BaseModel):
    total_score: float
    max_score: float
    passed: bool
    correct_count: int
    total_count: int


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("", response_model=MyExamsPublic, summary="我参与的考试列表")
def list_my_exams(
    session: SessionDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> MyExamsPublic:
    """List exams that the current user is enrolled in."""
    user_ids = _get_user_identifiers(current_user)

    # Find exams where user is a participant
    query = (
        select(Exam)
        .join(ExamParticipant, ExamParticipant.exam_id == Exam.id)
        .where(ExamParticipant.userid.in_(user_ids))
        .where(Exam.status == "PUBLISHED")
        .order_by(Exam.start_at.desc())
    )

    # Count
    count_query = (
        select(func.count())
        .select_from(Exam)
        .join(ExamParticipant, ExamParticipant.exam_id == Exam.id)
        .where(ExamParticipant.userid.in_(user_ids))
        .where(Exam.status == "PUBLISHED")
    )

    count = session.exec(count_query).one()
    offset = (page - 1) * limit
    exams = session.exec(query.offset(offset).limit(limit)).all()

    if not exams:
        return MyExamsPublic(data=[], count=count)

    # Batch fetch attempt stats for all exams in one query
    exam_ids = [e.id for e in exams]
    stats_query = (
        select(
            ExamAttempt.exam_id,
            func.count().label("attempt_count"),
            func.max(ExamAttempt.total_score).label("best_score"),
        )
        .where(ExamAttempt.exam_id.in_(exam_ids))
        .where(ExamAttempt.userid.in_(user_ids))
        .group_by(ExamAttempt.exam_id)
    )
    stats_rows = session.exec(stats_query).all()
    stats_map = {row.exam_id: row for row in stats_rows}

    # Batch fetch participant info (includes final score and completion status)
    participants_query = (
        select(ExamParticipant)
        .where(ExamParticipant.exam_id.in_(exam_ids))
        .where(ExamParticipant.userid.in_(user_ids))
    )
    participants = session.exec(participants_query).all()
    participant_map = {p.exam_id: p for p in participants}

    # Build exam list with attempt stats
    exam_data = []
    for e in exams:
        stats = stats_map.get(e.id)
        participant = participant_map.get(e.id)

        attempt_count = stats.attempt_count if stats else 0
        best_score = float(stats.best_score) if stats and stats.best_score else None

        # Use final score from participant (applies final score rule)
        final_score = float(participant.final_score) if participant and participant.final_score is not None else None
        passed = bool(participant.final_passed) if participant else False
        completion_status = participant.completion_status if participant else "NOT_STARTED"

        # Check if user can attempt
        can_attempt = True
        if e.attempt_limit_type == "LIMITED" and e.attempt_limit_count is not None:
            can_attempt = attempt_count < e.attempt_limit_count

        exam_data.append(MyExamPublic(
            id=e.id,
            name=e.name,
            description=e.description,
            status=e.status,
            start_at=e.start_at,
            end_at=e.end_at,
            duration_minutes=e.duration_minutes,
            pass_score=e.pass_score,
            show_answer=e.show_answer,
            created_at=e.created_at,
            attempt_count=attempt_count,
            best_score=best_score,
            last_score=final_score,
            passed=passed,
            completion_status=completion_status,
            can_attempt=can_attempt,
        ))

    return MyExamsPublic(data=exam_data, count=count)


@router.get("/{exam_id}", response_model=MyExamPublic, summary="考试详情")
def get_my_exam(
    session: SessionDep,
    current_user: CurrentUser,
    exam_id: uuid.UUID,
) -> MyExamPublic:
    """Get exam detail if user is enrolled."""
    user_ids = _get_user_identifiers(current_user)

    exam = session.exec(
        select(Exam)
        .join(ExamParticipant, ExamParticipant.exam_id == Exam.id)
        .where(Exam.id == exam_id)
        .where(ExamParticipant.userid.in_(user_ids))
        .where(Exam.status == "PUBLISHED")
    ).first()

    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在或未参与")

    return MyExamPublic(
        id=exam.id,
        name=exam.name,
        description=exam.description,
        status=exam.status,
        start_at=exam.start_at,
        end_at=exam.end_at,
        duration_minutes=exam.duration_minutes,
        pass_score=exam.pass_score,
        show_answer=exam.show_answer,
        created_at=exam.created_at,
    )


@router.get("/{exam_id}/paper", response_model=ExamPaper, summary="获取试卷")
def get_exam_paper(
    session: SessionDep,
    current_user: CurrentUser,
    exam_id: uuid.UUID,
) -> ExamPaper:
    """Get exam paper for taking (without correct answers)."""
    user_ids = _get_user_identifiers(current_user)

    # Verify enrollment
    participant = session.exec(
        select(ExamParticipant)
        .where(ExamParticipant.exam_id == exam_id)
        .where(ExamParticipant.userid.in_(user_ids))
    ).first()

    if not participant:
        raise HTTPException(status_code=403, detail="未参与此考试")

    # Get exam
    exam = session.get(Exam, exam_id)
    if not exam or exam.status != "PUBLISHED":
        raise HTTPException(status_code=404, detail="考试不存在或未发布")

    # Get questions
    questions = session.exec(
        select(Question)
        .where(Question.exam_id == exam_id)
        .order_by(Question.sort_no)
    ).all()

    if not questions:
        return ExamPaper(
            exam_id=exam.id,
            exam_name=exam.name,
            duration_minutes=exam.duration_minutes,
            pass_score=exam.pass_score,
            questions=[],
        )

    # Batch load all options for all questions at once
    question_ids = [q.id for q in questions]
    all_options = session.exec(
        select(QuestionOption)
        .where(QuestionOption.question_id.in_(question_ids))
        .order_by(QuestionOption.sort_no)
    ).all()

    # Group options by question_id
    options_by_question: dict[uuid.UUID, list[QuestionOption]] = {}
    for opt in all_options:
        options_by_question.setdefault(opt.question_id, []).append(opt)

    # Build paper questions
    paper_questions = []
    for q in questions:
        options = options_by_question.get(q.id, [])
        paper_questions.append(
            ExamQuestion(
                id=q.id,
                question_type=q.question_type,
                stem=q.stem,
                score=q.score,
                sort_no=q.sort_no,
                options=[
                    ExamQuestionOption(
                        id=o.id,
                        option_key=o.option_key,
                        option_text=o.option_text,
                    )
                    for o in options
                ],
            )
        )

    return ExamPaper(
        exam_id=exam.id,
        exam_name=exam.name,
        duration_minutes=exam.duration_minutes,
        pass_score=exam.pass_score,
        questions=paper_questions,
    )


@router.post("/{exam_id}/start", summary="开始考试")
def start_exam(
    session: SessionDep,
    current_user: CurrentUser,
    exam_id: uuid.UUID,
) -> dict:
    """Start an exam and generate random order snapshots if enabled."""
    from datetime import timedelta
    import random

    user_ids = _get_user_identifiers(current_user)

    # Verify enrollment
    participant = session.exec(
        select(ExamParticipant)
        .where(ExamParticipant.exam_id == exam_id)
        .where(ExamParticipant.userid.in_(user_ids))
    ).first()

    if not participant:
        raise HTTPException(status_code=403, detail="未参与此考试")

    # Get exam with lock to prevent race condition
    exam = session.exec(
        select(Exam).where(Exam.id == exam_id).with_for_update()
    ).first()
    if not exam or exam.status != "PUBLISHED":
        raise HTTPException(status_code=404, detail="考试不存在或未发布")

    # Check time window
    now = datetime.now(timezone.utc)
    start_at = exam.start_at if exam.start_at.tzinfo else exam.start_at.replace(tzinfo=timezone.utc)
    end_at = exam.end_at if exam.end_at.tzinfo else exam.end_at.replace(tzinfo=timezone.utc)
    if now < start_at:
        raise HTTPException(status_code=400, detail="考试尚未开始")
    if now > end_at:
        raise HTTPException(status_code=400, detail="考试已结束")

    # Check for existing IN_PROGRESS attempt
    user_id = participant.userid
    existing_attempt = session.exec(
        select(ExamAttempt)
        .where(ExamAttempt.exam_id == exam_id)
        .where(ExamAttempt.userid == user_id)
        .where(ExamAttempt.status == "IN_PROGRESS")
    ).first()

    if existing_attempt:
        # Check if existing attempt has expired
        if existing_attempt.expire_at and now > existing_attempt.expire_at:
            # Mark as expired
            existing_attempt.status = "EXPIRED"
            session.add(existing_attempt)
        else:
            # Return existing attempt
            return {
                "attempt_id": str(existing_attempt.id),
                "started_at": existing_attempt.started_at.isoformat() if existing_attempt.started_at else None,
                "expire_at": existing_attempt.expire_at.isoformat() if existing_attempt.expire_at else None,
                "duration_minutes": exam.duration_minutes,
            }

    # Check attempt limits
    attempt_count = session.exec(
        select(func.count())
        .select_from(ExamAttempt)
        .where(ExamAttempt.exam_id == exam_id)
        .where(ExamAttempt.userid == user_id)
    ).one()

    if exam.attempt_limit_type == "LIMITED" and exam.attempt_limit_count is not None:
        if attempt_count >= exam.attempt_limit_count:
            raise HTTPException(status_code=400, detail="已达最大考试次数限制")

    # Get questions
    questions = session.exec(
        select(Question).where(Question.exam_id == exam_id).order_by(Question.sort_no)
    ).all()

    if not questions:
        raise HTTPException(status_code=400, detail="试卷没有题目")

    # Generate random order snapshots
    question_order = [str(q.id) for q in questions]
    if exam.random_question_order:
        random.shuffle(question_order)

    # Batch load all options
    question_ids = [q.id for q in questions]
    all_options = session.exec(
        select(QuestionOption)
        .where(QuestionOption.question_id.in_(question_ids))
        .order_by(QuestionOption.sort_no)
    ).all()
    options_by_question: dict[uuid.UUID, list[QuestionOption]] = {}
    for opt in all_options:
        options_by_question.setdefault(opt.question_id, []).append(opt)

    option_order = {}
    for q in questions:
        options = options_by_question.get(q.id, [])
        option_ids = [str(o.id) for o in options]
        if exam.random_option_order:
            random.shuffle(option_ids)
        option_order[str(q.id)] = option_ids

    # Create attempt with snapshots
    attempt = ExamAttempt(
        exam_id=exam_id,
        userid=user_id,
        attempt_no=attempt_count + 1,
        status="IN_PROGRESS",
        total_score=0,
        max_score=0,
        passed=False,
        correct_count=0,
        total_count=len(questions),
        started_at=now,
        expire_at=now + timedelta(minutes=exam.duration_minutes),
        question_order_snapshot=question_order,
        option_order_snapshot=option_order,
    )
    session.add(attempt)

    # Update participant status
    if participant.completion_status == "NOT_STARTED":
        participant.completion_status = "IN_PROGRESS"
        participant.updated_at = now
        session.add(participant)

    session.commit()
    session.refresh(attempt)

    return {
        "attempt_id": str(attempt.id),
        "started_at": attempt.started_at.isoformat(),
        "expire_at": attempt.expire_at.isoformat() if attempt.expire_at else None,
        "duration_minutes": exam.duration_minutes,
    }


@router.post("/{exam_id}/submit", response_model=SubmitResult, summary="提交答卷")
def submit_exam(
    session: SessionDep,
    current_user: CurrentUser,
    exam_id: uuid.UUID,
    body: SubmitRequest,
) -> SubmitResult:
    """Submit exam answers and get score."""
    user_ids = _get_user_identifiers(current_user)

    # Verify enrollment
    participant = session.exec(
        select(ExamParticipant)
        .where(ExamParticipant.exam_id == exam_id)
        .where(ExamParticipant.userid.in_(user_ids))
    ).first()

    if not participant:
        raise HTTPException(status_code=403, detail="未参与此考试")

    # Get exam
    exam = session.get(Exam, exam_id)
    if not exam or exam.status != "PUBLISHED":
        raise HTTPException(status_code=404, detail="考试不存在或未发布")

    # Get the existing IN_PROGRESS attempt
    attempt = session.exec(
        select(ExamAttempt)
        .where(ExamAttempt.id == body.attempt_id)
        .where(ExamAttempt.exam_id == exam_id)
        .where(ExamAttempt.userid == participant.userid)
        .where(ExamAttempt.status == "IN_PROGRESS")
    ).first()

    if not attempt:
        raise HTTPException(status_code=400, detail="考试尝试不存在或已提交")

    # Check if attempt has expired
    now = datetime.now(timezone.utc)
    if attempt.expire_at and now > attempt.expire_at:
        # Auto-submit with current answers
        attempt.status = "EXPIRED"
        # Continue with scoring

    # Check time window
    start_at = exam.start_at if exam.start_at.tzinfo else exam.start_at.replace(tzinfo=timezone.utc)
    end_at = exam.end_at if exam.end_at.tzinfo else exam.end_at.replace(tzinfo=timezone.utc)
    if now < start_at:
        raise HTTPException(status_code=400, detail="考试尚未开始")
    if now > end_at:
        raise HTTPException(status_code=400, detail="考试已结束")

    # Batch load all questions for this exam
    all_questions = session.exec(
        select(Question).where(Question.exam_id == exam_id)
    ).all()
    questions_map = {q.id: q for q in all_questions}

    # Calculate max_score from all questions (not just answered ones)
    max_score = sum(q.score for q in all_questions)

    # Batch load all options for validation
    all_options = session.exec(
        select(QuestionOption)
        .where(QuestionOption.question_id.in_(list(questions_map.keys())))
    ).all()
    options_by_question: dict[uuid.UUID, set[uuid.UUID]] = {}
    for opt in all_options:
        options_by_question.setdefault(opt.question_id, set()).add(opt.id)

    # Batch load correct options
    correct_options_map: dict[uuid.UUID, set[uuid.UUID]] = {}
    for qid, opts in options_by_question.items():
        correct_options = session.exec(
            select(QuestionOption.id)
            .where(QuestionOption.question_id == qid)
            .where(QuestionOption.is_correct.is_(True))
        ).all()
        correct_options_map[qid] = set(correct_options)

    # Validate submit_rule: ALL_REQUIRED requires all questions answered
    if exam.submit_rule == "ALL_REQUIRED" and len(body.answers) != len(all_questions):
        raise HTTPException(status_code=400, detail=f"必须回答所有 {len(all_questions)} 道题目")

    # Validate and score answers
    total_score = 0.0
    correct_count = 0
    total_count = len(all_questions)
    answered_question_ids = set()

    for answer in body.answers:
        # Check for duplicate answers
        if answer.question_id in answered_question_ids:
            raise HTTPException(status_code=400, detail="存在重复的答案")
        answered_question_ids.add(answer.question_id)

        # Validate question belongs to exam
        question = questions_map.get(answer.question_id)
        if not question:
            raise HTTPException(status_code=400, detail="答案中包含不属于此考试的题目")

        # Validate selected options belong to this question
        valid_options = options_by_question.get(answer.question_id, set())
        selected_set = set(answer.selected_option_ids)
        if not selected_set.issubset(valid_options):
            raise HTTPException(status_code=400, detail="答案中包含不属于此题目的选项")

        # Get correct options for this question
        correct_set = correct_options_map.get(answer.question_id, set())

        # Check if answer is correct
        if correct_set == selected_set:
            total_score += question.score
            correct_count += 1

    passed = total_score >= exam.pass_score

    # Update the existing attempt
    attempt.status = "SUBMITTED"
    attempt.total_score = total_score
    attempt.max_score = max_score
    attempt.passed = passed
    attempt.correct_count = correct_count
    attempt.total_count = total_count
    attempt.submitted_at = now
    session.add(attempt)
    session.flush()

    # Save individual answers
    for answer in body.answers:
        question = questions_map.get(answer.question_id)
        if not question:
            continue

        correct_set = correct_options_map.get(answer.question_id, set())
        selected_set = set(answer.selected_option_ids)
        is_correct = correct_set == selected_set
        score_awarded = question.score if is_correct else 0

        exam_answer = ExamAnswer(
            attempt_id=attempt.id,
            question_id=answer.question_id,
            selected_option_ids=[str(oid) for oid in answer.selected_option_ids],
            is_correct=is_correct,
            score_awarded=score_awarded,
        )
        session.add(exam_answer)

    # Update participant's completion status and final score
    # Rule: If has passing attempt, use last passing score; otherwise use last attempt
    all_attempts = session.exec(
        select(ExamAttempt)
        .where(ExamAttempt.exam_id == exam_id)
        .where(ExamAttempt.userid == participant.userid)
        .where(ExamAttempt.status.in_(["SUBMITTED", "AUTO_SUBMITTED"]))
        .order_by(ExamAttempt.submitted_at.asc())
    ).all()

    passed_attempts = [a for a in all_attempts if a.passed]

    if passed_attempts:
        # Use last passing attempt
        final_attempt = passed_attempts[-1]
        participant.completion_status = "COMPLETED"
        participant.completed_at = final_attempt.submitted_at
    else:
        # Use last attempt
        final_attempt = all_attempts[-1] if all_attempts else None
        participant.completion_status = "NOT_COMPLETED"
        participant.completed_at = None

    if final_attempt:
        participant.final_score = final_attempt.total_score
        participant.final_passed = final_attempt.passed
        participant.final_attempt_id = final_attempt.id

    participant.updated_at = now
    session.add(participant)
    session.commit()

    return SubmitResult(
        total_score=total_score,
        max_score=max_score,
        passed=passed,
        correct_count=correct_count,
        total_count=total_count,
    )


@router.get("/{exam_id}/attempts", summary="获取考试尝试记录")
def get_exam_attempts(
    session: SessionDep,
    current_user: CurrentUser,
    exam_id: uuid.UUID,
) -> list[dict]:
    """Get all attempts for an exam by the current user."""
    user_ids = _get_user_identifiers(current_user)

    # Verify enrollment
    participant = session.exec(
        select(ExamParticipant)
        .where(ExamParticipant.exam_id == exam_id)
        .where(ExamParticipant.userid.in_(user_ids))
    ).first()

    if not participant:
        raise HTTPException(status_code=403, detail="未参与此考试")

    # Get attempts
    attempts = session.exec(
        select(ExamAttempt)
        .where(ExamAttempt.exam_id == exam_id)
        .where(ExamAttempt.userid == participant.userid)
        .order_by(ExamAttempt.submitted_at.desc())
    ).all()

    return [
        {
            "id": str(a.id),
            "attempt_no": a.attempt_no,
            "status": a.status,
            "total_score": a.total_score,
            "max_score": a.max_score,
            "passed": a.passed,
            "correct_count": a.correct_count,
            "total_count": a.total_count,
            "started_at": a.started_at.isoformat() if a.started_at else None,
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
        }
        for a in attempts
    ]


@router.get("/{exam_id}/attempts/{attempt_id}/answers", summary="获取考试答案详情")
def get_attempt_answers(
    session: SessionDep,
    current_user: CurrentUser,
    exam_id: uuid.UUID,
    attempt_id: uuid.UUID,
) -> dict:
    """Get detailed answers for an attempt, including correct answers if show_answer is enabled."""
    user_ids = _get_user_identifiers(current_user)

    # Verify enrollment
    participant = session.exec(
        select(ExamParticipant)
        .where(ExamParticipant.exam_id == exam_id)
        .where(ExamParticipant.userid.in_(user_ids))
    ).first()

    if not participant:
        raise HTTPException(status_code=403, detail="未参与此考试")

    # Get exam
    exam = session.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    # Get attempt
    attempt = session.exec(
        select(ExamAttempt)
        .where(ExamAttempt.id == attempt_id)
        .where(ExamAttempt.exam_id == exam_id)
        .where(ExamAttempt.userid == participant.userid)
    ).first()

    if not attempt:
        raise HTTPException(status_code=404, detail="尝试记录不存在")

    # Get answers
    answers = session.exec(
        select(ExamAnswer).where(ExamAnswer.attempt_id == attempt_id)
    ).all()

    # Get questions and options
    questions = session.exec(
        select(Question).where(Question.exam_id == exam_id)
    ).all()
    questions_map = {q.id: q for q in questions}

    question_ids = [q.id for q in questions]
    all_options = session.exec(
        select(QuestionOption).where(QuestionOption.question_id.in_(question_ids))
    ).all()
    options_by_question = {}
    for opt in all_options:
        options_by_question.setdefault(opt.question_id, []).append(opt)

    # Build response
    answer_details = []
    for answer in answers:
        question = questions_map.get(answer.question_id)
        if not question:
            continue

        options = options_by_question.get(answer.question_id, [])
        answer_detail = {
            "question_id": str(answer.question_id),
            "question_type": question.question_type,
            "stem": question.stem,
            "score": question.score,
            "selected_option_ids": [str(oid) for oid in answer.selected_option_ids],
            "is_correct": answer.is_correct,
            "score_awarded": answer.score_awarded,
            "options": [
                {
                    "id": str(o.id),
                    "option_key": o.option_key,
                    "option_text": o.option_text,
                }
                for o in options
            ],
        }

        # Include correct answers if show_answer is enabled
        if exam.show_answer:
            correct_options = [o for o in options if o.is_correct]
            answer_detail["correct_option_ids"] = [str(o.id) for o in correct_options]

        answer_details.append(answer_detail)

    return {
        "attempt_id": str(attempt.id),
        "exam_name": exam.name,
        "total_score": attempt.total_score,
        "max_score": attempt.max_score,
        "passed": attempt.passed,
        "correct_count": attempt.correct_count,
        "total_count": attempt.total_count,
        "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
        "answers": answer_details,
    }

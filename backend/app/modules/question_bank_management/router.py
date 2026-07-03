"""
Question Bank Management API Router  (/api/v1/question-bank-management/*)

Endpoints:
  GET    /sets                         — list bank sets (paginated)
  POST   /sets                         — create bank set
  GET    /sets/{set_id}                — bank set detail with questions
  PUT    /sets/{set_id}                — update bank set
  DELETE /sets/{set_id}                — delete bank set
  POST   /sets/{set_id}/questions      — create bank question
  PUT    /sets/{set_id}/questions/{question_id} — update bank question
  DELETE /sets/{set_id}/questions/{question_id} — delete bank question

All endpoints require exam admin or superuser.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import SessionDep
from app.modules.question_bank_management.schemas import (
    BankQuestionCreate,
    BankQuestionPublic,
    BankQuestionUpdate,
    QuestionBankSetCreate,
    QuestionBankSetDetailPublic,
    QuestionBankSetPublic,
    QuestionBankSetsPublic,
    QuestionBankSetUpdate,
)
from app.modules.question_bank_management.service import (
    create_bank_question,
    create_set,
    delete_bank_question,
    delete_set,
    get_bank_question,
    get_set,
    get_set_with_questions,
    list_sets,
    update_bank_question,
    update_set,
)
from app.modules.wecom_gateway.deps import RequireExamAdmin

router = APIRouter(
    prefix="/question-bank-management",
    tags=["question-bank-management"],
)


# ─── helpers ─────────────────────────────────────────────────────────────────

def _set_to_public(bank_set) -> QuestionBankSetPublic:
    return QuestionBankSetPublic(
        id=bank_set.id,
        name=bank_set.name,
        description=bank_set.description,
        category_id=bank_set.category_id,
        created_by=bank_set.created_by,
        created_at=bank_set.created_at,
        updated_at=bank_set.updated_at,
    )


def _question_to_public(question, options=None) -> BankQuestionPublic:
    if options is None:
        options = getattr(question, "options", []) or []
    return BankQuestionPublic(
        id=question.id,
        set_id=question.set_id,
        question_type=question.question_type,
        stem=question.stem,
        score=question.score,
        difficulty=question.difficulty,
        sort_no=question.sort_no,
        analysis=question.analysis,
        options=[
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
    )


def _get_set_or_404(session: SessionDep, set_id: uuid.UUID):
    bank_set = get_set(session, set_id)
    if not bank_set:
        raise HTTPException(status_code=404, detail="题库集不存在")
    return bank_set


def _get_question_or_404(session: SessionDep, question_id: uuid.UUID):
    question = get_bank_question(session, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="题库题目不存在")
    return question


# ─── Bank Set CRUD ───────────────────────────────────────────────────────────

@router.get("/sets", response_model=QuestionBankSetsPublic, summary="题库集列表")
def list_sets_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    q: str | None = Query(default=None, description="按题库集名称搜索"),
    category_id: int | None = Query(default=None, description="按分类筛选"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> QuestionBankSetsPublic:
    sets, count = list_sets(
        session, q=q, category_id=category_id, page=page, limit=limit
    )
    return QuestionBankSetsPublic(
        data=[_set_to_public(s) for s in sets],
        count=count,
    )


@router.post(
    "/sets",
    response_model=QuestionBankSetPublic,
    status_code=status.HTTP_201_CREATED,
    summary="创建题库集",
)
def create_set_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    body: QuestionBankSetCreate,
) -> QuestionBankSetPublic:
    bank_set = create_set(session, body, created_by=current_user.id)
    return _set_to_public(bank_set)


@router.get(
    "/sets/{set_id}",
    response_model=QuestionBankSetDetailPublic,
    summary="题库集详情",
)
def get_set_detail_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    set_id: uuid.UUID,
) -> QuestionBankSetDetailPublic:
    result = get_set_with_questions(session, set_id)
    if not result:
        raise HTTPException(status_code=404, detail="题库集不存在")
    bank_set, questions = result
    return QuestionBankSetDetailPublic(
        **_set_to_public(bank_set).model_dump(),
        questions=[BankQuestionPublic(**q) for q in questions],
    )


@router.put(
    "/sets/{set_id}",
    response_model=QuestionBankSetPublic,
    summary="更新题库集",
)
def update_set_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    set_id: uuid.UUID,
    body: QuestionBankSetUpdate,
) -> QuestionBankSetPublic:
    bank_set = _get_set_or_404(session, set_id)
    updated = update_set(session, bank_set, body)
    return _set_to_public(updated)


@router.delete(
    "/sets/{set_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除题库集",
)
def delete_set_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    set_id: uuid.UUID,
):
    bank_set = _get_set_or_404(session, set_id)
    delete_set(session, bank_set)


# ─── Bank Question CRUD ──────────────────────────────────────────────────────

@router.post(
    "/sets/{set_id}/questions",
    response_model=BankQuestionPublic,
    status_code=status.HTTP_201_CREATED,
    summary="创建题库题目",
)
def create_bank_question_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    set_id: uuid.UUID,
    body: BankQuestionCreate,
) -> BankQuestionPublic:
    _get_set_or_404(session, set_id)
    question, options = create_bank_question(session, set_id, body)
    return _question_to_public(question, options)


@router.put(
    "/sets/{set_id}/questions/{question_id}",
    response_model=BankQuestionPublic,
    summary="更新题库题目",
)
def update_bank_question_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    set_id: uuid.UUID,
    question_id: uuid.UUID,
    body: BankQuestionUpdate,
) -> BankQuestionPublic:
    _get_set_or_404(session, set_id)
    question = _get_question_or_404(session, question_id)
    if question.set_id != set_id:
        raise HTTPException(status_code=404, detail="题库题目不存在")
    question, options = update_bank_question(session, question, body)
    return _question_to_public(question, options)


@router.delete(
    "/sets/{set_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除题库题目",
)
def delete_bank_question_endpoint(
    session: SessionDep,
    current_user: RequireExamAdmin,
    set_id: uuid.UUID,
    question_id: uuid.UUID,
):
    _get_set_or_404(session, set_id)
    question = _get_question_or_404(session, question_id)
    if question.set_id != set_id:
        raise HTTPException(status_code=404, detail="题库题目不存在")
    delete_bank_question(session, question)

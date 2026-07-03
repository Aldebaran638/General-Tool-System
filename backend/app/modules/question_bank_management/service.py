"""
Question Bank Management Module — Service layer
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from app.modules.question_bank_management.models import (
    QuestionBankOption,
    QuestionBankQuestion,
    QuestionBankSet,
)
from app.modules.question_bank_management.schemas import (
    BankQuestionCreate,
    BankQuestionUpdate,
    QuestionBankSetCreate,
    QuestionBankSetUpdate,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─── Set CRUD ────────────────────────────────────────────────────────────────

def list_sets(
    session: Session,
    *,
    q: str | None = None,
    category_id: int | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[QuestionBankSet], int]:
    """Return paginated bank sets, optionally filtered by name or category."""
    base = select(QuestionBankSet)
    count_base = select(func.count()).select_from(QuestionBankSet)

    if q:
        like = f"%{q}%"
        base = base.where(QuestionBankSet.name.ilike(like))  # type: ignore[union-attr]
        count_base = count_base.where(QuestionBankSet.name.ilike(like))  # type: ignore[union-attr]
    if category_id is not None:
        base = base.where(QuestionBankSet.category_id == category_id)
        count_base = count_base.where(QuestionBankSet.category_id == category_id)

    count = session.exec(count_base).one()
    offset = (page - 1) * limit
    rows = session.exec(
        base.order_by(QuestionBankSet.created_at.desc()).offset(offset).limit(limit)
    ).all()
    return list(rows), count


def create_set(
    session: Session,
    data: QuestionBankSetCreate,
    created_by: uuid.UUID,
) -> QuestionBankSet:
    """Create a new bank set."""
    bank_set = QuestionBankSet(**data.model_dump(), created_by=created_by)
    session.add(bank_set)
    session.commit()
    session.refresh(bank_set)
    return bank_set


def get_set(session: Session, set_id: uuid.UUID) -> QuestionBankSet | None:
    """Get a bank set by id."""
    return session.get(QuestionBankSet, set_id)


def get_set_with_questions(
    session: Session,
    set_id: uuid.UUID,
) -> tuple[QuestionBankSet, list[dict]] | None:
    """Get a bank set together with all questions and options."""
    bank_set = session.get(QuestionBankSet, set_id)
    if not bank_set:
        return None

    questions = session.exec(
        select(QuestionBankQuestion)
        .where(QuestionBankQuestion.set_id == set_id)
        .order_by(QuestionBankQuestion.sort_no)
    ).all()

    question_ids = [q.id for q in questions]
    all_options = session.exec(
        select(QuestionBankOption)
        .where(QuestionBankOption.question_id.in_(question_ids))
        .order_by(QuestionBankOption.sort_no)
    ).all()

    options_by_question: dict[uuid.UUID, list[QuestionBankOption]] = {}
    for option in all_options:
        options_by_question.setdefault(option.question_id, []).append(option)

    question_list = []
    for q in questions:
        options = options_by_question.get(q.id, [])
        question_list.append(
            {
                "id": q.id,
                "set_id": q.set_id,
                "question_type": q.question_type,
                "stem": q.stem,
                "score": q.score,
                "difficulty": q.difficulty,
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
            }
        )

    return bank_set, question_list


def update_set(
    session: Session,
    bank_set: QuestionBankSet,
    data: QuestionBankSetUpdate,
) -> QuestionBankSet:
    """Update a bank set's editable fields."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bank_set, field, value)
    bank_set.updated_at = _utcnow()
    session.add(bank_set)
    session.commit()
    session.refresh(bank_set)
    return bank_set


def delete_set(session: Session, bank_set: QuestionBankSet) -> None:
    """Delete a bank set (cascades to questions and options)."""
    session.delete(bank_set)
    session.commit()


# ─── Bank Question CRUD ──────────────────────────────────────────────────────

def get_bank_question(
    session: Session,
    question_id: uuid.UUID,
) -> QuestionBankQuestion | None:
    return session.get(QuestionBankQuestion, question_id)


def create_bank_question(
    session: Session,
    set_id: uuid.UUID,
    data: BankQuestionCreate,
) -> QuestionBankQuestion:
    """Create a question with options inside a bank set."""
    question = QuestionBankQuestion(
        set_id=set_id,
        question_type=data.question_type,
        stem=data.stem,
        score=data.score,
        difficulty=data.difficulty,
        sort_no=data.sort_no,
        analysis=data.analysis,
    )
    session.add(question)
    session.flush()  # get question.id

    for option_data in data.options:
        session.add(
            QuestionBankOption(
                question_id=question.id,
                option_key=option_data.option_key,
                option_text=option_data.option_text,
                is_correct=option_data.is_correct,
                sort_no=option_data.sort_no,
            )
        )

    session.commit()
    session.refresh(question)

    options = session.exec(
        select(QuestionBankOption)
        .where(QuestionBankOption.question_id == question.id)
        .order_by(QuestionBankOption.sort_no)
    ).all()
    return question, list(options)


def update_bank_question(
    session: Session,
    question: QuestionBankQuestion,
    data: BankQuestionUpdate,
) -> tuple[QuestionBankQuestion, list[QuestionBankOption]]:
    """Update a bank question and replace its options."""
    update_data = data.model_dump(exclude_unset=True, exclude={"options"})
    options_data = data.options if data.options is not None else None

    for field, value in update_data.items():
        setattr(question, field, value)

    if options_data is not None:
        existing = session.exec(
            select(QuestionBankOption).where(
                QuestionBankOption.question_id == question.id
            )
        ).all()
        for option in existing:
            session.delete(option)

        for option_data in options_data:
            session.add(
                QuestionBankOption(
                    question_id=question.id,
                    option_key=option_data.option_key,
                    option_text=option_data.option_text,
                    is_correct=option_data.is_correct,
                    sort_no=option_data.sort_no,
                )
            )

    question.updated_at = _utcnow()
    session.add(question)
    session.commit()
    session.refresh(question)

    options = session.exec(
        select(QuestionBankOption)
        .where(QuestionBankOption.question_id == question.id)
        .order_by(QuestionBankOption.sort_no)
    ).all()
    return question, list(options)


def delete_bank_question(
    session: Session,
    question: QuestionBankQuestion,
) -> None:
    """Delete a bank question (cascades to options)."""
    session.delete(question)
    session.commit()

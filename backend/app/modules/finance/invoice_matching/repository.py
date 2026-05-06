"""Invoice Matching Repository

Database access layer for invoice_match records.
"""

import uuid
from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, select

from app.models_core import get_datetime_utc

from .constants import (
    MATCH_STATUS_APPROVED,
    MATCH_STATUS_CANCELLED,
    MATCH_STATUS_CONFIRMED,
    MATCH_STATUS_NEEDS_REVIEW,
)
from .models import InvoiceMatch


def count_matches(
    session: Session,
    *,
    owner_id: uuid.UUID | None = None,
    status: str | None = None,
) -> int:
    stmt = select(func.count(InvoiceMatch.id))
    if owner_id is not None:
        stmt = stmt.where(InvoiceMatch.owner_id == owner_id)
    if status is not None:
        stmt = stmt.where(InvoiceMatch.status == status)
    return session.exec(stmt).one()


def list_matches(
    session: Session,
    *,
    owner_id: uuid.UUID | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[InvoiceMatch]:
    stmt = select(InvoiceMatch)
    if owner_id is not None:
        stmt = stmt.where(InvoiceMatch.owner_id == owner_id)
    if status is not None:
        stmt = stmt.where(InvoiceMatch.status == status)
    stmt = stmt.offset(skip).limit(limit)
    return list(session.exec(stmt).all())


def get_match(session: Session, *, match_id: uuid.UUID) -> InvoiceMatch | None:
    return session.get(InvoiceMatch, match_id)


def get_active_match_for_purchase_record(
    session: Session,
    *,
    purchase_record_id: uuid.UUID,
) -> InvoiceMatch | None:
    stmt = select(InvoiceMatch).where(
        InvoiceMatch.purchase_record_id == purchase_record_id,
        InvoiceMatch.status.in_([MATCH_STATUS_CONFIRMED, MATCH_STATUS_NEEDS_REVIEW]),
    )
    return session.exec(stmt).first()


def get_active_matches_for_invoice_file(
    session: Session,
    *,
    invoice_file_id: uuid.UUID,
) -> list[InvoiceMatch]:
    stmt = select(InvoiceMatch).where(
        InvoiceMatch.invoice_file_id == invoice_file_id,
        InvoiceMatch.status.in_([MATCH_STATUS_CONFIRMED, MATCH_STATUS_NEEDS_REVIEW]),
    )
    return list(session.exec(stmt).all())


def create_match(
    session: Session,
    *,
    owner_id: uuid.UUID,
    purchase_record_id: uuid.UUID,
    invoice_file_id: uuid.UUID,
    score: int,
    score_breakdown: dict | None = None,
    confirmed_by_id: uuid.UUID,
    status: str = MATCH_STATUS_CONFIRMED,
) -> InvoiceMatch:
    now = get_datetime_utc()
    match = InvoiceMatch(
        owner_id=owner_id,
        purchase_record_id=purchase_record_id,
        invoice_file_id=invoice_file_id,
        status=status,
        score=score,
        score_breakdown=score_breakdown or {},
        confirmed_by_id=confirmed_by_id,
        confirmed_at=now,
        created_at=now,
        updated_at=now,
    )
    session.add(match)
    session.commit()
    session.refresh(match)
    return match


def cancel_match(
    session: Session,
    *,
    match: InvoiceMatch,
    cancelled_by_id: uuid.UUID,
) -> InvoiceMatch:
    now = get_datetime_utc()
    match.status = MATCH_STATUS_CANCELLED
    match.cancelled_by_id = cancelled_by_id
    match.cancelled_at = now
    match.updated_at = now
    session.add(match)
    session.commit()
    session.refresh(match)
    return match


def reconfirm_match(
    session: Session,
    *,
    match: InvoiceMatch,
    confirmed_by_id: uuid.UUID,
    score: int | None = None,
    score_breakdown: dict | None = None,
) -> InvoiceMatch:
    now = get_datetime_utc()
    match.status = MATCH_STATUS_CONFIRMED
    match.confirmed_by_id = confirmed_by_id
    match.confirmed_at = now
    match.review_reason = None
    if score is not None:
        match.score = score
    if score_breakdown is not None:
        match.score_breakdown = score_breakdown
    match.updated_at = now
    session.add(match)
    session.commit()
    session.refresh(match)
    return match


def approve_match(
    session: Session,
    *,
    match: InvoiceMatch,
    approved_by_id: uuid.UUID,
) -> InvoiceMatch:
    now = get_datetime_utc()
    match.status = MATCH_STATUS_APPROVED
    match.approved_by_id = approved_by_id
    match.approved_at = now
    match.updated_at = now
    session.add(match)
    session.commit()
    session.refresh(match)
    return match


def unapprove_match(
    session: Session,
    *,
    match: InvoiceMatch,
) -> InvoiceMatch:
    now = get_datetime_utc()
    match.status = MATCH_STATUS_CONFIRMED
    match.approved_by_id = None
    match.approved_at = None
    match.updated_at = now
    session.add(match)
    session.commit()
    session.refresh(match)
    return match


def mark_needs_review(
    session: Session,
    *,
    match: InvoiceMatch,
    review_reason: str,
) -> InvoiceMatch:
    now = get_datetime_utc()
    match.status = MATCH_STATUS_NEEDS_REVIEW
    match.review_reason = review_reason
    match.updated_at = now
    session.add(match)
    session.commit()
    session.refresh(match)
    return match


def mark_matches_needing_review_for_purchase_record(
    session: Session,
    *,
    purchase_record_id: uuid.UUID,
    review_reason: str,
) -> int:
    stmt = select(InvoiceMatch).where(
        InvoiceMatch.purchase_record_id == purchase_record_id,
        InvoiceMatch.status.in_([MATCH_STATUS_CONFIRMED, MATCH_STATUS_NEEDS_REVIEW]),
    )
    count = 0
    for match in session.exec(stmt).all():
        # Skip approved matches — they are immutable
        if match.status == MATCH_STATUS_APPROVED:
            continue
        match.status = MATCH_STATUS_NEEDS_REVIEW
        match.review_reason = review_reason
        match.updated_at = get_datetime_utc()
        session.add(match)
        count += 1
    session.commit()
    return count


def mark_matches_needing_review_for_invoice_file(
    session: Session,
    *,
    invoice_file_id: uuid.UUID,
    review_reason: str,
) -> int:
    stmt = select(InvoiceMatch).where(
        InvoiceMatch.invoice_file_id == invoice_file_id,
        InvoiceMatch.status.in_([MATCH_STATUS_CONFIRMED, MATCH_STATUS_NEEDS_REVIEW]),
    )
    count = 0
    for match in session.exec(stmt).all():
        # Skip approved matches — they are immutable
        if match.status == MATCH_STATUS_APPROVED:
            continue
        match.status = MATCH_STATUS_NEEDS_REVIEW
        match.review_reason = review_reason
        match.updated_at = get_datetime_utc()
        session.add(match)
        count += 1
    session.commit()
    return count

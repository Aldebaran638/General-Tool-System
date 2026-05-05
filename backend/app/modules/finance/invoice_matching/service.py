"""Invoice Matching Service

Business logic layer for invoice matching.
"""

import uuid
from datetime import date
from decimal import Decimal

from fastapi import HTTPException
from sqlmodel import Session

from app.models_core import User

from ..invoice_files.constants import STATUS_CONFIRMED as INVOICE_STATUS_CONFIRMED
from ..invoice_files.models import InvoiceFile
from ..invoice_files.repository import get_record as get_invoice_file
from ..purchase_records.constants import (
    STATUS_APPROVED as PR_STATUS_APPROVED,
    STATUS_SUBMITTED as PR_STATUS_SUBMITTED,
)
from ..purchase_records.models import PurchaseRecord
from ..purchase_records.repository import get_record as get_purchase_record

from .constants import (
    AMOUNT_TOLERANCE,
    MATCH_STATUS_CANCELLED,
    MATCH_STATUS_CONFIRMED,
    MATCH_STATUS_NEEDS_REVIEW,
    MAX_DATE_DIFF_DAYS,
    SCORE_AMOUNT_MATCH,
    SCORE_CURRENCY_MATCH,
    SCORE_DATE_EXACT,
    SCORE_DATE_FAR,
    SCORE_DATE_NEAR,
    SCORE_KEYWORD_MATCH,
    SCORE_TEXT_SIMILARITY,
    SCORE_THRESHOLD_STRONG,
    SCORE_THRESHOLD_WEAK,
)
from .models import CandidateInvoice, InvoiceMatch
from . import repository

VALID_PR_STATUSES_FOR_MATCH = {PR_STATUS_SUBMITTED, PR_STATUS_APPROVED}
AMOUNT_TOLERANCE_DECIMAL = Decimal(str(AMOUNT_TOLERANCE))


# =============================================================================
# Access Control
# =============================================================================


def _require_owner_only(*, current_user: User, owner_id: uuid.UUID) -> None:
    """Owner-only write access. Superuser cannot bypass."""
    if current_user.id != owner_id:
        raise PermissionError("Not enough permissions")


def _require_read_access(*, current_user: User, owner_id: uuid.UUID) -> None:
    """Owner sees own; superuser sees all."""
    if not current_user.is_superuser and current_user.id != owner_id:
        raise PermissionError("Not enough permissions")


# =============================================================================
# Eligibility Helpers
# =============================================================================


def _date_diff_days(d1: date, d2: date) -> int:
    return abs((d1 - d2).days)


def _currencies_match(pr: PurchaseRecord, inv: InvoiceFile) -> bool:
    if not pr.currency or not inv.currency:
        return False
    return pr.currency.upper() == inv.currency.upper()


def _within_date_window(pr: PurchaseRecord, inv: InvoiceFile) -> bool:
    if pr.purchase_date is None or inv.invoice_date is None:
        return False
    return _date_diff_days(pr.purchase_date, inv.invoice_date) <= MAX_DATE_DIFF_DAYS


def _purchase_eligible_for_match(record: PurchaseRecord) -> bool:
    if record.deleted_at is not None:
        return False
    return record.status in VALID_PR_STATUSES_FOR_MATCH


def _invoice_eligible_for_match(invoice: InvoiceFile) -> bool:
    if invoice.deleted_at is not None:
        return False
    return invoice.status == INVOICE_STATUS_CONFIRMED


# =============================================================================
# Scoring
# =============================================================================


def _score_candidate(
    purchase: PurchaseRecord,
    invoice: InvoiceFile,
) -> tuple[int, dict]:
    score = 0
    breakdown: dict = {}

    if purchase.amount is not None and invoice.invoice_amount is not None:
        if abs(purchase.amount - invoice.invoice_amount) <= AMOUNT_TOLERANCE_DECIMAL:
            score += SCORE_AMOUNT_MATCH
            breakdown["amount"] = SCORE_AMOUNT_MATCH

    if _currencies_match(purchase, invoice):
        score += SCORE_CURRENCY_MATCH
        breakdown["currency"] = SCORE_CURRENCY_MATCH

    if purchase.purchase_date and invoice.invoice_date:
        diff = _date_diff_days(purchase.purchase_date, invoice.invoice_date)
        if diff == 0:
            score += SCORE_DATE_EXACT
            breakdown["date"] = SCORE_DATE_EXACT
        elif diff <= 3:
            score += SCORE_DATE_NEAR
            breakdown["date"] = SCORE_DATE_NEAR
        elif diff <= MAX_DATE_DIFF_DAYS:
            score += SCORE_DATE_FAR
            breakdown["date"] = SCORE_DATE_FAR

    pr_text = " ".join(
        filter(
            None,
            [
                purchase.order_name or "",
                purchase.category or "",
                purchase.subcategory or "",
            ],
        )
    ).lower()
    inv_text = " ".join(
        filter(
            None,
            [
                invoice.invoice_number or "",
                invoice.seller or "",
            ],
        )
    ).lower()
    if pr_text and inv_text:
        pr_words = set(pr_text.split())
        inv_words = set(inv_text.split())
        if pr_words & inv_words:
            score += SCORE_TEXT_SIMILARITY
            breakdown["text"] = SCORE_TEXT_SIMILARITY

    keywords: list[str] = []
    if purchase.note:
        keywords.extend(purchase.note.lower().split())
    if purchase.category:
        keywords.append(purchase.category.lower())
    if purchase.subcategory:
        keywords.append(purchase.subcategory.lower())
    if keywords and invoice.seller:
        seller_lower = invoice.seller.lower()
        if any(kw in seller_lower for kw in keywords):
            score += SCORE_KEYWORD_MATCH
            breakdown["keyword"] = SCORE_KEYWORD_MATCH

    return score, breakdown


def _get_level(score: int) -> str:
    if score >= SCORE_THRESHOLD_STRONG:
        return "strong"
    if score >= SCORE_THRESHOLD_WEAK:
        return "weak"
    return "low"


# =============================================================================
# Allocation
# =============================================================================


def get_allocated_for_invoice(
    session: Session,
    *,
    invoice_file_id: uuid.UUID,
    exclude_match_id: uuid.UUID | None = None,
) -> Decimal:
    """Sum the purchase_record.amount of all active matches for an invoice.

    Active = confirmed + needs_review. Optionally exclude one match
    (used by reconfirm to avoid double-counting itself).

    Public helper: cross-module callers (e.g. finance.dashboard) reuse this
    instead of duplicating the allocation rule. See Round 005 design.
    """
    matches = repository.get_active_matches_for_invoice_file(
        session, invoice_file_id=invoice_file_id
    )
    total = Decimal("0")
    for m in matches:
        if exclude_match_id is not None and m.id == exclude_match_id:
            continue
        pr = get_purchase_record(session, record_id=m.purchase_record_id)
        if pr and pr.amount is not None:
            total += pr.amount
    return total


# =============================================================================
# Serialization
# =============================================================================


def _serialize_match(
    match: InvoiceMatch,
    *,
    purchase: PurchaseRecord | None = None,
    invoice: InvoiceFile | None = None,
) -> dict:
    return {
        "id": match.id,
        "owner_id": match.owner_id,
        "purchase_record_id": match.purchase_record_id,
        "invoice_file_id": match.invoice_file_id,
        "purchase_record_name": purchase.order_name if purchase else None,
        "purchase_date": str(purchase.purchase_date) if purchase and purchase.purchase_date else None,
        "purchase_amount": str(purchase.amount) if purchase and purchase.amount else None,
        "invoice_file_number": invoice.invoice_number if invoice else None,
        "invoice_date": str(invoice.invoice_date) if invoice and invoice.invoice_date else None,
        "invoice_amount": str(invoice.invoice_amount) if invoice and invoice.invoice_amount else None,
        "seller": invoice.seller if invoice else None,
        "status": match.status,
        "score": match.score,
        "score_breakdown": match.score_breakdown,
        "review_reason": match.review_reason,
        "confirmed_by_id": match.confirmed_by_id,
        "confirmed_at": match.confirmed_at,
        "cancelled_by_id": match.cancelled_by_id,
        "cancelled_at": match.cancelled_at,
        "created_at": match.created_at,
        "updated_at": match.updated_at,
    }


# =============================================================================
# Read APIs
# =============================================================================


def read_summary(
    session: Session,
    *,
    current_user: User,
) -> dict:
    owner_id = None if current_user.is_superuser else current_user.id
    confirmed = repository.count_matches(
        session, owner_id=owner_id, status=MATCH_STATUS_CONFIRMED
    )
    cancelled = repository.count_matches(
        session, owner_id=owner_id, status=MATCH_STATUS_CANCELLED
    )
    needs_review = repository.count_matches(
        session, owner_id=owner_id, status=MATCH_STATUS_NEEDS_REVIEW
    )
    unmatched = list_unmatched_purchase_records(session, current_user=current_user)
    available = list_available_invoices(session, current_user=current_user)
    return {
        "total_confirmed": confirmed,
        "total_cancelled": cancelled,
        "total_needs_review": needs_review,
        "total_unmatched_purchase_records": len(unmatched),
        "total_available_invoices": len(available),
    }


def list_unmatched_purchase_records(
    session: Session,
    *,
    current_user: User,
    skip: int = 0,
    limit: int = 100,
) -> list[PurchaseRecord]:
    from ..purchase_records.repository import list_records

    owner_id = None if current_user.is_superuser else current_user.id
    records = list_records(session, owner_id=owner_id, skip=skip, limit=limit)
    unmatched: list[PurchaseRecord] = []
    for record in records:
        if not _purchase_eligible_for_match(record):
            continue
        active = repository.get_active_match_for_purchase_record(
            session, purchase_record_id=record.id
        )
        if active is None:
            unmatched.append(record)
    return unmatched


def list_available_invoices(
    session: Session,
    *,
    current_user: User,
    skip: int = 0,
    limit: int = 100,
) -> list[InvoiceFile]:
    from ..invoice_files.repository import list_records

    owner_id = None if current_user.is_superuser else current_user.id
    records = list_records(session, owner_id=owner_id, skip=skip, limit=limit)
    return [r for r in records if _invoice_eligible_for_match(r)]


def list_candidates(
    session: Session,
    *,
    current_user: User,
    purchase_record_id: uuid.UUID,
) -> list[CandidateInvoice]:
    purchase = get_purchase_record(session, record_id=purchase_record_id)
    if not purchase:
        raise ValueError("Purchase record not found")
    _require_read_access(current_user=current_user, owner_id=purchase.owner_id)
    if not _purchase_eligible_for_match(purchase):
        # Surface bad-callers (draft / rejected / deleted) as 400 instead of an
        # empty list, so the frontend can't accidentally render "no candidates"
        # for an obviously ineligible purchase.
        raise ValueError(
            "Purchase record is not eligible for matching "
            f"(status={purchase.status}, deleted={purchase.deleted_at is not None})"
        )

    invoices = list_available_invoices(session, current_user=current_user)
    candidates: list[CandidateInvoice] = []
    for inv in invoices:
        # Hard filters before scoring: same currency + within 7-day window.
        if not _currencies_match(purchase, inv):
            continue
        if not _within_date_window(purchase, inv):
            continue

        score, breakdown = _score_candidate(purchase, inv)
        if score < SCORE_THRESHOLD_WEAK:
            continue

        allocated = get_allocated_for_invoice(session, invoice_file_id=inv.id)
        remaining = (
            inv.invoice_amount - allocated if inv.invoice_amount else Decimal("0")
        )
        candidates.append(
            CandidateInvoice(
                invoice_file_id=inv.id,
                invoice_number=inv.invoice_number or "",
                invoice_date=str(inv.invoice_date) if inv.invoice_date else "",
                invoice_amount=str(inv.invoice_amount) if inv.invoice_amount else "0",
                currency=inv.currency or "",
                seller=inv.seller or "",
                allocated_amount=str(allocated),
                remaining_amount=str(remaining),
                score=score,
                score_breakdown=breakdown,
                level=_get_level(score),
            )
        )
    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates


def read_matches(
    session: Session,
    *,
    current_user: User,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    owner_id = None if current_user.is_superuser else current_user.id
    matches = repository.list_matches(
        session, owner_id=owner_id, status=status, skip=skip, limit=limit
    )
    result: list[dict] = []
    for m in matches:
        purchase = get_purchase_record(session, record_id=m.purchase_record_id)
        invoice = get_invoice_file(session, record_id=m.invoice_file_id)
        if purchase is not None and purchase.deleted_at is not None:
            continue
        if invoice is not None and invoice.deleted_at is not None:
            continue
        result.append(_serialize_match(m, purchase=purchase, invoice=invoice))
    return result


# =============================================================================
# Confirm / Cancel / Reconfirm
# =============================================================================


def _validate_pair_for_match(
    session: Session,
    *,
    purchase: PurchaseRecord,
    invoice: InvoiceFile,
    exclude_match_id: uuid.UUID | None = None,
) -> None:
    if invoice.owner_id != purchase.owner_id:
        raise ValueError("Invoice owner does not match purchase owner")
    if invoice.deleted_at is not None:
        raise ValueError("Invoice file is deleted")
    if invoice.status != INVOICE_STATUS_CONFIRMED:
        raise ValueError("Invoice is not confirmed")
    if purchase.deleted_at is not None:
        raise ValueError("Purchase record is deleted")
    if purchase.status not in VALID_PR_STATUSES_FOR_MATCH:
        raise ValueError("Purchase record is not eligible for matching")
    if not _currencies_match(purchase, invoice):
        raise ValueError("Currency mismatch between purchase and invoice")
    if not _within_date_window(purchase, invoice):
        raise ValueError("Date difference exceeds 7 days")
    if purchase.amount is None or invoice.invoice_amount is None:
        raise ValueError("Missing amount on purchase or invoice")

    allocated = get_allocated_for_invoice(
        session, invoice_file_id=invoice.id, exclude_match_id=exclude_match_id
    )
    if (allocated + purchase.amount) > (invoice.invoice_amount + AMOUNT_TOLERANCE_DECIMAL):
        raise ValueError("Invoice remaining amount is insufficient")


def confirm_match(
    session: Session,
    *,
    current_user: User,
    purchase_record_id: uuid.UUID,
    invoice_file_id: uuid.UUID,
) -> dict:
    purchase = get_purchase_record(session, record_id=purchase_record_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase record not found")
    _require_owner_only(current_user=current_user, owner_id=purchase.owner_id)

    existing = repository.get_active_match_for_purchase_record(
        session, purchase_record_id=purchase_record_id
    )
    if existing:
        raise ValueError("Purchase record already has an active match")

    invoice = get_invoice_file(session, record_id=invoice_file_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice file not found")

    _validate_pair_for_match(session, purchase=purchase, invoice=invoice)

    # Score and breakdown are always recomputed on the backend; never trust frontend.
    score, score_breakdown = _score_candidate(purchase, invoice)

    match = repository.create_match(
        session,
        owner_id=purchase.owner_id,
        purchase_record_id=purchase_record_id,
        invoice_file_id=invoice_file_id,
        score=score,
        score_breakdown=score_breakdown,
        confirmed_by_id=current_user.id,
    )
    return _serialize_match(match)


def cancel_match(
    session: Session,
    *,
    current_user: User,
    match_id: uuid.UUID,
) -> dict:
    match = repository.get_match(session, match_id=match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    _require_owner_only(current_user=current_user, owner_id=match.owner_id)
    if match.status == MATCH_STATUS_CANCELLED:
        raise ValueError("Match is already cancelled")
    updated = repository.cancel_match(
        session, match=match, cancelled_by_id=current_user.id
    )
    return _serialize_match(updated)


def reconfirm_match(
    session: Session,
    *,
    current_user: User,
    match_id: uuid.UUID,
) -> dict:
    match = repository.get_match(session, match_id=match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    _require_owner_only(current_user=current_user, owner_id=match.owner_id)
    if match.status != MATCH_STATUS_NEEDS_REVIEW:
        raise ValueError("Match must be in needs_review status to reconfirm")

    purchase = get_purchase_record(session, record_id=match.purchase_record_id)
    if not purchase:
        raise ValueError("Purchase record not found")
    invoice = get_invoice_file(session, record_id=match.invoice_file_id)
    if not invoice:
        raise ValueError("Invoice file not found")

    _validate_pair_for_match(
        session,
        purchase=purchase,
        invoice=invoice,
        exclude_match_id=match.id,
    )

    score, score_breakdown = _score_candidate(purchase, invoice)
    updated = repository.reconfirm_match(
        session,
        match=match,
        confirmed_by_id=current_user.id,
        score=score,
        score_breakdown=score_breakdown,
    )
    return _serialize_match(updated)


# =============================================================================
# Manual Search
# =============================================================================


def search_available_invoices(
    session: Session,
    *,
    current_user: User,
    purchase_record_id: uuid.UUID,
    search: str | None = None,
) -> list[dict]:
    """Search available invoices for manual matching.

    Filters by hard match rules (currency + date window) then by
    invoice_number prefix or seller substring.
    """
    purchase = get_purchase_record(session, record_id=purchase_record_id)
    if not purchase:
        raise ValueError("Purchase record not found")
    _require_read_access(current_user=current_user, owner_id=purchase.owner_id)
    if not _purchase_eligible_for_match(purchase):
        raise ValueError(
            "Purchase record is not eligible for matching "
            f"(status={purchase.status}, deleted={purchase.deleted_at is not None})"
        )

    invoices = list_available_invoices(session, current_user=current_user)
    result: list[dict] = []
    search_lower = search.strip().lower() if search else ""

    for inv in invoices:
        if not _currencies_match(purchase, inv):
            continue
        if not _within_date_window(purchase, inv):
            continue

        if search_lower:
            match_number = (inv.invoice_number or "").lower().startswith(search_lower)
            match_seller = search_lower in (inv.seller or "").lower()
            if not match_number and not match_seller:
                continue

        allocated = get_allocated_for_invoice(session, invoice_file_id=inv.id)
        remaining = (
            inv.invoice_amount - allocated if inv.invoice_amount else Decimal("0")
        )
        result.append(
            {
                "id": inv.id,
                "owner_id": inv.owner_id,
                "invoice_number": inv.invoice_number or "",
                "invoice_date": str(inv.invoice_date) if inv.invoice_date else "",
                "invoice_amount": str(inv.invoice_amount) if inv.invoice_amount else "0",
                "currency": inv.currency or "",
                "seller": inv.seller or "",
                "remaining_amount": str(remaining),
                "status": inv.status or "",
            }
        )

    return result


# =============================================================================
# Cross-Module Integration Hooks (called by purchase_records / invoice_files)
# =============================================================================


def mark_needs_review_for_purchase_record(
    session: Session,
    *,
    purchase_record_id: uuid.UUID,
    review_reason: str,
) -> int:
    return repository.mark_matches_needing_review_for_purchase_record(
        session,
        purchase_record_id=purchase_record_id,
        review_reason=review_reason,
    )


def mark_needs_review_for_invoice_file(
    session: Session,
    *,
    invoice_file_id: uuid.UUID,
    review_reason: str,
) -> int:
    return repository.mark_matches_needing_review_for_invoice_file(
        session,
        invoice_file_id=invoice_file_id,
        review_reason=review_reason,
    )

"""Finance Dashboard Service

Cross-module aggregation for the finance dashboard tool.

This module owns no tables and no business state. It composes counts and
pending items from purchase_records, invoice_files, and invoice_matching
modules. Allocation rules come from invoice_matching.service.get_allocated_for_invoice.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlmodel import Session

from app.models_core import User

from ..invoice_files.models import InvoiceFile
from ..invoice_matching.constants import (
    AMOUNT_TOLERANCE,
    MATCH_STATUS_CANCELLED,
    MATCH_STATUS_CONFIRMED,
    MATCH_STATUS_NEEDS_REVIEW,
)
from ..invoice_matching.models import InvoiceMatch
from ..invoice_matching.repository import (
    get_active_match_for_purchase_record,
)
from ..invoice_matching.service import get_allocated_for_invoice
from ..purchase_records.models import PurchaseRecord

from . import repository
from .constants import (
    PENDING_DEFAULT_LIMIT,
    PENDING_MAX_LIMIT,
    PENDING_TYPE_INVOICE_UNALLOCATED,
    PENDING_TYPE_MATCH_NEEDS_REVIEW,
    PENDING_TYPE_PURCHASE_UNMATCHED,
    PRIORITY_BY_TYPE,
    SCOPE_GLOBAL,
    SCOPE_SELF,
    SEVERITY_BY_TYPE,
)
from .schemas import (
    ByUserItem,
    ByUserList,
    DashboardSummary,
    InvoiceFileSummary,
    MatchSummary,
    PendingItem,
    PendingList,
    PurchaseRecordSummary,
)


AMOUNT_TOLERANCE_DECIMAL = Decimal(str(AMOUNT_TOLERANCE))


# =============================================================================
# Internal helpers
# =============================================================================


def _classify_invoice_allocation(
    session: Session, *, invoice: InvoiceFile
) -> str:
    """Bucket a confirmed invoice into unallocated / partially / fully.

    Returns one of the keys exposed in InvoiceFileSummary so the caller can
    increment the right counter directly.
    """
    if invoice.invoice_amount is None:
        # No invoice amount → treat as unallocated (matches design.md: allocated 0).
        return "unallocated"

    allocated = get_allocated_for_invoice(
        session, invoice_file_id=invoice.id
    )
    if allocated <= Decimal("0"):
        return "unallocated"
    if (invoice.invoice_amount - allocated) <= AMOUNT_TOLERANCE_DECIMAL:
        return "fully_allocated"
    return "partially_allocated"


def _purchase_has_active_match(
    session: Session, *, purchase_id: uuid.UUID
) -> bool:
    return (
        get_active_match_for_purchase_record(
            session, purchase_record_id=purchase_id
        )
        is not None
    )


def _scope_label(current_user: User) -> str:
    return SCOPE_SELF


def _scoped_owner_id(current_user: User) -> uuid.UUID | None:
    return current_user.id


# =============================================================================
# Summary
# =============================================================================


def _build_purchase_summary(
    session: Session, *, owner_id: uuid.UUID | None
) -> PurchaseRecordSummary:
    total = repository.count_purchase_records(
        session, owner_id=owner_id, deleted=False
    )
    deleted = repository.count_purchase_records(
        session, owner_id=owner_id, deleted=True
    )
    eligible = repository.list_eligible_purchase_records(
        session, owner_id=owner_id
    )
    matched = 0
    unmatched = 0
    for record in eligible:
        if _purchase_has_active_match(session, purchase_id=record.id):
            matched += 1
        else:
            unmatched += 1
    return PurchaseRecordSummary(
        total=total, unmatched=unmatched, matched=matched, deleted=deleted
    )


def _build_invoice_summary(
    session: Session, *, owner_id: uuid.UUID | None
) -> InvoiceFileSummary:
    total = repository.count_invoice_files(session, owner_id=owner_id)
    voided = repository.count_voided_invoices(session, owner_id=owner_id)
    confirmed_invoices = repository.list_confirmed_invoices(
        session, owner_id=owner_id
    )
    unallocated = 0
    partially = 0
    fully = 0
    for invoice in confirmed_invoices:
        bucket = _classify_invoice_allocation(session, invoice=invoice)
        if bucket == "unallocated":
            unallocated += 1
        elif bucket == "partially_allocated":
            partially += 1
        else:
            fully += 1
    return InvoiceFileSummary(
        total=total,
        unallocated=unallocated,
        partially_allocated=partially,
        fully_allocated=fully,
        voided=voided,
    )


def _build_match_summary(
    session: Session, *, owner_id: uuid.UUID | None
) -> MatchSummary:
    return MatchSummary(
        confirmed=repository.count_matches_by_status(
            session, owner_id=owner_id, status=MATCH_STATUS_CONFIRMED
        ),
        needs_review=repository.count_matches_by_status(
            session, owner_id=owner_id, status=MATCH_STATUS_NEEDS_REVIEW
        ),
        cancelled=repository.count_matches_by_status(
            session, owner_id=owner_id, status=MATCH_STATUS_CANCELLED
        ),
    )


def read_summary(
    session: Session, *, current_user: User
) -> DashboardSummary:
    owner_id = _scoped_owner_id(current_user)
    return DashboardSummary(
        scope=_scope_label(current_user),
        purchase_records=_build_purchase_summary(session, owner_id=owner_id),
        invoice_files=_build_invoice_summary(session, owner_id=owner_id),
        matches=_build_match_summary(session, owner_id=owner_id),
    )


# =============================================================================
# Pending list
# =============================================================================


def _format_datetime(dt: datetime | None) -> datetime | None:
    return dt


def _resolve_email(
    email_map: dict[uuid.UUID, str], owner_id: uuid.UUID
) -> str | None:
    return email_map.get(owner_id)


def _pending_from_purchase(
    record: PurchaseRecord, email_map: dict[uuid.UUID, str]
) -> PendingItem:
    return PendingItem(
        type=PENDING_TYPE_PURCHASE_UNMATCHED,
        severity=SEVERITY_BY_TYPE[PENDING_TYPE_PURCHASE_UNMATCHED],
        title="Purchase record not matched",
        description=(
            f"{record.order_name or 'Untitled purchase'} "
            f"({record.amount} {record.currency}) has no active invoice match."
        ),
        entity_type="purchase_record",
        entity_id=record.id,
        owner_id=record.owner_id,
        owner_email=_resolve_email(email_map, record.owner_id),
        business_date=record.purchase_date,
        created_at=_format_datetime(record.created_at),
    )


def _pending_from_invoice(
    invoice: InvoiceFile, email_map: dict[uuid.UUID, str]
) -> PendingItem:
    return PendingItem(
        type=PENDING_TYPE_INVOICE_UNALLOCATED,
        severity=SEVERITY_BY_TYPE[PENDING_TYPE_INVOICE_UNALLOCATED],
        title="Invoice not allocated",
        description=(
            f"Invoice {invoice.invoice_number or invoice.id} "
            f"({invoice.invoice_amount} {invoice.currency}) "
            "has no purchase record matched."
        ),
        entity_type="invoice_file",
        entity_id=invoice.id,
        owner_id=invoice.owner_id,
        owner_email=_resolve_email(email_map, invoice.owner_id),
        business_date=invoice.invoice_date,
        created_at=_format_datetime(invoice.created_at),
    )


def _pending_from_match(
    match: InvoiceMatch, email_map: dict[uuid.UUID, str]
) -> PendingItem:
    return PendingItem(
        type=PENDING_TYPE_MATCH_NEEDS_REVIEW,
        severity=SEVERITY_BY_TYPE[PENDING_TYPE_MATCH_NEEDS_REVIEW],
        title="Match needs review",
        description=match.review_reason or "Match needs review",
        entity_type="invoice_match",
        entity_id=match.id,
        owner_id=match.owner_id,
        owner_email=_resolve_email(email_map, match.owner_id),
        business_date=None,
        created_at=_format_datetime(match.updated_at or match.created_at),
    )


def _sort_key(item: PendingItem) -> tuple:
    # Higher priority first (so negate); then oldest first within same type.
    priority = PRIORITY_BY_TYPE.get(item.type, 0)
    created = item.created_at or datetime.min
    return (-priority, created)


def list_pending(
    session: Session,
    *,
    current_user: User,
    limit: int = PENDING_DEFAULT_LIMIT,
) -> PendingList:
    if limit <= 0:
        raise HTTPException(status_code=422, detail="limit must be positive")
    effective_limit = min(limit, PENDING_MAX_LIMIT)

    owner_id = _scoped_owner_id(current_user)

    eligible_purchases = repository.list_eligible_purchase_records(
        session, owner_id=owner_id
    )
    unmatched_purchases = [
        p
        for p in eligible_purchases
        if not _purchase_has_active_match(session, purchase_id=p.id)
    ]

    confirmed_invoices = repository.list_confirmed_invoices(
        session, owner_id=owner_id
    )
    unallocated_invoices = [
        inv
        for inv in confirmed_invoices
        if _classify_invoice_allocation(session, invoice=inv) == "unallocated"
    ]

    needs_review_matches = repository.list_needs_review_matches(
        session, owner_id=owner_id
    )

    owner_ids = {p.owner_id for p in unmatched_purchases}
    owner_ids.update(inv.owner_id for inv in unallocated_invoices)
    owner_ids.update(m.owner_id for m in needs_review_matches)
    email_map = repository.get_user_email_map(
        session, owner_ids=list(owner_ids)
    ) if current_user.is_superuser else {current_user.id: current_user.email}

    items: list[PendingItem] = []
    items.extend(_pending_from_purchase(p, email_map) for p in unmatched_purchases)
    items.extend(_pending_from_invoice(inv, email_map) for inv in unallocated_invoices)
    items.extend(_pending_from_match(m, email_map) for m in needs_review_matches)

    items.sort(key=_sort_key)
    truncated = items[:effective_limit]
    return PendingList(data=truncated, count=len(truncated))


# =============================================================================
# By-user (admin only)
# =============================================================================


def list_by_user(
    session: Session, *, current_user: User
) -> ByUserList:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    users = repository.list_active_users(session)
    rows: list[ByUserItem] = []
    for user in users:
        eligible = repository.list_eligible_purchase_records(
            session, owner_id=user.id
        )
        pr_unmatched = sum(
            1
            for p in eligible
            if not _purchase_has_active_match(session, purchase_id=p.id)
        )

        confirmed_invoices = repository.list_confirmed_invoices(
            session, owner_id=user.id
        )
        inv_unallocated = sum(
            1
            for inv in confirmed_invoices
            if _classify_invoice_allocation(session, invoice=inv)
            == "unallocated"
        )

        match_needs_review = repository.count_matches_by_status(
            session, owner_id=user.id, status=MATCH_STATUS_NEEDS_REVIEW
        )

        total = pr_unmatched + inv_unallocated + match_needs_review
        if total == 0:
            # Skip users that have nothing pending. The admin view should
            # focus attention on users that need action.
            continue
        rows.append(
            ByUserItem(
                owner_id=user.id,
                owner_email=user.email,
                purchase_record_unmatched=pr_unmatched,
                invoice_file_unallocated=inv_unallocated,
                match_needs_review=match_needs_review,
                total_pending=total,
            )
        )

    rows.sort(key=lambda r: (-r.total_pending, r.owner_email))
    return ByUserList(data=rows, count=len(rows))

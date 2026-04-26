"""Finance Dashboard Repository

Read-only persistence helpers for cross-module aggregation. All counts are
expressed as SQL queries so that we don't load full row payloads into memory.

This module owns no tables; every helper here joins data from purchase_records,
invoice_files, and invoice_match.
"""

import uuid

from sqlmodel import Session, func, select

from app.models_core import User

from ..invoice_files.constants import (
    STATUS_CONFIRMED as INV_STATUS_CONFIRMED,
    STATUS_VOIDED as INV_STATUS_VOIDED,
)
from ..invoice_files.models import InvoiceFile
from ..invoice_matching.constants import (
    MATCH_STATUS_CONFIRMED,
    MATCH_STATUS_NEEDS_REVIEW,
)
from ..invoice_matching.models import InvoiceMatch
from ..purchase_records.constants import (
    STATUS_APPROVED as PR_STATUS_APPROVED,
    STATUS_SUBMITTED as PR_STATUS_SUBMITTED,
)
from ..purchase_records.models import PurchaseRecord


PR_ELIGIBLE_STATUSES = (PR_STATUS_SUBMITTED, PR_STATUS_APPROVED)
ACTIVE_MATCH_STATUSES = (MATCH_STATUS_CONFIRMED, MATCH_STATUS_NEEDS_REVIEW)


# =============================================================================
# Purchase Record Counts
# =============================================================================


def count_purchase_records(
    session: Session,
    *,
    owner_id: uuid.UUID | None = None,
    deleted: bool = False,
) -> int:
    """Count non-deleted (or deleted) purchase records, optionally scoped to one owner."""
    stmt = select(func.count()).select_from(PurchaseRecord)
    if deleted:
        stmt = stmt.where(PurchaseRecord.deleted_at.isnot(None))
    else:
        stmt = stmt.where(PurchaseRecord.deleted_at.is_(None))
    if owner_id is not None:
        stmt = stmt.where(PurchaseRecord.owner_id == owner_id)
    return session.exec(stmt).one()


def list_eligible_purchase_records(
    session: Session,
    *,
    owner_id: uuid.UUID | None = None,
) -> list[PurchaseRecord]:
    """Return non-deleted purchases whose status is submitted/approved.

    These are the records that *could* hold an active match. The dashboard
    uses this set to compute matched / unmatched counts.
    """
    stmt = (
        select(PurchaseRecord)
        .where(PurchaseRecord.deleted_at.is_(None))
        .where(PurchaseRecord.status.in_(PR_ELIGIBLE_STATUSES))
    )
    if owner_id is not None:
        stmt = stmt.where(PurchaseRecord.owner_id == owner_id)
    return list(session.exec(stmt).all())


# =============================================================================
# Invoice File Counts
# =============================================================================


def count_invoice_files(
    session: Session,
    *,
    owner_id: uuid.UUID | None = None,
    status: str | None = None,
) -> int:
    """Count non-deleted invoices, optionally filtered by status / owner."""
    stmt = select(func.count()).select_from(InvoiceFile).where(
        InvoiceFile.deleted_at.is_(None)
    )
    if owner_id is not None:
        stmt = stmt.where(InvoiceFile.owner_id == owner_id)
    if status is not None:
        stmt = stmt.where(InvoiceFile.status == status)
    return session.exec(stmt).one()


def list_confirmed_invoices(
    session: Session,
    *,
    owner_id: uuid.UUID | None = None,
) -> list[InvoiceFile]:
    """All non-deleted, confirmed invoices.

    Voided / draft invoices are excluded — the dashboard only allocates
    confirmed invoices.
    """
    stmt = (
        select(InvoiceFile)
        .where(InvoiceFile.deleted_at.is_(None))
        .where(InvoiceFile.status == INV_STATUS_CONFIRMED)
    )
    if owner_id is not None:
        stmt = stmt.where(InvoiceFile.owner_id == owner_id)
    return list(session.exec(stmt).all())


def count_voided_invoices(
    session: Session,
    *,
    owner_id: uuid.UUID | None = None,
) -> int:
    """Voided invoices that are not soft-deleted."""
    return count_invoice_files(
        session, owner_id=owner_id, status=INV_STATUS_VOIDED
    )


# =============================================================================
# Match Counts
# =============================================================================


def count_matches_by_status(
    session: Session,
    *,
    owner_id: uuid.UUID | None = None,
    status: str,
) -> int:
    stmt = select(func.count()).select_from(InvoiceMatch).where(
        InvoiceMatch.status == status
    )
    if owner_id is not None:
        stmt = stmt.where(InvoiceMatch.owner_id == owner_id)
    return session.exec(stmt).one()


def list_needs_review_matches(
    session: Session,
    *,
    owner_id: uuid.UUID | None = None,
) -> list[InvoiceMatch]:
    stmt = select(InvoiceMatch).where(
        InvoiceMatch.status == MATCH_STATUS_NEEDS_REVIEW
    )
    if owner_id is not None:
        stmt = stmt.where(InvoiceMatch.owner_id == owner_id)
    return list(session.exec(stmt).all())


# =============================================================================
# User Lookups
# =============================================================================


def list_active_users(session: Session) -> list[User]:
    """All active users — used by admin by-user aggregation."""
    stmt = select(User).where(User.is_active.is_(True))
    return list(session.exec(stmt).all())


def get_user_email_map(
    session: Session, *, owner_ids: list[uuid.UUID]
) -> dict[uuid.UUID, str]:
    """Bulk-fetch email by id for the given owner_ids."""
    if not owner_ids:
        return {}
    # SQLModel/SQLAlchemy can't bind an empty `IN` cleanly, so we guarded above.
    stmt = select(User.id, User.email).where(User.id.in_(owner_ids))
    return {row[0]: row[1] for row in session.exec(stmt).all()}

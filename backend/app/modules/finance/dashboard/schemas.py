"""Finance Dashboard Schemas

Pydantic / SQLModel response models for the finance dashboard tool.
This module owns no database tables — everything here is read-only aggregation.
"""

import uuid
from datetime import date, datetime

from sqlmodel import SQLModel


# =============================================================================
# Summary
# =============================================================================


class PurchaseRecordSummary(SQLModel):
    total: int
    unmatched: int
    matched: int
    deleted: int


class InvoiceFileSummary(SQLModel):
    total: int
    unallocated: int
    partially_allocated: int
    fully_allocated: int
    voided: int


class MatchSummary(SQLModel):
    confirmed: int
    needs_review: int
    cancelled: int


class DashboardSummary(SQLModel):
    scope: str
    purchase_records: PurchaseRecordSummary
    invoice_files: InvoiceFileSummary
    matches: MatchSummary


# =============================================================================
# Pending
# =============================================================================


class PendingItem(SQLModel):
    type: str
    severity: str
    title: str
    description: str
    entity_type: str
    entity_id: uuid.UUID
    owner_id: uuid.UUID
    owner_email: str | None = None
    business_date: date | None = None
    created_at: datetime | None = None


class PendingList(SQLModel):
    data: list[PendingItem]
    count: int


# =============================================================================
# By-User
# =============================================================================


class ByUserItem(SQLModel):
    owner_id: uuid.UUID
    owner_email: str
    purchase_record_unmatched: int
    invoice_file_unallocated: int
    match_needs_review: int
    total_pending: int


class ByUserList(SQLModel):
    data: list[ByUserItem]
    count: int

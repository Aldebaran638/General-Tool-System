"""
Reimbursement Exports Schemas

Re-exports models used as schemas for transport layer.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlmodel import Field, SQLModel

from app.models_core import Message

from .constants import (
    DEFAULT_RETENTION_DAYS,
    MAX_RETENTION_DAYS,
    MIN_RETENTION_DAYS,
)


# =============================================================================
# Output / View Models
# =============================================================================

class ReimbursementExportItemPublic(SQLModel):
    id: uuid.UUID
    export_id: uuid.UUID
    purchase_record_id: uuid.UUID
    invoice_file_id: uuid.UUID | None
    invoice_match_id: uuid.UUID | None
    document_number: int
    purchase_date: date
    amount: Decimal
    currency: str
    category: str
    subcategory: str | None
    order_name: str
    remark: str | None
    description_snapshot: str | None
    department_snapshot: str | None
    created_at: datetime


class ReimbursementExportPublic(SQLModel):
    id: uuid.UUID
    created_by_id: uuid.UUID
    created_at: datetime
    department: str | None
    business_unit: str | None
    reimburser: str | None
    reimbursement_date: date | None
    currency: str | None
    total_amount: Decimal
    item_count: int
    original_filename: str | None
    stored_filename: str | None
    file_path: str | None
    mime_type: str | None
    file_size: int | None
    file_expires_at: datetime | None
    file_deleted_at: datetime | None


class ReimbursementExportDetailPublic(SQLModel):
    id: uuid.UUID
    created_by_id: uuid.UUID
    created_at: datetime
    department: str | None
    business_unit: str | None
    reimburser: str | None
    reimbursement_date: date | None
    currency: str | None
    total_amount: Decimal
    item_count: int
    original_filename: str | None
    stored_filename: str | None
    file_path: str | None
    mime_type: str | None
    file_size: int | None
    file_expires_at: datetime | None
    file_deleted_at: datetime | None
    items: list[ReimbursementExportItemPublic]


class ReimbursementExportsPublic(SQLModel):
    data: list[ReimbursementExportPublic]
    count: int


# =============================================================================
# Record with export metadata
# =============================================================================

class InvoiceFileBriefPublic(SQLModel):
    id: uuid.UUID
    invoice_number: str
    invoice_date: date
    invoice_amount: Decimal
    currency: str
    seller: str


class PurchaseRecordWithExportInfo(SQLModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    purchase_date: date
    amount: Decimal
    currency: str
    order_name: str
    category: str
    subcategory: str | None
    note: str | None
    status: str
    created_at: datetime | None
    invoice_file: InvoiceFileBriefPublic | None
    exported: bool
    latest_exported_at: datetime | None
    latest_exported_by: uuid.UUID | None


class RecordsPublic(SQLModel):
    data: list[PurchaseRecordWithExportInfo]
    count: int


# =============================================================================
# Query / Filter Models
# =============================================================================

class RecordsFilter(SQLModel):
    start_date: date | None = None
    end_date: date | None = None
    category: str | None = None
    subcategory: str | None = None
    currency: str | None = None
    owner_id: uuid.UUID | None = None
    exported: str | None = None  # all / exported / not_exported
    q: str | None = None


# =============================================================================
# Request Models
# =============================================================================

class GenerateRequest(SQLModel):
    purchase_record_ids: list[uuid.UUID] = Field(default_factory=list)
    department: str | None = Field(default=None, max_length=255)
    business_unit: str | None = Field(default=None, max_length=255)
    reimburser: str | None = Field(default=None, max_length=255)
    reimbursement_date: date | None = None
    retention_days: int = Field(
        default=DEFAULT_RETENTION_DAYS,
        ge=MIN_RETENTION_DAYS,
        le=MAX_RETENTION_DAYS,
    )


# =============================================================================
# Settings Models
# =============================================================================

class SettingsResponse(SQLModel):
    retention_days: int


class SettingsUpdate(SQLModel):
    retention_days: int | None = Field(
        default=None,
        ge=MIN_RETENTION_DAYS,
        le=MAX_RETENTION_DAYS,
    )

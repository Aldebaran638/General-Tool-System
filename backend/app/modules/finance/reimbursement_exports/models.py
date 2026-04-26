"""
Reimbursement Exports Module Models

SQLModel definitions for the reimbursement_exports tool module.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric
from sqlmodel import Field, SQLModel

from app.models_core import get_datetime_utc


# =============================================================================
# Reimbursement Export
# =============================================================================

class ReimbursementExport(SQLModel, table=True):
    """Database model for reimbursement export history."""

    __tablename__ = "reimbursement_export"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_by_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    # Header fields
    department: str | None = Field(default=None, max_length=255)
    business_unit: str | None = Field(default=None, max_length=255)
    reimburser: str | None = Field(default=None, max_length=255)
    reimbursement_date: date | None = None

    # Aggregate info
    currency: str | None = Field(default=None, max_length=3)
    total_amount: Decimal = Field(default=Decimal("0.00"), sa_type=Numeric(precision=15, scale=2))
    item_count: int = Field(default=0)

    # File info
    original_filename: str | None = Field(default=None, max_length=255)
    stored_filename: str | None = Field(default=None, max_length=255)
    file_path: str | None = Field(default=None, max_length=512)
    mime_type: str | None = Field(default=None, max_length=128)
    file_size: int | None = Field(default=None)
    file_expires_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    file_deleted_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


# =============================================================================
# Reimbursement Export Item
# =============================================================================

class ReimbursementExportItem(SQLModel, table=True):
    """Database model for export item snapshots."""

    __tablename__ = "reimbursement_export_item"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    export_id: uuid.UUID = Field(
        foreign_key="reimbursement_export.id",
        nullable=False,
        ondelete="CASCADE",
    )
    purchase_record_id: uuid.UUID = Field(
        foreign_key="purchase_record.id",
        nullable=False,
    )
    invoice_file_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="invoice_file.id",
        nullable=True,
    )
    invoice_match_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="invoice_match.id",
        nullable=True,
    )

    document_number: int
    purchase_date: date
    amount: Decimal = Field(sa_type=Numeric(precision=15, scale=2))
    currency: str = Field(max_length=3)
    category: str = Field(max_length=64)
    subcategory: str | None = Field(default=None, max_length=64)
    order_name: str = Field(max_length=255)
    remark: str | None = Field(default=None, max_length=1024)
    description_snapshot: str | None = Field(default=None, max_length=1024)
    department_snapshot: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

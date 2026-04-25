"""
Invoice Files Module Models

SQLModel definitions for the invoice_files tool module.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric
from sqlmodel import Field, SQLModel

from app.models_core import get_datetime_utc

from .constants import STATUS_DRAFT, VALID_CURRENCIES, VALID_INVOICE_TYPES


# =============================================================================
# Base / Shared Schema
# =============================================================================

class InvoiceFileBase(SQLModel):
    invoice_number: str = Field(min_length=1, max_length=128)
    invoice_date: date
    invoice_amount: Decimal = Field(sa_type=Numeric(precision=15, scale=2))
    tax_amount: Decimal = Field(default=Decimal("0.00"), sa_type=Numeric(precision=15, scale=2))
    currency: str = Field(min_length=3, max_length=3)
    buyer: str = Field(min_length=1, max_length=255)
    seller: str = Field(min_length=1, max_length=255)
    invoice_type: str = Field(min_length=1, max_length=64)
    note: str | None = Field(default=None, max_length=1024)


# =============================================================================
# Create / Update DTOs
# =============================================================================

class InvoiceFileCreate(InvoiceFileBase):
    pass


class InvoiceFileUpdate(SQLModel):
    invoice_number: str | None = Field(default=None, min_length=1, max_length=128)
    invoice_date: date | None = None
    invoice_amount: Decimal | None = Field(default=None, sa_type=Numeric(precision=15, scale=2))
    tax_amount: Decimal | None = Field(default=None, sa_type=Numeric(precision=15, scale=2))
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    buyer: str | None = Field(default=None, min_length=1, max_length=255)
    seller: str | None = Field(default=None, min_length=1, max_length=255)
    invoice_type: str | None = Field(default=None, min_length=1, max_length=64)
    note: str | None = Field(default=None, max_length=1024)


# =============================================================================
# Database Model
# =============================================================================

class InvoiceFile(InvoiceFileBase, table=True):
    """Database model for invoice files."""

    __tablename__ = "invoice_file"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    status: str = Field(default=STATUS_DRAFT, max_length=32)

    # PDF metadata (file itself is stored on disk)
    pdf_path: str = Field(max_length=512)
    pdf_original_name: str = Field(max_length=255)
    pdf_mime_type: str = Field(max_length=128)
    pdf_size: int

    # Soft delete
    deleted_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    deleted_by_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user.id",
        nullable=True,
    )

    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


# =============================================================================
# Output / View Models
# =============================================================================

class InvoiceFilePublic(InvoiceFileBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    status: str
    pdf_path: str
    pdf_original_name: str
    pdf_mime_type: str
    pdf_size: int
    deleted_at: datetime | None
    deleted_by_id: uuid.UUID | None
    created_at: datetime | None
    updated_at: datetime | None
    # Admin-only duplicate hint
    duplicate_warning: str | None = None
    duplicate_invoice_owner_count: int | None = None


class InvoiceFilesPublic(SQLModel):
    data: list[InvoiceFilePublic]
    count: int


# =============================================================================
# Parse Preview Response
# =============================================================================

class ParsePreviewResponse(SQLModel):
    invoice_number: str | None = None
    invoice_date: str | None = None
    invoice_amount: str | None = None
    tax_amount: str | None = None
    currency: str | None = None
    buyer: str | None = None
    seller: str | None = None
    invoice_type: str | None = None
    note: str | None = None

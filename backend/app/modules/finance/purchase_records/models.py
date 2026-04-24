"""
Purchase Records Module Models

SQLModel definitions for the purchase_records tool module.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric
from sqlmodel import Field, SQLModel

from app.models_core import get_datetime_utc

from .constants import (
    INVOICE_UNMATCHED,
    STATUS_DRAFT,
    VALID_CATEGORIES,
    VALID_CURRENCIES,
    VALID_INVOICE_MATCH_STATUSES,
    VALID_STATUSES,
    VALID_SUBCATEGORIES,
)


# =============================================================================
# Base / Shared Schema
# =============================================================================

class PurchaseRecordBase(SQLModel):
    purchase_date: date
    amount: Decimal = Field(sa_type=Numeric(precision=15, scale=2))
    currency: str = Field(min_length=3, max_length=3)
    order_name: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=64)
    subcategory: str | None = Field(default=None, max_length=64)
    note: str | None = Field(default=None, max_length=1024)


# =============================================================================
# Create / Update DTOs
# =============================================================================

class PurchaseRecordCreate(PurchaseRecordBase):
    pass


class PurchaseRecordUpdate(SQLModel):
    purchase_date: date | None = None
    amount: Decimal | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    order_name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, min_length=1, max_length=64)
    subcategory: str | None = Field(default=None, max_length=64)
    note: str | None = Field(default=None, max_length=1024)


# =============================================================================
# Database Model
# =============================================================================

class PurchaseRecord(PurchaseRecordBase, table=True):
    """Database model for purchase records."""

    __tablename__ = "purchase_record"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    status: str = Field(default=STATUS_DRAFT, max_length=32)
    invoice_match_status: str = Field(default=INVOICE_UNMATCHED, max_length=32)

    # Screenshot metadata (file itself is stored on disk)
    screenshot_path: str = Field(max_length=512)
    screenshot_original_name: str = Field(max_length=255)
    screenshot_mime_type: str = Field(max_length=128)
    screenshot_size: int

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

class PurchaseRecordPublic(PurchaseRecordBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    status: str
    invoice_match_status: str
    screenshot_path: str
    screenshot_original_name: str
    screenshot_mime_type: str
    screenshot_size: int
    deleted_at: datetime | None
    deleted_by_id: uuid.UUID | None
    created_at: datetime | None
    updated_at: datetime | None


class PurchaseRecordsPublic(SQLModel):
    data: list[PurchaseRecordPublic]
    count: int


# =============================================================================
# OCR Preview Response
# =============================================================================

class OCRPreviewResponse(SQLModel):
    purchase_date: str | None = None
    amount: str | None = None
    currency: str | None = None
    order_name: str | None = None
    category: str | None = None
    subcategory: str | None = None
    note: str | None = None

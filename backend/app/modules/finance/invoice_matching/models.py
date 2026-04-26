"""
Invoice Matching Module Models

SQLModel definitions for the invoice_matching tool module.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, JSON
from sqlmodel import Field, SQLModel

from app.models_core import get_datetime_utc

from .constants import MATCH_STATUS_CONFIRMED


# =============================================================================
# Base / Shared Schema
# =============================================================================

class InvoiceMatchBase(SQLModel):
    status: str = Field(default=MATCH_STATUS_CONFIRMED, max_length=32)
    score: int = Field(default=0)
    score_breakdown: dict = Field(default_factory=dict, sa_type=JSON)
    review_reason: str | None = Field(default=None, max_length=255)


# =============================================================================
# Create / Update DTOs
# =============================================================================

class InvoiceMatchCreate(InvoiceMatchBase):
    purchase_record_id: uuid.UUID
    invoice_file_id: uuid.UUID


class InvoiceMatchUpdate(SQLModel):
    status: str | None = Field(default=None, max_length=32)
    review_reason: str | None = Field(default=None, max_length=255)


# =============================================================================
# Database Model
# =============================================================================

class InvoiceMatch(InvoiceMatchBase, table=True):
    """Database model for invoice matches."""

    __tablename__ = "invoice_match"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    purchase_record_id: uuid.UUID = Field(
        foreign_key="purchase_record.id", nullable=False, ondelete="CASCADE"
    )
    invoice_file_id: uuid.UUID = Field(
        foreign_key="invoice_file.id", nullable=False, ondelete="CASCADE"
    )

    confirmed_by_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user.id",
        nullable=True,
    )
    confirmed_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    cancelled_by_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user.id",
        nullable=True,
    )
    cancelled_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
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

class InvoiceMatchPublic(InvoiceMatchBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    purchase_record_id: uuid.UUID
    invoice_file_id: uuid.UUID
    confirmed_by_id: uuid.UUID | None
    confirmed_at: datetime | None
    cancelled_by_id: uuid.UUID | None
    cancelled_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None


class InvoiceMatchesPublic(SQLModel):
    data: list[InvoiceMatchPublic]
    count: int


# =============================================================================
# Candidate View Model
# =============================================================================

class CandidateInvoice(SQLModel):
    invoice_file_id: uuid.UUID
    invoice_number: str
    invoice_date: str
    invoice_amount: str
    currency: str
    seller: str
    allocated_amount: str
    remaining_amount: str
    score: int
    score_breakdown: dict
    level: str

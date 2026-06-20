"""
Equipment Purchase Contract Filler Module Models

SQLModel definitions for the equipment_purchase_filler tool module.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel

from app.models_core import get_datetime_utc


class EquipmentPurchaseFilledVersionBase(SQLModel):
    version_name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1024)


class EquipmentPurchaseFilledVersionCreate(EquipmentPurchaseFilledVersionBase):
    field_values: dict[str, str]
    equipment_items: list[dict[str, str]] | None = None


class EquipmentPurchaseFilledVersionUpdate(SQLModel):
    version_name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1024)
    field_values: dict[str, str] | None = None
    equipment_items: list[dict[str, str]] | None = None


class EquipmentPurchaseFilledVersion(EquipmentPurchaseFilledVersionBase, table=True):
    """Database model for a saved equipment purchase contract fill version."""

    __tablename__ = "equipment_purchase_filled_version"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_by_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE",
    )

    # Filled values as JSON string
    field_values: str = Field(max_length=65535)

    # Equipment table rows as JSON string
    equipment_items: str | None = Field(default=None, max_length=65535)

    # Generated output file metadata
    output_filename: str | None = Field(default=None, max_length=255)
    output_file_path: str | None = Field(default=None, max_length=512)
    output_file_size: int | None = Field(default=None)

    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class EquipmentPurchaseFilledVersionPublic(EquipmentPurchaseFilledVersionBase):
    id: uuid.UUID
    created_by_id: uuid.UUID
    field_values: dict[str, str]
    equipment_items: list[dict[str, str]] | None
    output_filename: str | None
    output_file_path: str | None
    output_file_size: int | None
    created_at: datetime | None
    updated_at: datetime | None


class EquipmentPurchaseFilledVersionsPublic(SQLModel):
    data: list[EquipmentPurchaseFilledVersionPublic]
    count: int

"""
Project Management Module Models

These models belong to the project_management tool module.
They are registered with the module registry and imported by the core
compatibility layer in app/models.py.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.models_core import get_datetime_utc


# =============================================================================
# Item Models (Project Management)
# =============================================================================

class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


class Item(ItemBase, table=True):
    """Database model for project items."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    # Use string reference to avoid circular import with User model
    # Note: back_populates is not used because User is in models_core
    # and we want to avoid cross-module relationship configuration issues.
    # Database-level cascade is handled by the foreign_key ondelete="CASCADE".
    owner: "User" = Relationship(  # type: ignore
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    amount: float | None = None
    test_amount: float | None = None


class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int

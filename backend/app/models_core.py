"""
Core Models

These models are shared across the entire application and belong to the platform layer.
Tool modules MUST NOT modify these models. They can import and reference them.

New tool models should be defined in:
    app/modules/<group>/<tool>/models.py

And registered via:
    from app.modules.registry import register_module
    register_module(..., models=[YourModel])
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# =============================================================================
# User Models
# =============================================================================

class UserBase(SQLModel):
    wecom_userid: str = Field(unique=True, index=True, max_length=64)
    mobile: str | None = Field(default=None, unique=True, index=True, max_length=32)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str = Field(min_length=1, max_length=128)


class UserRegister(SQLModel):
    wecom_userid: str = Field(max_length=64)
    password: str = Field(min_length=1, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    mobile: str | None = Field(default=None, max_length=32)


class UserUpdate(SQLModel):
    wecom_userid: str | None = Field(default=None, max_length=64)
    mobile: str | None = Field(default=None, max_length=32)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = Field(default=None)
    is_superuser: bool | None = Field(default=None)
    password: str | None = Field(default=None, min_length=1, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    mobile: str | None = Field(default=None, max_length=32)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=1, max_length=128)


# Database model - this stays in core because authentication is platform-level
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    # Relationship to items is defined via back_populates in the Item model


class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# =============================================================================
# Auth Models
# =============================================================================

class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=1, max_length=128)


# =============================================================================
# Common Response Models
# =============================================================================

class Message(SQLModel):
    message: str


# =============================================================================
# WeCom Models
# =============================================================================

class WecomConfig(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    corp_id: str = Field(max_length=64)
    agent_id: str = Field(max_length=64)
    secret_encrypted: str = Field(max_length=255)
    trusted_domain: str | None = Field(default=None, max_length=255)
    access_token: str | None = Field(default=None, max_length=512)
    access_token_expire_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    created_at: datetime | None = Field(default_factory=get_datetime_utc, sa_type=DateTime(timezone=True))
    updated_at: datetime | None = Field(default_factory=get_datetime_utc, sa_type=DateTime(timezone=True))


class SystemUserRole(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    userid: str = Field(index=True, max_length=64)
    role_code: str = Field(max_length=64)
    created_by: str | None = Field(default=None, max_length=64)
    created_at: datetime | None = Field(default_factory=get_datetime_utc, sa_type=DateTime(timezone=True))
    updated_at: datetime | None = Field(default_factory=get_datetime_utc, sa_type=DateTime(timezone=True))

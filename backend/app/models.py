"""
App Models (Compatibility Layer)

⚠️  IMPORTANT: This file is a LEGACY COMPATIBILITY LAYER.

New code should import from:
    - app.models_core          for platform models (User, Token, etc.)
    - app.modules.xxx.models   for tool-specific models (Item, etc.)

================================================================================
MIGRATION NOTICE:

Item models have been moved to the project_management module:
    from app.modules.workbench.project_management.models import Item, ItemCreate, ...

This file will be removed in a future major version once all legacy code is migrated.
================================================================================
"""

# Re-export core models only
from app.models_core import (
    Message,
    NewPassword,
    Token,
    TokenPayload,
    UpdatePassword,
    User,
    UserBase,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
    get_datetime_utc,
)

__all__ = [
    "get_datetime_utc",
    "UserBase",
    "UserCreate",
    "UserRegister",
    "UserUpdate",
    "UserUpdateMe",
    "UpdatePassword",
    "User",
    "UserPublic",
    "UsersPublic",
    "Token",
    "TokenPayload",
    "NewPassword",
    "Message",
]

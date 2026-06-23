from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import settings


ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(
    plain_password: str, hashed_password: str
) -> tuple[bool, str | None]:
    """明文密码校验（本项目无隐私要求，为简化管理而使用明文）。"""
    return plain_password == hashed_password, None


def get_password_hash(password: str) -> str:
    """明文存储密码（本项目无隐私要求，不启用哈希）。"""
    return password

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from sqlmodel import Session, delete, or_, select

from app.core.config import settings
from app.core.security import get_password_hash
from app.models_core import FeishuLoginTicket, User

FEISHU_AUTHORIZE_URL = "https://accounts.feishu.cn/open-apis/authen/v1/authorize"
FEISHU_TOKEN_URL = "https://open.feishu.cn/open-apis/authen/v2/oauth/token"
FEISHU_USER_INFO_URL = "https://open.feishu.cn/open-apis/authen/v1/user_info"
TICKET_LIFETIME = timedelta(minutes=2)


class FeishuAuthError(Exception):
    pass


@dataclass(frozen=True)
class FeishuProfile:
    open_id: str
    name: str | None


def require_feishu_config() -> tuple[str, str, str]:
    if not (
        settings.FEISHU_APP_ID
        and settings.FEISHU_APP_SECRET
        and settings.FEISHU_REDIRECT_URI
    ):
        raise FeishuAuthError("Feishu login is not configured")
    return (
        settings.FEISHU_APP_ID,
        settings.FEISHU_APP_SECRET,
        settings.FEISHU_REDIRECT_URI,
    )


def build_authorization_url(state: str) -> str:
    app_id, _, redirect_uri = require_feishu_config()
    query = urlencode(
        {
            "client_id": app_id,
            "redirect_uri": redirect_uri,
            "state": state,
        }
    )
    return f"{FEISHU_AUTHORIZE_URL}?{query}"


def fetch_feishu_profile(code: str) -> FeishuProfile:
    app_id, app_secret, redirect_uri = require_feishu_config()
    try:
        with httpx.Client(timeout=10.0) as client:
            token_response = client.post(
                FEISHU_TOKEN_URL,
                json={
                    "grant_type": "authorization_code",
                    "client_id": app_id,
                    "client_secret": app_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )
            token_response.raise_for_status()
            token_payload = token_response.json()
            if token_payload.get("code", 0) != 0:
                raise FeishuAuthError(
                    token_payload.get("msg") or "Failed to exchange Feishu code"
                )
            access_token = token_payload.get("access_token") or token_payload.get(
                "data", {}
            ).get("access_token")
            if not access_token:
                raise FeishuAuthError("Feishu did not return an access token")

            profile_response = client.get(
                FEISHU_USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile_response.raise_for_status()
            profile_payload = profile_response.json()
    except httpx.HTTPError as exc:
        raise FeishuAuthError("Unable to reach Feishu authentication service") from exc

    if profile_payload.get("code", 0) != 0:
        raise FeishuAuthError(
            profile_payload.get("msg") or "Failed to obtain Feishu user information"
        )
    profile_data = profile_payload.get("data", profile_payload)
    open_id = profile_data.get("open_id")
    if not open_id:
        raise FeishuAuthError("Feishu did not return an open ID")
    return FeishuProfile(
        open_id=str(open_id),
        name=profile_data.get("name") or profile_data.get("en_name"),
    )


def get_or_create_feishu_user(
    *, session: Session, profile: FeishuProfile
) -> User:
    user = session.exec(
        select(User).where(User.feishu_open_id == profile.open_id)
    ).first()
    if user:
        return user

    user = User(
        email=_fallback_email(profile.open_id),
        full_name=profile.name,
        feishu_open_id=profile.open_id,
        hashed_password=get_password_hash(secrets.token_urlsafe(32)),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def issue_login_ticket(*, session: Session, user: User) -> str:
    now = datetime.now(timezone.utc)
    session.exec(
        delete(FeishuLoginTicket).where(
            or_(
                FeishuLoginTicket.expires_at <= now,
                FeishuLoginTicket.used_at.is_not(None),
            )
        )
    )
    raw_ticket = secrets.token_urlsafe(48)
    ticket = FeishuLoginTicket(
        user_id=user.id,
        token_hash=_hash_ticket(raw_ticket),
        expires_at=now + TICKET_LIFETIME,
    )
    session.add(ticket)
    session.commit()
    return raw_ticket


def consume_login_ticket(*, session: Session, raw_ticket: str) -> User:
    ticket = session.exec(
        select(FeishuLoginTicket)
        .where(FeishuLoginTicket.token_hash == _hash_ticket(raw_ticket))
        .with_for_update()
    ).first()
    now = datetime.now(timezone.utc)
    if not ticket or ticket.used_at or ticket.expires_at <= now:
        raise FeishuAuthError("Invalid or expired Feishu login ticket")
    user = session.get(User, ticket.user_id)
    if not user:
        raise FeishuAuthError("User linked to Feishu login no longer exists")
    ticket.used_at = now
    session.add(ticket)
    session.commit()
    return user


def _hash_ticket(raw_ticket: str) -> str:
    return hashlib.sha256(raw_ticket.encode()).hexdigest()


def _fallback_email(feishu_open_id: str) -> str:
    digest = hashlib.sha256(feishu_open_id.encode()).hexdigest()[:24]
    return f"feishu-{digest}@users.feishu.internal"

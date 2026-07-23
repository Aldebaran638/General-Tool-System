from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import settings

FEISHU_TENANT_TOKEN_URL = (
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
)
FEISHU_MESSAGE_URL = "https://open.feishu.cn/open-apis/im/v1/messages"
TOKEN_REFRESH_MARGIN = timedelta(minutes=5)


class FeishuMessageError(Exception):
    def __init__(self, message: str, *, code: str | None = None, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass
class _CachedToken:
    value: str
    expires_at: datetime


_token_cache: _CachedToken | None = None
_token_lock = threading.Lock()


def _require_credentials() -> tuple[str, str]:
    if not settings.FEISHU_APP_ID or not settings.FEISHU_APP_SECRET:
        raise FeishuMessageError("Feishu application credentials are not configured")
    return settings.FEISHU_APP_ID, settings.FEISHU_APP_SECRET


def get_tenant_access_token() -> str:
    global _token_cache

    now = datetime.now(timezone.utc)
    with _token_lock:
        if _token_cache and _token_cache.expires_at - TOKEN_REFRESH_MARGIN > now:
            return _token_cache.value

        app_id, app_secret = _require_credentials()
        try:
            response = httpx.post(
                FEISHU_TENANT_TOKEN_URL,
                json={"app_id": app_id, "app_secret": app_secret},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise FeishuMessageError(
                "Unable to obtain Feishu tenant access token", retryable=True
            ) from exc

        if payload.get("code", 0) != 0 or not payload.get("tenant_access_token"):
            raise FeishuMessageError(
                payload.get("msg") or "Feishu did not return a tenant access token",
                code=str(payload.get("code")) if payload.get("code") is not None else None,
            )
        expires_in = int(payload.get("expire", 7200))
        _token_cache = _CachedToken(
            value=str(payload["tenant_access_token"]),
            expires_at=now + timedelta(seconds=expires_in),
        )
        return _token_cache.value


def send_interactive_message(
    *, open_id: str, card: dict[str, Any], idempotency_key: str
) -> str:
    token = get_tenant_access_token()
    try:
        response = httpx.post(
            FEISHU_MESSAGE_URL,
            params={"receive_id_type": "open_id"},
            headers={"Authorization": f"Bearer {token}"},
            json={
                "receive_id": open_id,
                "msg_type": "interactive",
                "content": json.dumps(card, ensure_ascii=False),
                "uuid": idempotency_key[:50],
            },
            timeout=10,
        )
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise FeishuMessageError(
            "Unable to send Feishu message", retryable=True
        ) from exc

    code = payload.get("code", 0)
    if response.status_code >= 500 or response.status_code == 429:
        raise FeishuMessageError(
            payload.get("msg") or f"Feishu returned HTTP {response.status_code}",
            code=str(code),
            retryable=True,
        )
    if response.is_error or code != 0:
        raise FeishuMessageError(
            payload.get("msg") or "Feishu rejected the message",
            code=str(code),
        )
    message_id = payload.get("data", {}).get("message_id")
    if not message_id:
        raise FeishuMessageError("Feishu did not return a message ID")
    return str(message_id)


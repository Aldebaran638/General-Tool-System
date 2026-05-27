"""
WeCom (企业微信) API Client

Provides WecomClient — a single class that encapsulates every interaction
with the WeCom server-side API:

  • access_token lifecycle  (cached; NEVER returned to the frontend)
  • OAuth2 code exchange    (userid from code)
  • User detail             (read member info)
  • Department tree         (list all / sub-departments)
  • Department user list    (members with fetch_child)
  • App message sending     (text + textcard)

Security contract
-----------------
access_token is obtained exclusively in the backend.
It must NEVER be passed to, or readable by, the frontend.

Multi-process note
------------------
_token_cache is a class-level in-memory dict.  It works correctly for a
single-process server (development, single-worker production).
For multi-worker deployments, swap out _token_cache for a Redis-backed
implementation without changing any call-sites.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import settings

# ─── constants ────────────────────────────────────────────────────────────────

_WECOM_API_BASE = "https://qyapi.weixin.qq.com"
_WECOM_OAUTH_BASE = "https://open.weixin.qq.com"

# Token is refreshed 5 minutes before actual expiry
_TOKEN_REFRESH_AHEAD_SECS = 300


# ─── exceptions ───────────────────────────────────────────────────────────────

class WecomAPIError(Exception):
    """Raised when WeCom API returns a non-zero errcode."""

    def __init__(self, errcode: int, errmsg: str, raw: dict) -> None:
        self.errcode = errcode
        self.errmsg = errmsg
        self.raw = raw
        super().__init__(f"WeCom API error {errcode}: {errmsg}")


class WecomNotConfiguredError(ValueError):
    """Raised when WeCom credentials are missing from settings."""


# ─── client ───────────────────────────────────────────────────────────────────

class WecomClient:
    """
    WeCom API client.

    Class-level _token_cache is shared across all instances so that
    multiple callers within the same process reuse the same token.
    """

    _token_cache: dict[str, dict[str, Any]] = {}
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self, corp_id: str, secret: str, agent_id: str) -> None:
        self.corp_id = corp_id
        self.secret = secret
        self.agent_id = agent_id

    # =========================================================================
    # Internal helpers
    # =========================================================================

    @staticmethod
    def _assert_ok(data: dict) -> None:
        """Raise WecomAPIError if errcode != 0."""
        errcode = data.get("errcode", 0)
        if errcode != 0:
            raise WecomAPIError(
                errcode=errcode,
                errmsg=data.get("errmsg", "unknown error"),
                raw=data,
            )

    # =========================================================================
    # Token management
    # =========================================================================

    async def get_access_token(self) -> str:
        """
        Return a valid access_token, refreshing from WeCom when needed.

        Thread-safe via asyncio.Lock; uses double-checked locking to avoid
        redundant requests from concurrent coroutines.

        Security: do NOT return this value in any API response.
        """
        now = time.time()
        cached = self._token_cache.get(self.corp_id)
        if cached and cached["expire_at"] > now + _TOKEN_REFRESH_AHEAD_SECS:
            return cached["token"]

        async with self._lock:
            # Re-check after acquiring the lock
            cached = self._token_cache.get(self.corp_id)
            if cached and cached["expire_at"] > now + _TOKEN_REFRESH_AHEAD_SECS:
                return cached["token"]

            url = f"{_WECOM_API_BASE}/cgi-bin/gettoken"
            params = {"corpid": self.corp_id, "corpsecret": self.secret}
            async with httpx.AsyncClient(timeout=30) as http:
                resp = await http.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            self._assert_ok(data)

            token: str = data["access_token"]
            expires_in: int = data.get("expires_in", 7200)
            self._token_cache[self.corp_id] = {
                "token": token,
                "expire_at": now + expires_in,
            }
            return token

    # =========================================================================
    # OAuth2 helpers
    # =========================================================================

    def build_oauth_url(self, redirect_uri: str, state: str = "wecom") -> str:
        """
        Construct the WeCom OAuth2 authorization URL.

        The user's browser must be redirected to this URL.
        WeCom then redirects to redirect_uri?code=CODE&state=STATE.

        redirect_uri must be URL-encoded per WeCom docs.
        """
        encoded = quote(redirect_uri, safe="")
        return (
            f"{_WECOM_OAUTH_BASE}/connect/oauth2/authorize"
            f"?appid={self.corp_id}"
            f"&redirect_uri={encoded}"
            f"&response_type=code"
            f"&scope=snsapi_base"
            f"&state={state}"
            f"&agentid={self.agent_id}"
            f"#wechat_redirect"
        )

    async def get_user_info_by_code(self, code: str) -> dict[str, Any]:
        """
        Exchange an OAuth code for user identity.

        Returns a dict containing:
          - userid: str  (internal members only)
          - openid: str  (external users only; no access to this system)
        """
        token = await self.get_access_token()
        url = f"{_WECOM_API_BASE}/cgi-bin/auth/getuserinfo"
        params = {"access_token": token, "code": code}
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        self._assert_ok(data)
        return data

    # =========================================================================
    # User / member API
    # =========================================================================

    async def get_user_detail(self, userid: str) -> dict[str, Any]:
        """
        Read a member's full profile (通讯录 - 读取成员).

        Key fields: name, position, department, status, email, mobile.
        """
        token = await self.get_access_token()
        url = f"{_WECOM_API_BASE}/cgi-bin/user/get"
        params = {"access_token": token, "userid": userid}
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        self._assert_ok(data)
        return data

    async def list_department_users(
        self,
        department_id: int,
        fetch_child: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Get all members in a department (获取部门成员详情).

        fetch_child=1 recursively includes all sub-departments.
        Returns a list of member dicts with fields:
          userid, name, position, department, status, main_department, etc.
        """
        token = await self.get_access_token()
        url = f"{_WECOM_API_BASE}/cgi-bin/user/list"
        params = {
            "access_token": token,
            "department_id": department_id,
            "fetch_child": fetch_child,
        }
        async with httpx.AsyncClient(timeout=60) as http:
            resp = await http.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        self._assert_ok(data)
        return data.get("userlist", [])

    # =========================================================================
    # Department API
    # =========================================================================

    async def list_departments(
        self,
        department_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get department list (获取部门列表).

        If department_id is None, returns the full tree.
        Root department has parentid = 1.

        Each dict contains: id, name, parentid, order.
        """
        token = await self.get_access_token()
        url = f"{_WECOM_API_BASE}/cgi-bin/department/list"
        params: dict[str, Any] = {"access_token": token}
        if department_id is not None:
            params["id"] = department_id
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        self._assert_ok(data)
        return data.get("department", [])

    # =========================================================================
    # Messaging API
    # =========================================================================

    async def send_text_message(
        self,
        touser: str | list[str],
        content: str,
        safe: int = 0,
    ) -> dict[str, Any]:
        """
        Send a plain-text app message (发送应用消息 - text).

        touser accepts a single userid string or a list.
        WeCom API accepts at most 1000 users per call.
        """
        token = await self.get_access_token()
        url = f"{_WECOM_API_BASE}/cgi-bin/message/send"
        touser_str = "|".join(touser) if isinstance(touser, list) else touser
        payload = {
            "touser": touser_str,
            "msgtype": "text",
            "agentid": self.agent_id,
            "text": {"content": content},
            "safe": safe,
        }
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.post(url, params={"access_token": token}, json=payload)
            resp.raise_for_status()
            data = resp.json()
        self._assert_ok(data)
        return data

    async def send_textcard_message(
        self,
        touser: str | list[str],
        title: str,
        description: str,
        url: str,
        btntxt: str = "详情",
    ) -> dict[str, Any]:
        """
        Send a textcard (rich card) app message (发送应用消息 - textcard).

        Renders as a card with title, description, and a button link.
        Ideal for exam reminders: button links to the exam page.
        """
        token = await self.get_access_token()
        api_url = f"{_WECOM_API_BASE}/cgi-bin/message/send"
        touser_str = "|".join(touser) if isinstance(touser, list) else touser
        payload = {
            "touser": touser_str,
            "msgtype": "textcard",
            "agentid": self.agent_id,
            "textcard": {
                "title": title,
                "description": description,
                "url": url,
                "btntxt": btntxt,
            },
        }
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.post(
                api_url, params={"access_token": token}, json=payload
            )
            resp.raise_for_status()
            data = resp.json()
        self._assert_ok(data)
        return data


# ─── factory ──────────────────────────────────────────────────────────────────

def get_wecom_client() -> WecomClient:
    """
    Build a WecomClient from application settings.

    Raises WecomNotConfiguredError if any required env var is missing.
    Import this function wherever you need to call WeCom APIs.
    """
    corp_id = settings.WECOM_CORP_ID
    secret = settings.WECOM_SECRET
    agent_id = settings.WECOM_AGENT_ID

    if not all([corp_id, secret, agent_id]):
        missing = [
            name
            for name, val in [
                ("WECOM_CORP_ID", corp_id),
                ("WECOM_SECRET", secret),
                ("WECOM_AGENT_ID", agent_id),
            ]
            if not val
        ]
        raise WecomNotConfiguredError(
            f"WeCom is not fully configured. Missing: {', '.join(missing)}"
        )

    return WecomClient(corp_id=corp_id, secret=secret, agent_id=agent_id)  # type: ignore[arg-type]


# ─── backward-compatibility shims ─────────────────────────────────────────────
# Old call-sites that imported loose functions still work without changes.

async def get_access_token() -> str:
    return await get_wecom_client().get_access_token()


async def get_user_info_by_code(code: str) -> dict[str, Any]:
    return await get_wecom_client().get_user_info_by_code(code)


async def get_user_detail(userid: str) -> dict[str, Any]:
    return await get_wecom_client().get_user_detail(userid)

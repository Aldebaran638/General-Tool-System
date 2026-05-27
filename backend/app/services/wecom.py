"""WeCom (企业微信) API service."""

import time
from typing import Any

import httpx
from app.core.config import settings

# In-memory cache for access_token
_token_cache: dict[str, Any] = {}


async def get_access_token() -> str:
    """Fetch and cache WeCom access_token."""
    global _token_cache

    corp_id = settings.WECOM_CORP_ID
    secret = settings.WECOM_SECRET
    if not corp_id or not secret:
        raise ValueError("WeCom corp_id or secret is not configured")

    now = time.time()
    cached = _token_cache.get(corp_id)
    if cached and cached["expire_at"] > now + 60:
        return cached["token"]

    url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    params = {"corpid": corp_id, "corpsecret": secret}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

    if data.get("errcode") != 0:
        raise RuntimeError(f"WeCom gettoken failed: {data}")

    token = data["access_token"]
    expires_in = data.get("expires_in", 7200)
    _token_cache[corp_id] = {"token": token, "expire_at": now + expires_in}
    return token


async def get_user_info_by_code(code: str) -> dict[str, Any]:
    """Exchange OAuth code for WeCom user info."""
    token = await get_access_token()
    url = "https://qyapi.weixin.qq.com/cgi-bin/auth/getuserinfo"
    params = {"access_token": token, "code": code}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

    if data.get("errcode") != 0:
        raise RuntimeError(f"WeCom getuserinfo failed: {data}")

    return data


async def get_user_detail(userid: str) -> dict[str, Any]:
    """Fetch detailed user info by userid."""
    token = await get_access_token()
    url = "https://qyapi.weixin.qq.com/cgi-bin/user/get"
    params = {"access_token": token, "userid": userid}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

    if data.get("errcode") != 0:
        raise RuntimeError(f"WeCom user/get failed: {data}")

    return data

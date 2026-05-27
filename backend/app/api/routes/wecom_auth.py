"""
WeCom OAuth Routes  (/api/auth/wecom/*)

These routes sit OUTSIDE the versioned /api/v1 prefix so that the OAuth
redirect_uri is stable and easy to configure as a trusted domain.

Flow
----
1. Frontend (in WeCom browser) detects WeCom UA and navigates to:
       GET /api/auth/wecom/login
   → Backend 302-redirects to WeCom OAuth URL.

2. Employee authorises → WeCom redirects to:
       GET /api/auth/wecom/callback?code=CODE&state=STATE
   → Backend exchanges code for userid, issues JWT,
     302-redirects to frontend:  /auth/wecom-callback?token=JWT

3. Frontend /auth/wecom-callback page stores JWT in localStorage
   and navigates to the main layout.

JSON variants
-------------
GET  /api/auth/wecom/oauth-url  → { "url": "<oauth url>" }
POST /api/auth/wecom/token      → { "access_token": "<jwt>", "token_type": "bearer" }

Security
--------
• WeCom access_token is NEVER returned in any response.
• JWT is issued only after successful WeCom identity verification.
• External WeCom users (openid without userid) are rejected.
"""

import secrets
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlmodel import select

from app.api.deps import SessionDep
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import SystemUserRole, Token, User
from app.services.wecom import WecomAPIError, WecomNotConfiguredError, get_wecom_client

router = APIRouter(tags=["wecom-auth"])


# ─── private helpers ──────────────────────────────────────────────────────────

def _callback_redirect_uri() -> str:
    """The URI WeCom redirects to after the user authorises."""
    return f"{settings.FRONTEND_HOST.rstrip('/')}/api/auth/wecom/callback"


async def _code_to_jwt(code: str, session: Any) -> str:
    """
    Core gateway logic: WeCom OAuth code → local JWT.

    Steps:
      1. Exchange code for WeCom userid (via WeCom API).
      2. Reject external users (no userid field).
      3. Fetch member name from user detail (best-effort).
      4. Find-or-create a local User bound to this wecom_userid.
      5. Sync is_superuser flag from SystemUserRole table.
      6. Issue and return a JWT.
    """
    try:
        client = get_wecom_client()
    except WecomNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    # Step 1 – exchange code
    try:
        user_info = await client.get_user_info_by_code(code)
    except WecomAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"WeCom identity exchange failed: {exc.errmsg} (errcode={exc.errcode})",
        ) from exc

    # Step 2 – internal members only
    wecom_userid: str | None = user_info.get("userid")
    if not wecom_userid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Only internal WeCom members can log in. "
                "External users (openid) are not supported."
            ),
        )

    # Step 3 – best-effort name
    name: str = wecom_userid
    try:
        detail = await client.get_user_detail(wecom_userid)
        name = detail.get("name") or wecom_userid
    except Exception:
        pass  # Non-fatal: fall back to userid as display name

    # Step 4 – find-or-create local user
    db_user: User | None = session.exec(
        select(User).where(User.wecom_userid == wecom_userid)
    ).first()

    if db_user is None:
        # Auto-provision: create a local account tied to this WeCom identity
        email = f"wecom_{wecom_userid}@wecom.local"
        # Edge-case: a manually pre-created account with this email
        db_user = session.exec(select(User).where(User.email == email)).first()
        if db_user:
            db_user.wecom_userid = wecom_userid
            db_user.full_name = name
        else:
            db_user = User(
                email=email,
                full_name=name,
                wecom_userid=wecom_userid,
                # Password is random and unusable; login is WeCom-only
                hashed_password=get_password_hash(secrets.token_urlsafe(32)),
                is_active=True,
                is_superuser=False,
            )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)

    # Step 5 – sync superuser flag from role table
    role = session.exec(
        select(SystemUserRole).where(SystemUserRole.userid == wecom_userid)
    ).first()
    should_be_super = bool(role and role.role_code == "SUPER_ADMIN")
    if db_user.is_superuser != should_be_super:
        db_user.is_superuser = should_be_super
        session.add(db_user)
        session.commit()
        session.refresh(db_user)

    # Step 6 – issue JWT
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return security.create_access_token(str(db_user.id), expires_delta=expires)


# ─── routes ───────────────────────────────────────────────────────────────────

@router.get(
    "/wecom/login",
    summary="Redirect browser to WeCom OAuth",
    description=(
        "Immediately 302-redirects to the WeCom OAuth authorisation page. "
        "Use `window.location.href = '/api/auth/wecom/login'` from the frontend."
    ),
)
def wecom_login() -> RedirectResponse:
    try:
        client = get_wecom_client()
    except WecomNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    url = client.build_oauth_url(_callback_redirect_uri())
    return RedirectResponse(url=url, status_code=302)


@router.get(
    "/wecom/oauth-url",
    summary="Return WeCom OAuth URL as JSON",
    description="Useful when the SPA wants to redirect programmatically.",
)
def wecom_oauth_url() -> dict[str, str]:
    try:
        client = get_wecom_client()
    except WecomNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    url = client.build_oauth_url(_callback_redirect_uri())
    return {"url": url}


@router.get(
    "/wecom/callback",
    summary="WeCom OAuth callback (redirects to frontend with JWT)",
    include_in_schema=False,  # Not a public API; called by WeCom server
)
async def wecom_callback(
    session: SessionDep,
    code: str = Query(..., description="OAuth code from WeCom"),
    state: str = Query(default="wecom"),
) -> RedirectResponse:
    jwt_token = await _code_to_jwt(code, session)
    frontend = settings.FRONTEND_HOST.rstrip("/")
    return RedirectResponse(
        url=f"{frontend}/auth/wecom-callback?token={jwt_token}",
        status_code=302,
    )


@router.post(
    "/wecom/token",
    response_model=Token,
    summary="Exchange WeCom code for JWT (JSON response)",
    description=(
        "Alternative to the redirect flow. "
        "Useful for native-app scenarios where a redirect is inconvenient."
    ),
)
async def wecom_token(
    session: SessionDep,
    code: str = Query(..., description="OAuth code from WeCom"),
) -> Token:
    access_token = await _code_to_jwt(code, session)
    return Token(access_token=access_token)


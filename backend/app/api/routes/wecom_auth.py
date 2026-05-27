import secrets
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlmodel import select

from app.api.deps import SessionDep
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import SystemUserRole, Token, User
from app.services.wecom import get_user_detail, get_user_info_by_code

router = APIRouter(tags=["wecom-auth"])


@router.get("/wecom/oauth-url")
def wecom_oauth_url() -> dict[str, str]:
    """Return the WeCom OAuth URL for frontend redirect."""
    corp_id = settings.WECOM_CORP_ID
    agent_id = settings.WECOM_AGENT_ID
    if not corp_id or not agent_id:
        raise HTTPException(status_code=500, detail="WeCom is not configured")

    redirect_uri = f"{settings.FRONTEND_HOST.rstrip('/')}/api/auth/wecom/callback"
    url = (
        f"https://open.weixin.qq.com/connect/oauth2/authorize"
        f"?appid={corp_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=snsapi_base"
        f"&agentid={agent_id}"
        f"&state=STATE#wechat_redirect"
    )
    return {"url": url}


@router.get("/wecom/callback")
async def wecom_callback(
    code: str = Query(...),
    state: str = Query(default=""),
    session: SessionDep,
) -> Any:
    """Handle WeCom OAuth callback and redirect to frontend with token."""
    try:
        user_info = await get_user_info_by_code(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"WeCom auth failed: {e}")

    wecom_userid = user_info.get("userid")
    if not wecom_userid:
        raise HTTPException(status_code=400, detail="Failed to get WeCom userid")

    # Fetch detailed user info
    try:
        detail = await get_user_detail(wecom_userid)
    except Exception:
        detail = {}

    name = detail.get("name") or wecom_userid

    # Find or create local user
    db_user = session.exec(select(User).where(User.wecom_userid == wecom_userid)).first()
    if not db_user:
        # Check if a user with this email already exists
        email = detail.get("email") or f"wecom_{wecom_userid}@wecom.local"
        db_user = session.exec(select(User).where(User.email == email)).first()
        if db_user:
            db_user.wecom_userid = wecom_userid
            db_user.full_name = name
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
        else:
            # Create new user
            db_user = User(
                email=email,
                full_name=name,
                wecom_userid=wecom_userid,
                hashed_password=get_password_hash(secrets.token_urlsafe(32)),
                is_active=True,
                is_superuser=False,
            )
            session.add(db_user)
            session.commit()
            session.refresh(db_user)

    # Determine role from system_user_role table
    role_record = session.exec(
        select(SystemUserRole).where(SystemUserRole.userid == wecom_userid)
    ).first()
    if role_record and role_record.role_code == "SUPER_ADMIN":
        db_user.is_superuser = True
        session.add(db_user)
        session.commit()
        session.refresh(db_user)

    # Generate JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(
        str(db_user.id), expires_delta=access_token_expires
    )

    # Redirect to frontend with token
    redirect_url = f"{settings.FRONTEND_HOST.rstrip('/')}/auth/callback?token={token}"
    return RedirectResponse(url=redirect_url)


@router.post("/wecom/token", response_model=Token)
async def wecom_token(
    code: str = Query(...),
    session: SessionDep,
) -> Any:
    """Exchange WeCom OAuth code for local JWT (JSON response, no redirect)."""
    try:
        user_info = await get_user_info_by_code(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"WeCom auth failed: {e}")

    wecom_userid = user_info.get("userid")
    if not wecom_userid:
        raise HTTPException(status_code=400, detail="Failed to get WeCom userid")

    try:
        detail = await get_user_detail(wecom_userid)
    except Exception:
        detail = {}

    name = detail.get("name") or wecom_userid
    email = detail.get("email") or f"wecom_{wecom_userid}@wecom.local"

    db_user = session.exec(select(User).where(User.wecom_userid == wecom_userid)).first()
    if not db_user:
        db_user = session.exec(select(User).where(User.email == email)).first()
        if db_user:
            db_user.wecom_userid = wecom_userid
            db_user.full_name = name
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
        else:
            db_user = User(
                email=email,
                full_name=name,
                wecom_userid=wecom_userid,
                hashed_password=get_password_hash(secrets.token_urlsafe(32)),
                is_active=True,
                is_superuser=False,
            )
            session.add(db_user)
            session.commit()
            session.refresh(db_user)

    role_record = session.exec(
        select(SystemUserRole).where(SystemUserRole.userid == wecom_userid)
    ).first()
    if role_record and role_record.role_code == "SUPER_ADMIN":
        db_user.is_superuser = True
        session.add(db_user)
        session.commit()
        session.refresh(db_user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(
        str(db_user.id), expires_delta=access_token_expires
    )
    return Token(access_token=token, token_type="bearer")

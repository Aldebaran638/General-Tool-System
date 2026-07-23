import hmac
import secrets
from datetime import timedelta
from typing import Annotated, Any
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from app import crud
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core import security
from app.core.config import settings
from app.models import (
    FeishuTicketExchange,
    Message,
    NewPassword,
    Token,
    UserPublic,
    UserUpdate,
)
from app.services.feishu_auth import (
    FeishuAuthError,
    build_authorization_url,
    consume_login_ticket,
    fetch_feishu_profile,
    get_or_create_feishu_user,
    issue_login_ticket,
)
from app.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)

router = APIRouter(tags=["login"])
FEISHU_STATE_COOKIE = "feishu_oauth_state"
FEISHU_COOKIE_PATH = f"{settings.API_V1_STR}/login/feishu"


def _create_app_token(user_id: Any) -> Token:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user_id, expires_delta=access_token_expires
        )
    )


def _feishu_frontend_callback(**params: str) -> str:
    callback_url = f"{settings.FRONTEND_HOST.rstrip('/')}/login/feishu/callback"
    return f"{callback_url}?{urlencode(params)}"


@router.post("/login/access-token")
def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return _create_app_token(user.id)


@router.get("/login/feishu/authorize", response_class=RedirectResponse)
def authorize_feishu_login() -> RedirectResponse:
    state = secrets.token_urlsafe(32)
    try:
        authorization_url = build_authorization_url(state)
    except FeishuAuthError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    response = RedirectResponse(authorization_url, status_code=302)
    response.set_cookie(
        FEISHU_STATE_COOKIE,
        state,
        max_age=600,
        httponly=True,
        secure=settings.ENVIRONMENT != "local",
        samesite="lax",
        path=FEISHU_COOKIE_PATH,
    )
    return response


@router.get("/login/feishu/callback", response_class=RedirectResponse)
def feishu_login_callback(
    session: SessionDep,
    state: Annotated[str, Query(min_length=16)],
    code: str | None = None,
    error: str | None = None,
    state_cookie: Annotated[str | None, Cookie(alias=FEISHU_STATE_COOKIE)] = None,
) -> RedirectResponse:
    if not state_cookie or not hmac.compare_digest(state, state_cookie):
        response = RedirectResponse(
            _feishu_frontend_callback(error="invalid_state"), status_code=302
        )
        response.delete_cookie(FEISHU_STATE_COOKIE, path=FEISHU_COOKIE_PATH)
        return response
    if error or not code:
        response = RedirectResponse(
            _feishu_frontend_callback(error=error or "authorization_failed"),
            status_code=302,
        )
        response.delete_cookie(FEISHU_STATE_COOKIE, path=FEISHU_COOKIE_PATH)
        return response
    try:
        profile = fetch_feishu_profile(code)
        user = get_or_create_feishu_user(session=session, profile=profile)
        if not user.is_active:
            raise FeishuAuthError("Inactive user")
        ticket = issue_login_ticket(session=session, user=user)
        response = RedirectResponse(
            _feishu_frontend_callback(ticket=ticket), status_code=302
        )
    except FeishuAuthError as exc:
        response = RedirectResponse(
            _feishu_frontend_callback(error=str(exc)), status_code=302
        )
    response.delete_cookie(FEISHU_STATE_COOKIE, path=FEISHU_COOKIE_PATH)
    return response


@router.post("/login/feishu/exchange", response_model=Token)
def exchange_feishu_login_ticket(
    *, session: SessionDep, body: FeishuTicketExchange
) -> Token:
    try:
        user = consume_login_ticket(session=session, raw_ticket=body.ticket)
    except FeishuAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return _create_app_token(user.id)


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}")
def recover_password(email: str, session: SessionDep) -> Message:
    """
    Password Recovery
    """
    user = crud.get_user_by_email(session=session, email=email)

    # Always return the same response to prevent email enumeration attacks
    # Only send email if user actually exists
    if user:
        password_reset_token = generate_password_reset_token(email=email)
        email_data = generate_reset_password_email(
            email_to=user.email, email=email, token=password_reset_token
        )
        send_email(
            email_to=user.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return Message(
        message="If that email is registered, we sent a password recovery link"
    )


@router.post("/reset-password/")
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = crud.get_user_by_email(session=session, email=email)
    if not user:
        # Don't reveal that the user doesn't exist - use same error as invalid token
        raise HTTPException(status_code=400, detail="Invalid token")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    user_in_update = UserUpdate(password=body.new_password)
    crud.update_user(
        session=session,
        db_user=user,
        user_in=user_in_update,
    )
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
)
def recover_password_html_content(email: str, session: SessionDep) -> Any:
    """
    HTML Content for Password Recovery
    """
    user = crud.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )

    return HTMLResponse(
        content=email_data.html_content, headers={"subject:": email_data.subject}
    )

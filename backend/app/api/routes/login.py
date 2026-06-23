from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.core import security
from app.core.config import settings
from app.models import Message, NewPassword, Token, UserPublic, UserUpdate

router = APIRouter(tags=["login"])


@router.post("/login/access-token")
def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.authenticate(
        session=session, wecom_userid=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect wecom_userid or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{wecom_userid}")
def recover_password(wecom_userid: str, session: SessionDep) -> Message:
    """
    Password Recovery
    """
    user = crud.get_user_by_wecom_userid(session=session, wecom_userid=wecom_userid)

    # Always return the same response to prevent user enumeration attacks
    if user:
        # Email is no longer stored; password reset must be done by an admin.
        pass
    return Message(
        message="If that account is registered, please contact an admin to reset the password"
    )


@router.post("/reset-password/")
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """
    # Password reset via email token is no longer supported because email field is removed.
    # Admins can reset passwords directly from the admin panel.
    raise HTTPException(
        status_code=400,
        detail="Password reset via token is disabled. Contact an admin.",
    )

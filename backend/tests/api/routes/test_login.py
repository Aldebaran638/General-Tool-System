from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.crud import create_user
from app.models import User, UserCreate
from app.services.feishu_auth import FeishuProfile
from app.utils import generate_password_reset_token
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string


def test_get_access_token(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]


def test_get_access_token_incorrect_password(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": "incorrect",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400


def test_use_access_token(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers=superuser_token_headers,
    )
    result = r.json()
    assert r.status_code == 200
    assert "email" in result


def test_recovery_password(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    with (
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.core.config.settings.SMTP_USER", "admin@example.com"),
    ):
        email = "test@example.com"
        r = client.post(
            f"{settings.API_V1_STR}/password-recovery/{email}",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 200
        assert r.json() == {
            "message": "If that email is registered, we sent a password recovery link"
        }


def test_recovery_password_user_not_exits(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    email = "jVgQr@example.com"
    r = client.post(
        f"{settings.API_V1_STR}/password-recovery/{email}",
        headers=normal_user_token_headers,
    )
    # Should return 200 with generic message to prevent email enumeration attacks
    assert r.status_code == 200
    assert r.json() == {
        "message": "If that email is registered, we sent a password recovery link"
    }


def test_reset_password(client: TestClient, db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    new_password = random_lower_string()

    user_create = UserCreate(
        email=email,
        full_name="Test User",
        password=password,
        is_active=True,
        is_superuser=False,
    )
    user = create_user(session=db, user_create=user_create)
    token = generate_password_reset_token(email=email)
    headers = user_authentication_headers(client=client, email=email, password=password)
    data = {"new_password": new_password, "token": token}

    r = client.post(
        f"{settings.API_V1_STR}/reset-password/",
        headers=headers,
        json=data,
    )

    assert r.status_code == 200
    assert r.json() == {"message": "Password updated successfully"}

    db.refresh(user)
    verified, _ = verify_password(new_password, user.hashed_password)
    assert verified


def test_reset_password_invalid_token(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"new_password": "changethis", "token": "invalid"}
    r = client.post(
        f"{settings.API_V1_STR}/reset-password/",
        headers=superuser_token_headers,
        json=data,
    )
    response = r.json()

    assert "detail" in response
    assert r.status_code == 400
    assert response["detail"] == "Invalid token"


def test_login_with_bcrypt_password_upgrades_to_argon2(
    client: TestClient, db: Session
) -> None:
    """Test that logging in with a bcrypt password hash upgrades it to argon2."""
    email = random_email()
    password = random_lower_string()

    # Create a bcrypt hash directly (simulating legacy password)
    bcrypt_hasher = BcryptHasher()
    bcrypt_hash = bcrypt_hasher.hash(password)
    assert bcrypt_hash.startswith("$2")  # bcrypt hashes start with $2

    user = User(email=email, hashed_password=bcrypt_hash, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.hashed_password.startswith("$2")

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens

    db.refresh(user)

    # Verify the hash was upgraded to argon2
    assert user.hashed_password.startswith("$argon2")

    verified, updated_hash = verify_password(password, user.hashed_password)
    assert verified
    # Should not need another update since it's already argon2
    assert updated_hash is None


def test_login_with_argon2_password_keeps_hash(client: TestClient, db: Session) -> None:
    """Test that logging in with an argon2 password hash does not update it."""
    email = random_email()
    password = random_lower_string()

    # Create an argon2 hash (current default)
    argon2_hash = get_password_hash(password)
    assert argon2_hash.startswith("$argon2")

    # Create user with argon2 hash
    user = User(email=email, hashed_password=argon2_hash, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    original_hash = user.hashed_password

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens

    db.refresh(user)

    assert user.hashed_password == original_hash
    assert user.hashed_password.startswith("$argon2")


def test_feishu_login_creates_user_and_exchanges_ticket(
    client: TestClient, db: Session
) -> None:
    profile = FeishuProfile(open_id="feishu-user-new", name="Feishu User")
    with (
        patch.object(settings, "FEISHU_APP_ID", "cli_test"),
        patch.object(settings, "FEISHU_APP_SECRET", "secret"),
        patch.object(settings, "ENVIRONMENT", "production"),
        patch.object(settings, "AUTH_COOKIE_SECURE", False),
        patch.object(
            settings,
            "FEISHU_REDIRECT_URI",
            "http://localhost:10304/api/v1/login/feishu/callback",
        ),
    ):
        authorize_response = client.get(
            f"{settings.API_V1_STR}/login/feishu/authorize",
            follow_redirects=False,
        )
        assert authorize_response.status_code == 302
        authorize_query = parse_qs(urlparse(authorize_response.headers["location"]).query)
        state = authorize_query["state"][0]
        assert "scope" not in authorize_query
        assert "secure" not in authorize_response.headers["set-cookie"].lower()

        with patch(
            "app.api.routes.login.fetch_feishu_profile", return_value=profile
        ):
            callback_response = client.get(
                f"{settings.API_V1_STR}/login/feishu/callback",
                params={"code": "valid-code", "state": state},
                follow_redirects=False,
            )

    assert callback_response.status_code == 302
    callback_query = parse_qs(urlparse(callback_response.headers["location"]).query)
    ticket = callback_query["ticket"][0]
    created_user = db.exec(
        select(User).where(User.feishu_open_id == profile.open_id)
    ).one()
    assert created_user.feishu_open_id == profile.open_id
    assert created_user.full_name == profile.name
    assert created_user.hashed_password
    assert created_user.is_active is True
    assert created_user.is_superuser is False

    exchange_response = client.post(
        f"{settings.API_V1_STR}/login/feishu/exchange", json={"ticket": ticket}
    )
    assert exchange_response.status_code == 200
    assert exchange_response.json()["access_token"]

    replay_response = client.post(
        f"{settings.API_V1_STR}/login/feishu/exchange", json={"ticket": ticket}
    )
    assert replay_response.status_code == 400


def test_feishu_login_user_is_returned_by_user_list(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    profile = FeishuProfile(open_id="feishu-user-without-email", name="Feishu User")
    with (
        patch.object(settings, "FEISHU_APP_ID", "cli_test"),
        patch.object(settings, "FEISHU_APP_SECRET", "secret"),
        patch.object(
            settings,
            "FEISHU_REDIRECT_URI",
            "http://localhost:10304/api/v1/login/feishu/callback",
        ),
    ):
        authorize_response = client.get(
            f"{settings.API_V1_STR}/login/feishu/authorize",
            follow_redirects=False,
        )
        state = parse_qs(urlparse(authorize_response.headers["location"]).query)[
            "state"
        ][0]
        with patch(
            "app.api.routes.login.fetch_feishu_profile", return_value=profile
        ):
            callback_response = client.get(
                f"{settings.API_V1_STR}/login/feishu/callback",
                params={"code": "valid-code", "state": state},
                follow_redirects=False,
            )

    ticket = parse_qs(urlparse(callback_response.headers["location"]).query)[
        "ticket"
    ][0]
    created_user = db.exec(
        select(User).where(User.feishu_open_id == profile.open_id)
    ).one()
    assert created_user.email.endswith("@users.feishu.internal")

    exchange_response = client.post(
        f"{settings.API_V1_STR}/login/feishu/exchange", json={"ticket": ticket}
    )
    assert exchange_response.status_code == 200
    access_token = exchange_response.json()["access_token"]

    current_user_response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert current_user_response.status_code == 200
    assert current_user_response.json()["is_feishu_user"] is True

    users_response = client.get(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers
    )
    assert users_response.status_code == 200


def test_feishu_callback_rejects_invalid_state(client: TestClient) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/login/feishu/callback",
        params={"code": "code", "state": "invalid-state-value"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "error=invalid_state" in response.headers["location"]

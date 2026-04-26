import os
from collections.abc import Generator

# CRITICAL: Set TESTING before any app import so that Settings
# computes SQLALCHEMY_DATABASE_URI pointing at the test database.
os.environ["TESTING"] = "true"

# Each pytest session gets its own PID-based database name to avoid
# collisions when multiple pytest processes run in parallel.
_test_db_name = f"app_test_{os.getpid()}"
os.environ["POSTGRES_TEST_DB"] = _test_db_name

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlmodel import Session

from alembic import command
from alembic.config import Config

from app.api.deps import get_db
from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app

from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


def _admin_engine():
    admin_url = (
        f"postgresql+psycopg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/postgres"
    )
    return create_engine(admin_url, isolation_level="AUTOCOMMIT")


def _create_test_db() -> None:
    admin = _admin_engine()
    with admin.connect() as conn:
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
            {"db_name": settings.POSTGRES_TEST_DB},
        )
        if not result.scalar():
            conn.execute(text(f'CREATE DATABASE "{settings.POSTGRES_TEST_DB}"'))
    admin.dispose()


def _drop_test_db() -> None:
    admin = _admin_engine()
    with admin.connect() as conn:
        # Terminate any existing connections to the test DB before dropping
        conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :db_name AND pid <> pg_backend_pid()"
            ),
            {"db_name": settings.POSTGRES_TEST_DB},
        )
        conn.execute(text(f'DROP DATABASE IF EXISTS "{settings.POSTGRES_TEST_DB}"'))
    admin.dispose()


def _run_migrations() -> None:
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    _create_test_db()
    _run_migrations()

    def _get_db_override() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = _get_db_override

    with Session(engine) as session:
        init_db(session)
        yield session

    _drop_test_db()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )

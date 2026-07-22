import os
from collections.abc import Generator
from pathlib import Path

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from psycopg import sql
from sqlmodel import Session

# Tests must never write to the development database. They use a separate
# database in the same PostgreSQL service and recreate it for each test session.
os.environ["POSTGRES_DB"] = os.getenv("POSTGRES_TEST_DB", "app_test")

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


def _reset_test_database() -> None:
    if settings.POSTGRES_DB in {"app", "postgres", "template0", "template1"}:
        raise RuntimeError(f"Refusing to reset non-test database: {settings.POSTGRES_DB}")

    with psycopg.connect(
        dbname="postgres",
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_SERVER,
        port=settings.POSTGRES_PORT,
        autocommit=True,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s
                  AND pid <> pg_backend_pid()
                """,
                (settings.POSTGRES_DB,),
            )
            cursor.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(
                    sql.Identifier(settings.POSTGRES_DB)
                )
            )
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(settings.POSTGRES_DB)
                )
            )


def _run_migrations() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    _reset_test_database()
    _run_migrations()

    with Session(engine) as session:
        init_db(session)
        yield session


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

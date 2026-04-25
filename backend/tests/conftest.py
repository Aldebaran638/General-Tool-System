from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.modules.finance.invoice_files.models import InvoiceFile
from app.modules.workbench.project_management.models import Item
from app.modules.finance.purchase_records.models import PurchaseRecord
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        # Clean up any leftover data from previous aborted runs
        session.execute(delete(InvoiceFile))
        session.execute(delete(PurchaseRecord))
        session.execute(delete(Item))
        session.commit()
        yield session
        statement = delete(InvoiceFile)
        session.execute(statement)
        statement = delete(PurchaseRecord)
        session.execute(statement)
        statement = delete(Item)
        session.execute(statement)
        session.commit()


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

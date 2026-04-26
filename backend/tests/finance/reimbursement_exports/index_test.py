"""
Reimbursement Exports Backend Tests

Tests for the reimbursement_exports tool module (second rework).
"""

import io
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlmodel import select
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

_invoice_counter = 0

from app.core.config import settings
from app.models_core import AppSetting, User
from app.modules.finance.invoice_files.models import InvoiceFile
from app.modules.finance.invoice_matching.constants import MATCH_STATUS_CONFIRMED
from app.modules.finance.invoice_matching.models import InvoiceMatch
from app.modules.finance.purchase_records.constants import (
    CATEGORY_MEALS_ENTERTAINMENT,
    CATEGORY_OTHER_PROJECT,
    CATEGORY_TRANSPORTATION,
    CATEGORY_VEHICLE,
    STATUS_APPROVED,
    STATUS_DRAFT,
    STATUS_SUBMITTED,
)
from app.modules.finance.purchase_records.models import PurchaseRecord
from app.modules.finance.reimbursement_exports.constants import (
    DEFAULT_RETENTION_DAYS,
    MAX_RETENTION_DAYS,
    MIN_RETENTION_DAYS,
    SETTING_RETENTION_DAYS,
)
from app.modules.finance.reimbursement_exports.models import (
    ReimbursementExport,
    ReimbursementExportItem,
)
from app.modules.finance.reimbursement_exports.storage import EXPORT_DIR_PATH

from tests.utils.user import (
    authentication_token_from_email,
    user_authentication_headers,
)
from tests.utils.utils import get_superuser_token_headers


# =============================================================================
# Helpers
# =============================================================================

def _superuser_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client,
        email=settings.FIRST_SUPERUSER,
        db=db,
    )


def _create_invoice_file(
    db: Session,
    *,
    owner_id: uuid.UUID,
    status: str = "confirmed",
    deleted_at: datetime | None = None,
) -> InvoiceFile:
    global _invoice_counter
    _invoice_counter += 1
    inv = InvoiceFile(
        owner_id=owner_id,
        invoice_number=f"INV-{_invoice_counter:04d}",
        invoice_type="general_invoice",
        invoice_date=date.today(),
        invoice_amount=Decimal("100.00"),
        tax_amount=Decimal("0.00"),
        currency="CNY",
        buyer="Buyer A",
        seller="Seller A",
        pdf_path="/tmp/test.pdf",
        pdf_original_name="test.pdf",
        pdf_mime_type="application/pdf",
        pdf_size=1234,
        status=status,
        deleted_at=deleted_at,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def _create_purchase_record(
    db: Session,
    *,
    owner_id: uuid.UUID,
    status: str = STATUS_APPROVED,
    category: str = CATEGORY_TRANSPORTATION,
    subcategory: str | None = None,
    currency: str = "CNY",
    amount: Decimal = Decimal("100.00"),
    purchase_date: date | None = None,
    order_name: str = "test order",
) -> PurchaseRecord:
    record = PurchaseRecord(
        owner_id=owner_id,
        status=status,
        invoice_match_status="unmatched",
        category=category,
        subcategory=subcategory,
        currency=currency,
        amount=amount,
        purchase_date=purchase_date or date.today(),
        order_name=order_name,
        screenshot_path="/tmp/test.png",
        screenshot_original_name="test.png",
        screenshot_mime_type="image/png",
        screenshot_size=1234,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _create_confirmed_match(
    db: Session,
    *,
    owner_id: uuid.UUID,
    purchase_record_id: uuid.UUID,
    invoice_file_id: uuid.UUID,
) -> InvoiceMatch:
    match = InvoiceMatch(
        owner_id=owner_id,
        purchase_record_id=purchase_record_id,
        invoice_file_id=invoice_file_id,
        status=MATCH_STATUS_CONFIRMED,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


def _make_eligible_chain(
    db: Session,
    *,
    owner_id: uuid.UUID,
    status: str = STATUS_APPROVED,
    category: str = CATEGORY_TRANSPORTATION,
    subcategory: str | None = None,
    currency: str = "CNY",
    amount: Decimal = Decimal("100.00"),
    purchase_date: date | None = None,
    order_name: str = "test order",
    invoice_status: str = "confirmed",
    invoice_deleted_at: datetime | None = None,
) -> tuple[PurchaseRecord, InvoiceFile, InvoiceMatch]:
    """Create the full eligible chain: PurchaseRecord -> InvoiceMatch -> InvoiceFile."""
    record = _create_purchase_record(
        db,
        owner_id=owner_id,
        status=status,
        category=category,
        subcategory=subcategory,
        currency=currency,
        amount=amount,
        purchase_date=purchase_date,
        order_name=order_name,
    )
    inv = _create_invoice_file(
        db,
        owner_id=owner_id,
        status=invoice_status,
        deleted_at=invoice_deleted_at,
    )
    match = _create_confirmed_match(
        db,
        owner_id=owner_id,
        purchase_record_id=record.id,
        invoice_file_id=inv.id,
    )
    return record, inv, match


# =============================================================================
# Permission Tests
# =============================================================================

def test_records_normal_user_forbidden(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/finance/reimbursement-exports/records", headers=normal_user_token_headers)
    assert response.status_code == 403


def test_generate_normal_user_forbidden(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={},
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


def test_history_normal_user_forbidden(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/finance/reimbursement-exports/history", headers=normal_user_token_headers)
    assert response.status_code == 403


def test_read_export_normal_user_forbidden(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    response = client.get(
        f"/api/v1/finance/reimbursement-exports/{uuid.uuid4()}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


def test_download_export_normal_user_forbidden(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    response = client.get(
        f"/api/v1/finance/reimbursement-exports/{uuid.uuid4()}/download",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


def test_settings_read_normal_user_forbidden(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/finance/reimbursement-exports/settings", headers=normal_user_token_headers)
    assert response.status_code == 403


def test_settings_update_normal_user_forbidden(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    response = client.put(
        "/api/v1/finance/reimbursement-exports/settings",
        json={"retention_days": 7},
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


def test_purge_expired_normal_user_forbidden(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/finance/reimbursement-exports/purge-expired-files",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


# =============================================================================
# GET /records
# =============================================================================

def test_records_empty(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    response = client.get("/api/v1/finance/reimbursement-exports/records", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["count"], int)
    assert isinstance(data["data"], list)
    # Draft must not appear
    assert not any(r["status"] == STATUS_DRAFT for r in data["data"])


def test_records_filter_by_category(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    _make_eligible_chain(db, owner_id=user.id, category=CATEGORY_TRANSPORTATION)
    _make_eligible_chain(db, owner_id=user.id, category=CATEGORY_VEHICLE)
    response = client.get(
        "/api/v1/finance/reimbursement-exports/records",
        headers=headers,
        params={"category": CATEGORY_TRANSPORTATION},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["category"] == CATEGORY_TRANSPORTATION


def test_records_draft_not_included(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    # Draft purchase record should not appear even with match
    _make_eligible_chain(db, owner_id=user.id, status=STATUS_DRAFT)
    response = client.get("/api/v1/finance/reimbursement-exports/records", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert not any(r["status"] == STATUS_DRAFT for r in data["data"])


def test_records_confirmed_match_included(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, inv, _match = _make_eligible_chain(db, owner_id=user.id, status=STATUS_APPROVED)
    response = client.get("/api/v1/finance/reimbursement-exports/records", headers=headers)
    assert response.status_code == 200
    data = response.json()
    record_ids = [r["id"] for r in data["data"]]
    assert str(record.id) in record_ids
    # Should include invoice_file brief
    found = next(r for r in data["data"] if r["id"] == str(record.id))
    assert found["invoice_file"] is not None
    assert found["invoice_file"]["invoice_number"].startswith("INV-")


def test_records_invoice_file_voided_not_included(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, _inv, _match = _make_eligible_chain(
        db, owner_id=user.id, invoice_status="voided", order_name="voided_test"
    )
    response = client.get("/api/v1/finance/reimbursement-exports/records", headers=headers)
    assert response.status_code == 200
    data = response.json()
    record_ids = [r["id"] for r in data["data"]]
    assert str(record.id) not in record_ids


def test_records_invoice_file_deleted_not_included(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, _inv, _match = _make_eligible_chain(
        db,
        owner_id=user.id,
        invoice_deleted_at=datetime.now(timezone.utc),
        order_name="deleted_test",
    )
    response = client.get("/api/v1/finance/reimbursement-exports/records", headers=headers)
    assert response.status_code == 200
    data = response.json()
    record_ids = [r["id"] for r in data["data"]]
    assert str(record.id) not in record_ids


def test_records_exported_filter(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, _inv, _match = _make_eligible_chain(db, owner_id=user.id, order_name="exported_filter_test")
    # Generate export
    client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(record.id)], "retention_days": 7},
        headers=headers,
    )
    # exported=yes
    response = client.get(
        "/api/v1/finance/reimbursement-exports/records",
        headers=headers,
        params={"exported": "exported"},
    )
    assert response.status_code == 200
    data = response.json()
    exported_ids = [r["id"] for r in data["data"] if r["exported"]]
    assert str(record.id) in exported_ids
    found = next(r for r in data["data"] if r["id"] == str(record.id))
    assert found["latest_exported_at"] is not None

    # not_exported
    record2, _inv2, _match2 = _make_eligible_chain(db, owner_id=user.id, order_name="not_exported_test")
    response = client.get(
        "/api/v1/finance/reimbursement-exports/records",
        headers=headers,
        params={"exported": "not_exported"},
    )
    assert response.status_code == 200
    data = response.json()
    not_exported_ids = [r["id"] for r in data["data"] if not r["exported"]]
    assert str(record2.id) in not_exported_ids


def test_records_q_filter(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    _make_eligible_chain(db, owner_id=user.id, order_name="alpha order")
    _make_eligible_chain(db, owner_id=user.id, order_name="beta order")
    response = client.get(
        "/api/v1/finance/reimbursement-exports/records",
        headers=headers,
        params={"q": "alpha"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["order_name"] == "alpha order"


# =============================================================================
# POST /generate
# =============================================================================

def test_generate_no_records_422(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    response = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(uuid.uuid4())]},
        headers=headers,
    )
    assert response.status_code == 422


def test_generate_empty_ids_422(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    response = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": []},
        headers=headers,
    )
    assert response.status_code == 422


def test_generate_by_ids_success(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, _inv, _match = _make_eligible_chain(db, owner_id=user.id)
    response = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={
            "purchase_record_ids": [str(record.id)],
            "retention_days": 7,
            "department": "Tech Dept",
            "business_unit": "BU-1",
            "reimburser": "Alice",
            "reimbursement_date": "2025-06-01",
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["department"] == "Tech Dept"
    assert data["business_unit"] == "BU-1"
    assert data["reimburser"] == "Alice"
    assert data["reimbursement_date"] == "2025-06-01"
    assert data["currency"] == "CNY"
    assert data["total_amount"] == "100.00"
    assert data["item_count"] == 1
    assert data["file_size"] > 0
    assert data["file_expires_at"] is not None


def test_generate_multi_currency_rejected(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    r1, _inv1, _match1 = _make_eligible_chain(db, owner_id=user.id, currency="CNY")
    r2, _inv2, _match2 = _make_eligible_chain(db, owner_id=user.id, currency="USD")
    response = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(r1.id), str(r2.id)], "retention_days": 7},
        headers=headers,
    )
    assert response.status_code == 422
    assert "currency" in response.json()["detail"].lower() or "Multiple" in response.json()["detail"]


def test_generate_invalid_retention_low(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, _inv, _match = _make_eligible_chain(db, owner_id=user.id)
    response = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(record.id)], "retention_days": 0},
        headers=headers,
    )
    assert response.status_code == 422


def test_generate_invalid_retention_high(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, _inv, _match = _make_eligible_chain(db, owner_id=user.id)
    response = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(record.id)], "retention_days": 366},
        headers=headers,
    )
    assert response.status_code == 422


# =============================================================================
# GET /history
# =============================================================================

def test_history_empty(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    response = client.get("/api/v1/finance/reimbursement-exports/history", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["count"], int)
    assert isinstance(data["data"], list)


def test_history_after_generate(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, _inv, _match = _make_eligible_chain(db, owner_id=user.id)
    client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(record.id)], "retention_days": 7},
        headers=headers,
    )
    response = client.get("/api/v1/finance/reimbursement-exports/history", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert data["data"][-1]["item_count"] == 1


# =============================================================================
# GET /{id}
# =============================================================================

def test_read_export_not_found(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    response = client.get(
        f"/api/v1/finance/reimbursement-exports/{uuid.uuid4()}",
        headers=headers,
    )
    assert response.status_code == 404


def test_read_export_with_items(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, _inv, _match = _make_eligible_chain(db, owner_id=user.id)
    gen_resp = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(record.id)], "retention_days": 7},
        headers=headers,
    )
    export_id = gen_resp.json()["id"]
    response = client.get(
        f"/api/v1/finance/reimbursement-exports/{export_id}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["document_number"] == 1
    assert data["items"][0]["purchase_record_id"] == str(record.id)


# =============================================================================
# Document Numbering (category order)
# =============================================================================

def test_doc_numbering_category_order(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    # Create records in reverse category order
    r_vehicle, _inv_v, _match_v = _make_eligible_chain(
        db, owner_id=user.id, category=CATEGORY_VEHICLE, purchase_date=date(2025, 1, 1)
    )
    r_transport, _inv_t, _match_t = _make_eligible_chain(
        db, owner_id=user.id, category=CATEGORY_TRANSPORTATION, purchase_date=date(2025, 1, 2)
    )
    r_meals, _inv_m, _match_m = _make_eligible_chain(
        db, owner_id=user.id, category=CATEGORY_MEALS_ENTERTAINMENT, purchase_date=date(2025, 1, 3)
    )
    gen_resp = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={
            "purchase_record_ids": [str(r_vehicle.id), str(r_transport.id), str(r_meals.id)],
            "retention_days": 7,
        },
        headers=headers,
    )
    assert gen_resp.status_code == 200
    export_id = gen_resp.json()["id"]
    export_resp = client.get(
        f"/api/v1/finance/reimbursement-exports/{export_id}",
        headers=headers,
    )
    data = export_resp.json()
    items = data["items"]
    assert len(items) == 3
    # Category order: transportation(1), meals_entertainment(2), vehicle(3)
    categories = [i["category"] for i in items]
    assert categories == [CATEGORY_TRANSPORTATION, CATEGORY_MEALS_ENTERTAINMENT, CATEGORY_VEHICLE]
    doc_numbers = [i["document_number"] for i in items]
    assert doc_numbers == [1, 2, 3]


def test_doc_numbering_same_category_by_date(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    r1, _inv1, _match1 = _make_eligible_chain(
        db, owner_id=user.id, category=CATEGORY_TRANSPORTATION, purchase_date=date(2025, 2, 2)
    )
    r2, _inv2, _match2 = _make_eligible_chain(
        db, owner_id=user.id, category=CATEGORY_TRANSPORTATION, purchase_date=date(2025, 2, 1)
    )
    gen_resp = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(r1.id), str(r2.id)], "retention_days": 7},
        headers=headers,
    )
    export_id = gen_resp.json()["id"]
    export_resp = client.get(f"/api/v1/finance/reimbursement-exports/{export_id}", headers=headers)
    items = export_resp.json()["items"]
    # Earlier purchase_date should be doc_number 1
    assert items[0]["purchase_record_id"] == str(r2.id)
    assert items[0]["document_number"] == 1
    assert items[1]["purchase_record_id"] == str(r1.id)
    assert items[1]["document_number"] == 2


# =============================================================================
# GET /{id}/download
# =============================================================================

def test_download_export_success(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, _inv, _match = _make_eligible_chain(db, owner_id=user.id)
    gen_resp = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(record.id)], "retention_days": 7},
        headers=headers,
    )
    export_id = gen_resp.json()["id"]
    response = client.get(
        f"/api/v1/finance/reimbursement-exports/{export_id}/download",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_download_export_not_found(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    response = client.get(
        f"/api/v1/finance/reimbursement-exports/{uuid.uuid4()}/download",
        headers=headers,
    )
    assert response.status_code == 404


def test_download_export_purged_gone(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, _inv, _match = _make_eligible_chain(db, owner_id=user.id)
    gen_resp = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(record.id)], "retention_days": 7},
        headers=headers,
    )
    export_id = gen_resp.json()["id"]
    # Manually mark file_deleted_at
    export = db.get(ReimbursementExport, export_id)
    assert export is not None
    export.file_deleted_at = datetime.now(timezone.utc)
    db.add(export)
    db.commit()
    response = client.get(
        f"/api/v1/finance/reimbursement-exports/{export_id}/download",
        headers=headers,
    )
    assert response.status_code == 410


def test_download_export_expired_gone(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, _inv, _match = _make_eligible_chain(db, owner_id=user.id)
    gen_resp = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(record.id)], "retention_days": 7},
        headers=headers,
    )
    export_id = gen_resp.json()["id"]
    # Manually set file_expires_at to the past (simulate expiration without purge)
    export = db.get(ReimbursementExport, export_id)
    assert export is not None
    export.file_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.add(export)
    db.commit()
    # Download should return 410
    response = client.get(
        f"/api/v1/finance/reimbursement-exports/{export_id}/download",
        headers=headers,
    )
    assert response.status_code == 410
    # History detail should still be readable
    detail_resp = client.get(
        f"/api/v1/finance/reimbursement-exports/{export_id}",
        headers=headers,
    )
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == str(export_id)
    # Clean up: mark file_deleted so purge_no_expired isn't affected by this row
    export = db.get(ReimbursementExport, export_id)
    assert export is not None
    export.file_deleted_at = datetime.now(timezone.utc)
    db.add(export)
    db.commit()


# =============================================================================
# Settings
# =============================================================================

def test_settings_read_default(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    response = client.get("/api/v1/finance/reimbursement-exports/settings", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["retention_days"] == DEFAULT_RETENTION_DAYS


def test_settings_update_retention(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    response = client.put(
        "/api/v1/finance/reimbursement-exports/settings",
        json={"retention_days": 7},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["retention_days"] == 7


def test_settings_update_invalid_retention_low(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    response = client.put(
        "/api/v1/finance/reimbursement-exports/settings",
        json={"retention_days": 0},
        headers=headers,
    )
    assert response.status_code == 422


def test_settings_update_invalid_retention_high(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    response = client.put(
        "/api/v1/finance/reimbursement-exports/settings",
        json={"retention_days": 366},
        headers=headers,
    )
    assert response.status_code == 422


# =============================================================================
# Purge Expired
# =============================================================================

def test_purge_no_expired(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    response = client.post(
        "/api/v1/finance/reimbursement-exports/purge-expired-files",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["purged_count"] == 0


def test_purge_expired(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, _inv, _match = _make_eligible_chain(db, owner_id=user.id)
    gen_resp = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(record.id)], "retention_days": 1},
        headers=headers,
    )
    export_id = gen_resp.json()["id"]
    export = db.get(ReimbursementExport, export_id)
    assert export is not None
    export.file_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.add(export)
    db.commit()
    response = client.post(
        "/api/v1/finance/reimbursement-exports/purge-expired-files",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["purged_count"] == 1
    assert export_id in data["purged_ids"]
    # History record should still exist
    export_after = db.get(ReimbursementExport, export_id)
    assert export_after is not None
    assert export_after.file_deleted_at is not None


def test_purge_only_deletes_physical_file_not_history(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, _inv, _match = _make_eligible_chain(db, owner_id=user.id)
    gen_resp = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(record.id)], "retention_days": 1},
        headers=headers,
    )
    export_id = gen_resp.json()["id"]
    export = db.get(ReimbursementExport, export_id)
    assert export is not None
    export.file_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.add(export)
    db.commit()
    client.post(
        "/api/v1/finance/reimbursement-exports/purge-expired-files",
        headers=headers,
    )
    # Export history and items should still exist
    export_after = db.get(ReimbursementExport, export_id)
    assert export_after is not None
    items = db.exec(
        select(ReimbursementExportItem).where(ReimbursementExportItem.export_id == export_id)
    ).all()
    assert len(items) == 1


# =============================================================================
# File Retention / Expiry
# =============================================================================

def test_file_expires_at_correct(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, _inv, _match = _make_eligible_chain(db, owner_id=user.id)
    gen_resp = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(record.id)], "retention_days": 7},
        headers=headers,
    )
    data = gen_resp.json()
    expires_str = data["file_expires_at"].replace("Z", "+00:00")
    expires = datetime.fromisoformat(expires_str)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    assert (expires - now).days >= 6


# =============================================================================
# Unauthenticated Tests
# =============================================================================

def test_records_unauthenticated(client: TestClient) -> None:
    response = client.get("/api/v1/finance/reimbursement-exports/records")
    assert response.status_code == 401


def test_generate_unauthenticated(client: TestClient) -> None:
    response = client.post("/api/v1/finance/reimbursement-exports/generate", json={})
    assert response.status_code == 401


def test_history_unauthenticated(client: TestClient) -> None:
    response = client.get("/api/v1/finance/reimbursement-exports/history")
    assert response.status_code == 401


def test_settings_read_unauthenticated(client: TestClient) -> None:
    response = client.get("/api/v1/finance/reimbursement-exports/settings")
    assert response.status_code == 401


def test_purge_expired_unauthenticated(client: TestClient) -> None:
    response = client.post("/api/v1/finance/reimbursement-exports/purge-expired-files")
    assert response.status_code == 401


# =============================================================================
# Contract Guard Tests (no business logic changes)
# =============================================================================

def test_generate_rejects_old_record_ids_field(client: TestClient, db: Session) -> None:
    """Old field 'record_ids' must not be accepted as the primary contract."""
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, _inv, _match = _make_eligible_chain(db, owner_id=user.id)
    response = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"record_ids": [str(record.id)], "retention_days": 7},
        headers=headers,
    )
    assert response.status_code == 422


def test_records_exported_all_value(client: TestClient, db: Session) -> None:
    """exported=all must be accepted and return records regardless of export status."""
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    _make_eligible_chain(db, owner_id=user.id)
    response = client.get(
        "/api/v1/finance/reimbursement-exports/records",
        headers=headers,
        params={"exported": "all"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1


def test_records_exported_invalid_value_422(client: TestClient, db: Session) -> None:
    """exported must reject values outside all/exported/not_exported."""
    headers = _superuser_headers(client, db)
    response = client.get(
        "/api/v1/finance/reimbursement-exports/records",
        headers=headers,
        params={"exported": "invalid_value"},
    )
    assert response.status_code == 422


def test_records_invalid_start_date_format_422(client: TestClient, db: Session) -> None:
    """start_date must reject non-ISO date strings."""
    headers = _superuser_headers(client, db)
    response = client.get(
        "/api/v1/finance/reimbursement-exports/records",
        headers=headers,
        params={"start_date": "not-a-date"},
    )
    assert response.status_code == 422


def test_records_invalid_end_date_format_422(client: TestClient, db: Session) -> None:
    """end_date must reject non-ISO date strings."""
    headers = _superuser_headers(client, db)
    response = client.get(
        "/api/v1/finance/reimbursement-exports/records",
        headers=headers,
        params={"end_date": "2025/06/01"},
    )
    assert response.status_code == 422


def test_download_export_physical_file_missing_410(client: TestClient, db: Session) -> None:
    """Download must return 410 when the physical file no longer exists."""
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    record, _inv, _match = _make_eligible_chain(db, owner_id=user.id)
    gen_resp = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(record.id)], "retention_days": 7},
        headers=headers,
    )
    export_id = gen_resp.json()["id"]
    export = db.get(ReimbursementExport, export_id)
    assert export is not None
    # Point file_path to a non-existent file
    export.file_path = "/tmp/nonexistent_reimbursement_export.xlsx"
    db.add(export)
    db.commit()
    response = client.get(
        f"/api/v1/finance/reimbursement-exports/{export_id}/download",
        headers=headers,
    )
    assert response.status_code == 410
    # Clean up so purge tests are not affected
    export = db.get(ReimbursementExport, export_id)
    assert export is not None
    export.file_deleted_at = datetime.now(timezone.utc)
    db.add(export)
    db.commit()


def test_settings_update_persists_metadata(client: TestClient, db: Session) -> None:
    """PUT /settings must write value_type='int', non-empty description, and updated_by_id."""
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    response = client.put(
        "/api/v1/finance/reimbursement-exports/settings",
        json={"retention_days": 14},
        headers=headers,
    )
    assert response.status_code == 200
    # Verify the underlying AppSetting row
    setting = db.get(AppSetting, SETTING_RETENTION_DAYS)
    assert setting is not None
    assert setting.value == "14"
    assert setting.value_type == "int"
    assert setting.description is not None and len(setting.description) > 0
    assert setting.updated_by_id == user.id


# =============================================================================
# BE-R008-FIX-002: settings-driven retention_days fallback
# =============================================================================

def test_generate_uses_settings_retention_when_omitted(client: TestClient, db: Session) -> None:
    """If POST /generate omits retention_days, fall back to /settings retention_days."""
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None

    # Set platform setting to 14 days
    put_resp = client.put(
        "/api/v1/finance/reimbursement-exports/settings",
        json={"retention_days": 14},
        headers=headers,
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["retention_days"] == 14

    record, _inv, _match = _make_eligible_chain(db, owner_id=user.id, order_name="settings_fallback_test")

    # Generate without retention_days in body
    gen_resp = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(record.id)]},
        headers=headers,
    )
    assert gen_resp.status_code == 200
    data = gen_resp.json()
    expires_str = data["file_expires_at"].replace("Z", "+00:00")
    expires = datetime.fromisoformat(expires_str)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta_days = (expires - now).total_seconds() / 86400
    # Should be ~14 days, not 1 (DEFAULT_RETENTION_DAYS) and not the previously-set 7
    assert 13.0 < delta_days < 14.5, f"Expected ~14 days retention, got {delta_days:.2f}"


def test_generate_explicit_retention_days_overrides_settings(client: TestClient, db: Session) -> None:
    """If POST /generate sends retention_days, use that value, ignoring the platform setting."""
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None

    # Set platform setting to 30 days
    client.put(
        "/api/v1/finance/reimbursement-exports/settings",
        json={"retention_days": 30},
        headers=headers,
    )

    record, _inv, _match = _make_eligible_chain(db, owner_id=user.id, order_name="explicit_retention_test")
    # Override per-export with retention_days=3
    gen_resp = client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(record.id)], "retention_days": 3},
        headers=headers,
    )
    assert gen_resp.status_code == 200
    data = gen_resp.json()
    expires_str = data["file_expires_at"].replace("Z", "+00:00")
    expires = datetime.fromisoformat(expires_str)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta_days = (expires - now).total_seconds() / 86400
    # Override wins: ~3 days, not 30
    assert 2.0 < delta_days < 3.5, f"Expected ~3 days retention from override, got {delta_days:.2f}"


# =============================================================================
# BE-R008-FIX-002: GET /records count vs data consistency under exported filter
# =============================================================================

def test_records_exported_count_matches_data(client: TestClient, db: Session) -> None:
    """count must reflect the filtered total when exported=exported is applied."""
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None

    # Use a unique q-substring to fence the test off from other suites' data
    fence = "rxc-unique-fence-001"
    r1, _i1, _m1 = _make_eligible_chain(db, owner_id=user.id, order_name=f"{fence} alpha")
    r2, _i2, _m2 = _make_eligible_chain(db, owner_id=user.id, order_name=f"{fence} bravo")
    r3, _i3, _m3 = _make_eligible_chain(db, owner_id=user.id, order_name=f"{fence} charlie")

    # Export r1 and r2; leave r3 unexported
    client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(r1.id), str(r2.id)], "retention_days": 7},
        headers=headers,
    )

    # exported=exported -> count must equal len(data) and equal 2
    resp = client.get(
        "/api/v1/finance/reimbursement-exports/records",
        headers=headers,
        params={"q": fence, "exported": "exported"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == len(body["data"])
    assert body["count"] == 2
    ids = {r["id"] for r in body["data"]}
    assert ids == {str(r1.id), str(r2.id)}

    # exported=not_exported -> count must equal len(data) and equal 1
    resp = client.get(
        "/api/v1/finance/reimbursement-exports/records",
        headers=headers,
        params={"q": fence, "exported": "not_exported"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == len(body["data"])
    assert body["count"] == 1
    assert body["data"][0]["id"] == str(r3.id)


def test_records_exported_pagination_consistent_with_count(client: TestClient, db: Session) -> None:
    """When the filtered total exceeds the page size, count must still be the filtered total."""
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None

    fence = "rxc-pagination-fence-002"
    records = []
    for i in range(3):
        rec, _inv, _match = _make_eligible_chain(
            db, owner_id=user.id, order_name=f"{fence} item-{i}"
        )
        records.append(rec)
    # Export all three
    client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={
            "purchase_record_ids": [str(r.id) for r in records],
            "retention_days": 7,
        },
        headers=headers,
    )

    # Page size 2 -> count should still be 3
    resp = client.get(
        "/api/v1/finance/reimbursement-exports/records",
        headers=headers,
        params={"q": fence, "exported": "exported", "skip": 0, "limit": 2},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 3
    assert len(body["data"]) == 2

    # Next page picks up the rest
    resp2 = client.get(
        "/api/v1/finance/reimbursement-exports/records",
        headers=headers,
        params={"q": fence, "exported": "exported", "skip": 2, "limit": 2},
    )
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2["count"] == 3
    assert len(body2["data"]) == 1


# =============================================================================
# BE-R008-FIX-002: GET /history filter parameters
# =============================================================================

def test_history_filter_by_currency(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None

    cny_record, _i1, _m1 = _make_eligible_chain(
        db, owner_id=user.id, currency="CNY", order_name="hist_currency_cny"
    )
    usd_record, _i2, _m2 = _make_eligible_chain(
        db, owner_id=user.id, currency="USD", order_name="hist_currency_usd"
    )
    client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(cny_record.id)], "retention_days": 7},
        headers=headers,
    )
    client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(usd_record.id)], "retention_days": 7},
        headers=headers,
    )

    resp = client.get(
        "/api/v1/finance/reimbursement-exports/history",
        headers=headers,
        params={"currency": "USD"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    # All returned exports must have currency=USD
    assert all(e["currency"] == "USD" for e in data["data"])


def test_history_filter_by_created_by_id(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None

    record, _inv, _match = _make_eligible_chain(
        db, owner_id=user.id, order_name="hist_created_by_test"
    )
    client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(record.id)], "retention_days": 7},
        headers=headers,
    )

    resp = client.get(
        "/api/v1/finance/reimbursement-exports/history",
        headers=headers,
        params={"created_by_id": str(user.id)},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    assert all(e["created_by_id"] == str(user.id) for e in data["data"])

    # An unrelated UUID should yield zero
    other_id = uuid.uuid4()
    resp_empty = client.get(
        "/api/v1/finance/reimbursement-exports/history",
        headers=headers,
        params={"created_by_id": str(other_id)},
    )
    assert resp_empty.status_code == 200
    assert resp_empty.json()["count"] == 0


def test_history_filter_by_created_at_range(client: TestClient, db: Session) -> None:
    headers = _superuser_headers(client, db)
    from app import crud
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None

    record, _inv, _match = _make_eligible_chain(
        db, owner_id=user.id, order_name="hist_created_at_range"
    )
    before = datetime.now(timezone.utc) - timedelta(minutes=1)
    client.post(
        "/api/v1/finance/reimbursement-exports/generate",
        json={"purchase_record_ids": [str(record.id)], "retention_days": 7},
        headers=headers,
    )
    after = datetime.now(timezone.utc) + timedelta(minutes=1)

    # created_at_from in the past -> at least 1 result
    resp = client.get(
        "/api/v1/finance/reimbursement-exports/history",
        headers=headers,
        params={"created_at_from": before.isoformat()},
    )
    assert resp.status_code == 200
    assert resp.json()["count"] >= 1

    # created_at_from in the future -> 0
    far_future = datetime.now(timezone.utc) + timedelta(days=30)
    resp_future = client.get(
        "/api/v1/finance/reimbursement-exports/history",
        headers=headers,
        params={"created_at_from": far_future.isoformat()},
    )
    assert resp_future.status_code == 200
    assert resp_future.json()["count"] == 0

    # created_at_to before the export -> exclude this row
    far_past = datetime.now(timezone.utc) - timedelta(days=30)
    resp_past = client.get(
        "/api/v1/finance/reimbursement-exports/history",
        headers=headers,
        params={"created_at_to": far_past.isoformat()},
    )
    assert resp_past.status_code == 200
    # All returned rows (if any) must be on/before far_past
    for row in resp_past.json()["data"]:
        row_at = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
        if row_at.tzinfo is None:
            row_at = row_at.replace(tzinfo=timezone.utc)
        assert row_at <= far_past

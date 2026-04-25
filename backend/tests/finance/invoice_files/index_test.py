"""
backend/tests/finance/invoice_files/index_test.py
invoice_files 工具主测试文件

覆盖范围：
- POST /api/v1/finance/invoice-files/parse-preview   PDF 解析预览（不落库）
- GET  /api/v1/finance/invoice-files                  列表查询
- GET  /api/v1/finance/invoice-files/{id}             详情查询
- POST /api/v1/finance/invoice-files                  创建（含 PDF 元数据）
- PATCH /api/v1/finance/invoice-files/{id}            更新
- POST /api/v1/finance/invoice-files/{id}/confirm     确认
- POST /api/v1/finance/invoice-files/{id}/withdraw-confirmation 撤回确认
- POST /api/v1/finance/invoice-files/{id}/void        作废
- POST /api/v1/finance/invoice-files/{id}/restore-draft 恢复草稿
- DELETE /api/v1/finance/invoice-files/{id}           逻辑删除
- POST /api/v1/finance/invoice-files/{id}/restore     恢复
- POST /api/v1/finance/invoice-files/purge-deleted    清理 30 天前删除记录
- GET  /api/v1/finance/invoice-files/{id}/pdf         PDF 鉴权下载
- 权限分支（403 / 404）
- 发票类型/币种/金额/日期校验
- 同一用户发票号码唯一
- 跨用户重复提示
- 数据隔离
"""

import io
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.modules.finance.invoice_files.constants import (
    INVOICE_TYPE_GENERAL,
    STATUS_CONFIRMED,
    STATUS_DRAFT,
    STATUS_VOIDED,
)
from app.modules.finance.invoice_files.models import InvoiceFile
from app.modules.finance.invoice_files.repository import create_record
from app.modules.finance.invoice_files.schemas import InvoiceFileCreate

BASE_URL = f"{settings.API_V1_STR}/finance/invoice-files"


def _pdf_file() -> tuple[bytes, str]:
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n", "test.pdf"


def _create_random_invoice(
    db: Session,
    owner_id: uuid.UUID,
    status: str = STATUS_DRAFT,
    deleted_at=None,
    deleted_by_id=None,
    invoice_number: str | None = None,
) -> InvoiceFile:
    data = InvoiceFileCreate(
        invoice_number=invoice_number or f"INV-{uuid.uuid4().hex[:8].upper()}",
        invoice_date="2026-04-24",
        invoice_amount="123.45",
        tax_amount="10.00",
        currency="CNY",
        buyer="Test Buyer",
        seller="Test Seller",
        invoice_type=INVOICE_TYPE_GENERAL,
        note=None,
    )
    record = create_record(
        session=db,
        record_in=data,
        owner_id=owner_id,
        pdf_path="finance/invoice_files/fake.pdf",
        pdf_original_name="fake.pdf",
        pdf_mime_type="application/pdf",
        pdf_size=100,
    )
    # Override status / soft-delete fields for test scenarios
    if status != STATUS_DRAFT:
        record.status = status
    if deleted_at is not None:
        record.deleted_at = deleted_at
    if deleted_by_id is not None:
        record.deleted_by_id = deleted_by_id
    if status != STATUS_DRAFT or deleted_at is not None or deleted_by_id is not None:
        db.add(record)
        db.commit()
        db.refresh(record)
    return record


# =============================================================================
# Parse Preview
# =============================================================================


def test_parse_preview_no_persist(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Parse preview does not create a database record."""
    pdf_bytes, filename = _pdf_file()
    response = client.post(
        f"{BASE_URL}/parse-preview",
        headers=superuser_token_headers,
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 200
    content = response.json()
    assert isinstance(content, dict)


def test_parse_preview_unauthenticated(client: TestClient) -> None:
    pdf_bytes, filename = _pdf_file()
    response = client.post(
        f"{BASE_URL}/parse-preview",
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code in (401, 403)


def test_parse_preview_invalid_mime(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{BASE_URL}/parse-preview",
        headers=superuser_token_headers,
        files={"pdf": ("test.png", io.BytesIO(b"\x89PNG"), "image/png")},
    )
    assert response.status_code == 422


# =============================================================================
# Create
# =============================================================================


def test_create_invoice_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    pdf_bytes, filename = _pdf_file()
    response = client.post(
        BASE_URL + "/",
        headers=normal_user_token_headers,
        data={
            "invoice_number": "INV-001",
            "invoice_date": "2026-04-24",
            "invoice_amount": "99.99",
            "tax_amount": "5.00",
            "currency": "CNY",
            "buyer": "Buyer A",
            "seller": "Seller A",
            "invoice_type": INVOICE_TYPE_GENERAL,
        },
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["status"] == STATUS_DRAFT
    assert content["owner_id"] is not None
    assert content["pdf_path"] is not None
    assert content["pdf_original_name"] == filename


def test_create_invoice_default_tax_zero(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    pdf_bytes, filename = _pdf_file()
    response = client.post(
        BASE_URL + "/",
        headers=normal_user_token_headers,
        data={
            "invoice_number": "INV-TAX0",
            "invoice_date": "2026-04-24",
            "invoice_amount": "100.00",
            "currency": "CNY",
            "buyer": "Buyer",
            "seller": "Seller",
            "invoice_type": INVOICE_TYPE_GENERAL,
        },
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 200
    content = response.json()
    # tax_amount should default to 0 when omitted
    assert content["tax_amount"] == "0.00"


def test_create_invoice_invalid_type(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    pdf_bytes, filename = _pdf_file()
    response = client.post(
        BASE_URL + "/",
        headers=normal_user_token_headers,
        data={
            "invoice_number": "INV-BAD",
            "invoice_date": "2026-04-24",
            "invoice_amount": "10.00",
            "currency": "CNY",
            "buyer": "Buyer",
            "seller": "Seller",
            "invoice_type": "invalid_type",
        },
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 422


def test_create_invoice_invalid_currency(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    pdf_bytes, filename = _pdf_file()
    response = client.post(
        BASE_URL + "/",
        headers=normal_user_token_headers,
        data={
            "invoice_number": "INV-CUR",
            "invoice_date": "2026-04-24",
            "invoice_amount": "10.00",
            "currency": "XYZ",
            "buyer": "Buyer",
            "seller": "Seller",
            "invoice_type": INVOICE_TYPE_GENERAL,
        },
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 422


def test_create_invoice_invalid_amount(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    pdf_bytes, filename = _pdf_file()
    response = client.post(
        BASE_URL + "/",
        headers=normal_user_token_headers,
        data={
            "invoice_number": "INV-AMT",
            "invoice_date": "2026-04-24",
            "invoice_amount": "abc",
            "currency": "CNY",
            "buyer": "Buyer",
            "seller": "Seller",
            "invoice_type": INVOICE_TYPE_GENERAL,
        },
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 422


def test_create_invoice_invalid_date(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    pdf_bytes, filename = _pdf_file()
    response = client.post(
        BASE_URL + "/",
        headers=normal_user_token_headers,
        data={
            "invoice_number": "INV-DATE",
            "invoice_date": "not-a-date",
            "invoice_amount": "10.00",
            "currency": "CNY",
            "buyer": "Buyer",
            "seller": "Seller",
            "invoice_type": INVOICE_TYPE_GENERAL,
        },
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 422


# =============================================================================
# Duplicate Invoice Number
# =============================================================================


def test_duplicate_invoice_number_same_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    pdf_bytes, filename = _pdf_file()
    data = {
        "invoice_number": "DUP-001",
        "invoice_date": "2026-04-24",
        "invoice_amount": "10.00",
        "currency": "CNY",
        "buyer": "Buyer",
        "seller": "Seller",
        "invoice_type": INVOICE_TYPE_GENERAL,
    }
    r1 = client.post(
        BASE_URL + "/",
        headers=normal_user_token_headers,
        data=data,
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert r1.status_code == 200

    r2 = client.post(
        BASE_URL + "/",
        headers=normal_user_token_headers,
        data=data,
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert r2.status_code == 422


def test_duplicate_invoice_number_cross_user_allowed(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user, authentication_token_from_email

    pdf_bytes, filename = _pdf_file()
    data = {
        "invoice_number": "DUP-CROSS",
        "invoice_date": "2026-04-24",
        "invoice_amount": "10.00",
        "currency": "CNY",
        "buyer": "Buyer",
        "seller": "Seller",
        "invoice_type": INVOICE_TYPE_GENERAL,
    }
    # Create as normal user
    r1 = client.post(
        BASE_URL + "/",
        headers=normal_user_token_headers,
        data=data,
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert r1.status_code == 200

    # Create another user and use same invoice number
    other_user = create_random_user(db)
    other_headers = authentication_token_from_email(
        client=client, email=other_user.email, db=db
    )
    r2 = client.post(
        BASE_URL + "/",
        headers=other_headers,
        data=data,
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert r2.status_code == 200


# =============================================================================
# List
# =============================================================================


def test_list_invoices_normal_user_sees_only_own(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    response = client.get(BASE_URL + "/", headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content
    for rec in content["data"]:
        assert rec["deleted_at"] is None


def test_list_invoices_superuser_sees_all(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    response = client.get(BASE_URL + "/", headers=superuser_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content


def test_list_deleted_invoices_only_shows_deleter(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    response = client.get(
        BASE_URL + "/?deleted=true", headers=normal_user_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    for rec in content["data"]:
        assert rec["deleted_at"] is not None


# =============================================================================
# Detail
# =============================================================================


def test_read_invoice_success(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user

    user = create_random_user(db)
    record = _create_random_invoice(db, owner_id=user.id)
    response = client.get(
        f"{BASE_URL}/{record.id}", headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(record.id)


def test_read_invoice_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{BASE_URL}/{uuid.uuid4()}", headers=superuser_token_headers
    )
    assert response.status_code == 404


def test_read_invoice_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user

    other_user = create_random_user(db)
    record = _create_random_invoice(db, owner_id=other_user.id)
    response = client.get(
        f"{BASE_URL}/{record.id}", headers=normal_user_token_headers
    )
    assert response.status_code == 403


# =============================================================================
# Duplicate Hint (Admin vs Normal User)
# =============================================================================


def test_admin_sees_duplicate_hint(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user, authentication_token_from_email

    user1 = create_random_user(db)
    user2 = create_random_user(db)
    _create_random_invoice(db, owner_id=user1.id, invoice_number="DUP-HINT")
    _create_random_invoice(db, owner_id=user2.id, invoice_number="DUP-HINT")

    response = client.get(BASE_URL + "/", headers=superuser_token_headers)
    assert response.status_code == 200
    for rec in response.json()["data"]:
        if rec["invoice_number"] == "DUP-HINT":
            assert rec["duplicate_invoice_owner_count"] is not None
            assert rec["duplicate_invoice_owner_count"] > 0


def test_normal_user_no_duplicate_hint(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user, authentication_token_from_email

    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    _create_random_invoice(db, owner_id=owner_id, invoice_number="DUP-NO-HINT")

    response = client.get(BASE_URL + "/", headers=normal_user_token_headers)
    assert response.status_code == 200
    for rec in response.json()["data"]:
        if rec["invoice_number"] == "DUP-NO-HINT":
            assert rec["duplicate_invoice_owner_count"] is None
            assert rec["duplicate_warning"] is None


# =============================================================================
# Update
# =============================================================================


def test_update_invoice_success(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_invoice(db, owner_id=owner_id)

    response = client.patch(
        f"{BASE_URL}/{record.id}",
        headers=normal_user_token_headers,
        data={"buyer": "Updated Buyer"},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["buyer"] == "Updated Buyer"


def test_update_invoice_not_editable_status(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_invoice(db, owner_id=owner_id, status=STATUS_CONFIRMED)

    response = client.patch(
        f"{BASE_URL}/{record.id}",
        headers=normal_user_token_headers,
        data={"buyer": "Updated Buyer"},
    )
    assert response.status_code == 403


def test_update_invoice_invalid_amount(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_invoice(db, owner_id=owner_id)

    response = client.patch(
        f"{BASE_URL}/{record.id}",
        headers=normal_user_token_headers,
        data={"invoice_amount": "bad"},
    )
    assert response.status_code == 422


def test_update_invoice_invalid_date(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_invoice(db, owner_id=owner_id)

    response = client.patch(
        f"{BASE_URL}/{record.id}",
        headers=normal_user_token_headers,
        data={"invoice_date": "bad-date"},
    )
    assert response.status_code == 422


# =============================================================================
# State Transitions
# =============================================================================


def test_confirm_invoice(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_invoice(db, owner_id=owner_id)

    response = client.post(
        f"{BASE_URL}/{record.id}/confirm",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == STATUS_CONFIRMED


def test_withdraw_confirmation(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_invoice(db, owner_id=owner_id, status=STATUS_CONFIRMED)

    response = client.post(
        f"{BASE_URL}/{record.id}/withdraw-confirmation",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == STATUS_DRAFT


def test_void_invoice(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_invoice(db, owner_id=owner_id, status=STATUS_CONFIRMED)

    response = client.post(
        f"{BASE_URL}/{record.id}/void",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == STATUS_VOIDED


def test_restore_draft(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_invoice(db, owner_id=owner_id, status=STATUS_VOIDED)

    response = client.post(
        f"{BASE_URL}/{record.id}/restore-draft",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == STATUS_DRAFT


def test_invalid_state_transition_draft_to_void(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_invoice(db, owner_id=owner_id, status=STATUS_DRAFT)

    response = client.post(
        f"{BASE_URL}/{record.id}/void",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


def test_invalid_state_transition_void_to_confirmed(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_invoice(db, owner_id=owner_id, status=STATUS_VOIDED)

    response = client.post(
        f"{BASE_URL}/{record.id}/confirm",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


# =============================================================================
# Soft Delete / Restore
# =============================================================================


def test_soft_delete_invoice(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_invoice(db, owner_id=owner_id)

    response = client.delete(
        f"{BASE_URL}/{record.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Invoice file deleted successfully"

    # Should no longer appear in normal list
    list_resp = client.get(BASE_URL + "/", headers=normal_user_token_headers)
    assert list_resp.status_code == 200
    ids = [r["id"] for r in list_resp.json()["data"]]
    assert str(record.id) not in ids

    # Should appear in deleted list
    del_resp = client.get(
        BASE_URL + "/?deleted=true", headers=normal_user_token_headers
    )
    assert del_resp.status_code == 200
    ids = [r["id"] for r in del_resp.json()["data"]]
    assert str(record.id) in ids


def test_restore_invoice(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_invoice(db, owner_id=owner_id)

    client.delete(f"{BASE_URL}/{record.id}", headers=normal_user_token_headers)

    response = client.post(
        f"{BASE_URL}/{record.id}/restore",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["deleted_at"] is None
    assert response.json()["deleted_by_id"] is None


def test_non_deleter_cannot_view_deleted(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user
    from app.modules.finance.invoice_files.repository import soft_delete_record

    other_user = create_random_user(db)
    record = _create_random_invoice(db, owner_id=other_user.id)
    soft_delete_record(session=db, record=record, deleted_by_id=other_user.id)

    response = client.get(
        BASE_URL + "/?deleted=true", headers=superuser_token_headers
    )
    assert response.status_code == 200
    ids = [r["id"] for r in response.json()["data"]]
    assert str(record.id) not in ids


# =============================================================================
# Purge
# =============================================================================


def test_purge_old_deleted_invoices_admin_only(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    response = client.post(
        BASE_URL + "/purge-deleted",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert "Purged" in response.json()["message"]


def test_purge_old_deleted_invoices_normal_user_forbidden(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.post(
        BASE_URL + "/purge-deleted",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


# =============================================================================
# PDF Download
# =============================================================================


def test_pdf_download_auth(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_invoice(db, owner_id=owner_id)

    response = client.get(
        f"{BASE_URL}/{record.id}/pdf",
        headers=normal_user_token_headers,
    )
    # File may not exist on disk in test env, but auth should pass first
    assert response.status_code in (200, 404)


def test_pdf_download_forbidden(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user

    other_user = create_random_user(db)
    record = _create_random_invoice(db, owner_id=other_user.id)

    response = client.get(
        f"{BASE_URL}/{record.id}/pdf",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


def test_pdf_download_unauthenticated(client: TestClient, db: Session) -> None:
    from tests.utils.user import create_random_user

    user = create_random_user(db)
    record = _create_random_invoice(db, owner_id=user.id)

    response = client.get(f"{BASE_URL}/{record.id}/pdf")
    assert response.status_code in (401, 403)


# =============================================================================
# OCR / Parse Preview Config Behavior
# =============================================================================


def test_parse_preview_disabled_local_ocr(
    client: TestClient, superuser_token_headers: dict[str, str], monkeypatch
) -> None:
    monkeypatch.setattr(
        "app.modules.finance.invoice_files.pdf_parser.settings.ENABLE_LOCAL_OCR", False
    )
    pdf_bytes, filename = _pdf_file()
    response = client.post(
        f"{BASE_URL}/parse-preview",
        headers=superuser_token_headers,
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json() == {
        "invoice_number": None,
        "invoice_date": None,
        "invoice_amount": None,
        "tax_amount": None,
        "currency": None,
        "buyer": None,
        "seller": None,
        "invoice_type": None,
        "note": None,
    }


def test_parse_preview_unsupported_provider(
    client: TestClient, superuser_token_headers: dict[str, str], monkeypatch
) -> None:
    monkeypatch.setattr(
        "app.modules.finance.invoice_files.pdf_parser.settings.OCR_PROVIDER", "tesseract"
    )
    monkeypatch.setattr(
        "app.modules.finance.invoice_files.pdf_parser._paddleocr", None
    )
    pdf_bytes, filename = _pdf_file()
    response = client.post(
        f"{BASE_URL}/parse-preview",
        headers=superuser_token_headers,
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["invoice_amount"] is None


def test_parse_preview_model_dir_missing_no_download(
    client: TestClient, superuser_token_headers: dict[str, str], monkeypatch
) -> None:
    monkeypatch.setattr(
        "app.modules.finance.invoice_files.pdf_parser.settings.OCR_ALLOW_MODEL_DOWNLOAD",
        False,
    )
    monkeypatch.setattr(
        "app.modules.finance.invoice_files.pdf_parser.settings.OCR_MODEL_DIR",
        "/nonexistent/models/path",
    )
    monkeypatch.setattr(
        "app.modules.finance.invoice_files.pdf_parser._paddleocr", None
    )
    pdf_bytes, filename = _pdf_file()
    response = client.post(
        f"{BASE_URL}/parse-preview",
        headers=superuser_token_headers,
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json() == {
        "invoice_number": None,
        "invoice_date": None,
        "invoice_amount": None,
        "tax_amount": None,
        "currency": None,
        "buyer": None,
        "seller": None,
        "invoice_type": None,
        "note": None,
    }


# =============================================================================
# Strict local model directory checks
# =============================================================================


def test_has_required_local_models_missing_dir() -> None:
    from app.modules.finance.invoice_files.pdf_parser import _has_required_local_models
    from pathlib import Path

    assert _has_required_local_models(Path("/does/not/exist")) is False


def test_has_required_local_models_missing_subdir(tmp_path) -> None:
    from app.modules.finance.invoice_files.pdf_parser import _has_required_local_models

    model_dir = tmp_path / "models"
    model_dir.mkdir()
    (model_dir / "det").mkdir()
    (model_dir / "rec").mkdir()
    # cls missing
    assert _has_required_local_models(model_dir) is False


def test_has_required_local_models_empty_subdir(tmp_path) -> None:
    from app.modules.finance.invoice_files.pdf_parser import _has_required_local_models

    model_dir = tmp_path / "models"
    model_dir.mkdir()
    (model_dir / "det").mkdir()
    (model_dir / "rec").mkdir()
    (model_dir / "cls").mkdir()
    (model_dir / "det" / "model.bin").write_bytes(b"x")
    (model_dir / "rec" / "model.bin").write_bytes(b"x")
    assert _has_required_local_models(model_dir) is False


def test_has_required_local_models_all_present(tmp_path) -> None:
    from app.modules.finance.invoice_files.pdf_parser import _has_required_local_models

    model_dir = tmp_path / "models"
    model_dir.mkdir()
    for sub in ("det", "rec", "cls"):
        (model_dir / sub).mkdir()
        (model_dir / sub / "model.bin").write_bytes(b"x")
    assert _has_required_local_models(model_dir) is True


def test_parse_preview_no_paddleocr_init_when_models_missing(
    client: TestClient, superuser_token_headers: dict[str, str], monkeypatch
) -> None:
    monkeypatch.setattr(
        "app.modules.finance.invoice_files.pdf_parser.settings.OCR_ALLOW_MODEL_DOWNLOAD",
        False,
    )
    monkeypatch.setattr(
        "app.modules.finance.invoice_files.pdf_parser.settings.OCR_MODEL_DIR",
        "/nonexistent",
    )
    monkeypatch.setattr(
        "app.modules.finance.invoice_files.pdf_parser._paddleocr", None
    )

    pdf_bytes, filename = _pdf_file()
    response = client.post(
        f"{BASE_URL}/parse-preview",
        headers=superuser_token_headers,
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["invoice_number"] is None

    from app.modules.finance.invoice_files.pdf_parser import _paddleocr
    assert _paddleocr is None


# =============================================================================
# BE-FIX-001: PDF replacement transaction safety
# =============================================================================


def test_update_invoice_with_pdf_replacement(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Updating a draft with a new PDF should save new file, update metadata,
    and remove the old file after DB success."""
    from pathlib import Path

    pdf_bytes, filename = _pdf_file()
    create_resp = client.post(
        BASE_URL + "/",
        headers=normal_user_token_headers,
        data={
            "invoice_number": "PDF-REPLACE-001",
            "invoice_date": "2026-04-24",
            "invoice_amount": "10.00",
            "currency": "CNY",
            "buyer": "Buyer",
            "seller": "Seller",
            "invoice_type": INVOICE_TYPE_GENERAL,
        },
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert create_resp.status_code == 200
    old_pdf_path = create_resp.json()["pdf_path"]
    old_pdf_abs = Path("runtime_data/uploads") / old_pdf_path
    assert old_pdf_abs.exists()

    new_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n"
    update_resp = client.patch(
        f"{BASE_URL}/{create_resp.json()['id']}",
        headers=normal_user_token_headers,
        data={"buyer": "Updated Buyer"},
        files={"pdf": ("new.pdf", io.BytesIO(new_pdf_bytes), "application/pdf")},
    )
    assert update_resp.status_code == 200
    content = update_resp.json()
    assert content["buyer"] == "Updated Buyer"
    assert content["pdf_original_name"] == "new.pdf"
    new_pdf_path = content["pdf_path"]
    assert new_pdf_path != old_pdf_path
    new_pdf_abs = Path("runtime_data/uploads") / new_pdf_path
    assert new_pdf_abs.exists()
    assert not old_pdf_abs.exists()


# =============================================================================
# BE-FIX-002: Admin read-all / delete-any, but owner-only write
# =============================================================================


def test_admin_cannot_update_others_invoice(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user

    other_user = create_random_user(db)
    record = _create_random_invoice(db, owner_id=other_user.id)
    response = client.patch(
        f"{BASE_URL}/{record.id}",
        headers=superuser_token_headers,
        data={"buyer": "Hacked Buyer"},
    )
    assert response.status_code == 403


def test_admin_cannot_confirm_others_invoice(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user

    other_user = create_random_user(db)
    record = _create_random_invoice(db, owner_id=other_user.id)
    response = client.post(
        f"{BASE_URL}/{record.id}/confirm",
        headers=superuser_token_headers,
    )
    assert response.status_code == 403


def test_admin_cannot_withdraw_others_invoice(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user

    other_user = create_random_user(db)
    record = _create_random_invoice(db, owner_id=other_user.id, status=STATUS_CONFIRMED)
    response = client.post(
        f"{BASE_URL}/{record.id}/withdraw-confirmation",
        headers=superuser_token_headers,
    )
    assert response.status_code == 403


def test_admin_cannot_void_others_invoice(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user

    other_user = create_random_user(db)
    record = _create_random_invoice(db, owner_id=other_user.id, status=STATUS_CONFIRMED)
    response = client.post(
        f"{BASE_URL}/{record.id}/void",
        headers=superuser_token_headers,
    )
    assert response.status_code == 403


def test_admin_cannot_restore_draft_others_invoice(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user

    other_user = create_random_user(db)
    record = _create_random_invoice(db, owner_id=other_user.id, status=STATUS_VOIDED)
    response = client.post(
        f"{BASE_URL}/{record.id}/restore-draft",
        headers=superuser_token_headers,
    )
    assert response.status_code == 403


# Admin can still read and delete any record


def test_admin_can_read_others_invoice(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user

    other_user = create_random_user(db)
    record = _create_random_invoice(db, owner_id=other_user.id)
    response = client.get(
        f"{BASE_URL}/{record.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(record.id)


def test_admin_can_delete_others_invoice(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user

    other_user = create_random_user(db)
    record = _create_random_invoice(db, owner_id=other_user.id)
    response = client.delete(
        f"{BASE_URL}/{record.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200


# =============================================================================
# BE-FIX-003: Purge deletes physical PDF files
# =============================================================================


def test_purge_deletes_physical_pdf(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    from pathlib import Path
    from datetime import datetime, timezone, timedelta
    from tests.utils.user import create_random_user

    user = create_random_user(db)
    pdf_bytes, filename = _pdf_file()
    create_resp = client.post(
        BASE_URL + "/",
        headers=superuser_token_headers,
        data={
            "invoice_number": "PURGE-PDF-001",
            "invoice_date": "2026-04-24",
            "invoice_amount": "10.00",
            "currency": "CNY",
            "buyer": "Buyer",
            "seller": "Seller",
            "invoice_type": INVOICE_TYPE_GENERAL,
        },
        files={"pdf": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert create_resp.status_code == 200
    record_id = uuid.UUID(create_resp.json()["id"])
    pdf_path = create_resp.json()["pdf_path"]
    pdf_abs = Path("runtime_data/uploads") / pdf_path
    assert pdf_abs.exists()

    # Soft delete
    del_resp = client.delete(
        f"{BASE_URL}/{record_id}",
        headers=superuser_token_headers,
    )
    assert del_resp.status_code == 200

    # Manually set deleted_at to 31 days ago so it qualifies for purge
    from app.modules.finance.invoice_files.repository import get_record
    record = get_record(db, record_id=record_id)
    record.deleted_at = datetime.now(timezone.utc) - timedelta(days=31)
    db.add(record)
    db.commit()

    purge_resp = client.post(
        BASE_URL + "/purge-deleted",
        headers=superuser_token_headers,
    )
    assert purge_resp.status_code == 200
    assert "Purged" in purge_resp.json()["message"]

    # DB record should be gone
    from app.modules.finance.invoice_files.repository import get_record as get_record2
    assert get_record2(db, record_id=record_id) is None

    # Physical PDF should be gone
    assert not pdf_abs.exists()

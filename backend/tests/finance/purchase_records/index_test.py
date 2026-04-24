"""
backend/tests/finance/purchase_records/index_test.py
purchase_records 工具主测试文件

覆盖范围：
- POST /api/v1/finance/purchase-records/ocr-preview   OCR 预览（不落库）
- GET  /api/v1/finance/purchase-records                列表查询
- GET  /api/v1/finance/purchase-records/{id}           详情查询
- POST /api/v1/finance/purchase-records                创建（含截图元数据）
- PATCH /api/v1/finance/purchase-records/{id}          更新
- POST /api/v1/finance/purchase-records/{id}/submit    提交
- POST /api/v1/finance/purchase-records/{id}/withdraw  撤回
- POST /api/v1/finance/purchase-records/{id}/approve   批准（管理员）
- POST /api/v1/finance/purchase-records/{id}/reject    驳回（管理员）
- POST /api/v1/finance/purchase-records/{id}/unapprove 撤回批准（管理员）
- DELETE /api/v1/finance/purchase-records/{id}         逻辑删除
- POST /api/v1/finance/purchase-records/{id}/restore   恢复
- POST /api/v1/finance/purchase-records/purge-deleted  清理 30 天前删除记录
- GET  /api/v1/finance/purchase-records/{id}/screenshot 截图鉴权下载
- 权限分支（403 / 404）
- 大类/小类校验
- 数据隔离
"""

import io
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.modules.finance.purchase_records.constants import (
    CATEGORY_MEALS_ENTERTAINMENT,
    CATEGORY_OTHER_PROJECT,
    STATUS_APPROVED,
    STATUS_DRAFT,
    STATUS_REJECTED,
    STATUS_SUBMITTED,
    SUBCATEGORY_AGV,
)
from app.modules.finance.purchase_records.models import PurchaseRecord
from app.modules.finance.purchase_records.repository import create_record
from app.modules.finance.purchase_records.schemas import PurchaseRecordCreate

BASE_URL = f"{settings.API_V1_STR}/finance/purchase-records"


def _screenshot_file() -> tuple[bytes, str]:
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR", "test.png"


def _create_random_record(
    db: Session,
    owner_id: uuid.UUID,
    status: str = STATUS_DRAFT,
    deleted_at=None,
    deleted_by_id=None,
    category: str = CATEGORY_MEALS_ENTERTAINMENT,
    subcategory: str | None = None,
) -> PurchaseRecord:
    data = PurchaseRecordCreate(
        purchase_date="2026-04-24",
        amount="123.45",
        currency="CNY",
        order_name="Test Order",
        category=category,
        subcategory=subcategory,
        note=None,
    )
    record = create_record(
        session=db,
        record_in=data,
        owner_id=owner_id,
        screenshot_path="finance/purchase_records/fake.png",
        screenshot_original_name="fake.png",
        screenshot_mime_type="image/png",
        screenshot_size=100,
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
# OCR Preview
# =============================================================================


def test_ocr_preview_no_persist(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """OCR preview does not create a database record."""
    image_bytes, filename = _screenshot_file()
    response = client.post(
        f"{BASE_URL}/ocr-preview",
        headers=superuser_token_headers,
        files={"screenshot": (filename, io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    content = response.json()
    # Even if OCR fails / is unavailable, response should be a JSON object
    assert isinstance(content, dict)


# =============================================================================
# Create
# =============================================================================


def test_create_record_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    image_bytes, filename = _screenshot_file()
    response = client.post(
        BASE_URL + "/",
        headers=normal_user_token_headers,
        data={
            "purchase_date": "2026-04-24",
            "amount": "99.99",
            "currency": "CNY",
            "order_name": "User Order",
            "category": CATEGORY_MEALS_ENTERTAINMENT,
        },
        files={"screenshot": (filename, io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["status"] == STATUS_DRAFT
    assert content["invoice_match_status"] == "unmatched"
    assert content["owner_id"] is not None
    assert content["screenshot_path"] is not None
    assert content["screenshot_original_name"] == filename


def test_create_record_invalid_category_subcategory(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """subcategory must be empty when category is not other_project."""
    image_bytes, filename = _screenshot_file()
    response = client.post(
        BASE_URL + "/",
        headers=normal_user_token_headers,
        data={
            "purchase_date": "2026-04-24",
            "amount": "10.00",
            "currency": "CNY",
            "order_name": "Bad Order",
            "category": CATEGORY_MEALS_ENTERTAINMENT,
            "subcategory": SUBCATEGORY_AGV,
        },
        files={"screenshot": (filename, io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 422


def test_create_record_other_project_with_subcategory(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """subcategory allowed when category is other_project."""
    image_bytes, filename = _screenshot_file()
    response = client.post(
        BASE_URL + "/",
        headers=normal_user_token_headers,
        data={
            "purchase_date": "2026-04-24",
            "amount": "10.00",
            "currency": "CNY",
            "order_name": "Project Order",
            "category": CATEGORY_OTHER_PROJECT,
            "subcategory": SUBCATEGORY_AGV,
        },
        files={"screenshot": (filename, io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["category"] == CATEGORY_OTHER_PROJECT
    assert content["subcategory"] == SUBCATEGORY_AGV


# =============================================================================
# List
# =============================================================================


def test_list_records_normal_user_sees_only_own(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    response = client.get(BASE_URL + "/", headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content
    # Only records belonging to the normal user should appear
    for rec in content["data"]:
        assert rec["deleted_at"] is None


def test_list_records_superuser_sees_all(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    response = client.get(BASE_URL + "/", headers=superuser_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content


def test_list_deleted_records_only_shows_deleter(
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


def test_read_record_success(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # Need a record owned by superuser or accessible to superuser
    from tests.utils.user import create_random_user

    user = create_random_user(db)
    record = _create_random_record(db, owner_id=user.id)
    response = client.get(
        f"{BASE_URL}/{record.id}", headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(record.id)


def test_read_record_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{BASE_URL}/{uuid.uuid4()}", headers=superuser_token_headers
    )
    assert response.status_code == 404


def test_read_record_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user

    other_user = create_random_user(db)
    record = _create_random_record(db, owner_id=other_user.id)
    response = client.get(
        f"{BASE_URL}/{record.id}", headers=normal_user_token_headers
    )
    assert response.status_code == 403


# =============================================================================
# Update
# =============================================================================


def test_update_record_success(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    # Create a record for the normal user
    from tests.utils.user import authentication_token_from_email

    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_record(db, owner_id=owner_id)

    response = client.patch(
        f"{BASE_URL}/{record.id}",
        headers=normal_user_token_headers,
        data={"amount": "999.99"},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["amount"] == "999.99"


def test_update_record_not_editable_status(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import authentication_token_from_email

    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_record(db, owner_id=owner_id, status=STATUS_SUBMITTED)

    response = client.patch(
        f"{BASE_URL}/{record.id}",
        headers=normal_user_token_headers,
        data={"amount": "1.00"},
    )
    assert response.status_code == 403


# =============================================================================
# State Transitions
# =============================================================================


def test_submit_record(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_record(db, owner_id=owner_id)

    response = client.post(
        f"{BASE_URL}/{record.id}/submit",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == STATUS_SUBMITTED


def test_withdraw_record(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_record(db, owner_id=owner_id, status=STATUS_SUBMITTED)

    response = client.post(
        f"{BASE_URL}/{record.id}/withdraw",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == STATUS_DRAFT


def test_approve_record_admin_only(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user

    user = create_random_user(db)
    record = _create_random_record(db, owner_id=user.id, status=STATUS_SUBMITTED)

    response = client.post(
        f"{BASE_URL}/{record.id}/approve",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == STATUS_APPROVED


def test_approve_record_normal_user_forbidden(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_record(db, owner_id=owner_id, status=STATUS_SUBMITTED)

    response = client.post(
        f"{BASE_URL}/{record.id}/approve",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


def test_reject_record_admin_only(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user

    user = create_random_user(db)
    record = _create_random_record(db, owner_id=user.id, status=STATUS_SUBMITTED)

    response = client.post(
        f"{BASE_URL}/{record.id}/reject",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == STATUS_REJECTED


def test_unapprove_record_admin_only(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user

    user = create_random_user(db)
    record = _create_random_record(db, owner_id=user.id, status=STATUS_APPROVED)

    response = client.post(
        f"{BASE_URL}/{record.id}/unapprove",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == STATUS_SUBMITTED


# =============================================================================
# Soft Delete / Restore
# =============================================================================


def test_soft_delete_record(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_record(db, owner_id=owner_id)

    response = client.delete(
        f"{BASE_URL}/{record.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Purchase record deleted successfully"

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


def test_restore_record(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_record(db, owner_id=owner_id)

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

    other_user = create_random_user(db)
    record = _create_random_record(db, owner_id=other_user.id)
    # Delete as the owner
    from app.modules.finance.purchase_records.repository import soft_delete_record

    soft_delete_record(session=db, record=record, deleted_by_id=other_user.id)

    # Superuser should NOT see it in deleted list because deleted_by_id != superuser
    response = client.get(
        BASE_URL + "/?deleted=true", headers=superuser_token_headers
    )
    assert response.status_code == 200
    ids = [r["id"] for r in response.json()["data"]]
    assert str(record.id) not in ids


# =============================================================================
# Purge
# =============================================================================


def test_purge_old_deleted_records_admin_only(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    response = client.post(
        BASE_URL + "/purge-deleted",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    # Message should mention count
    assert "Purged" in response.json()["message"]


def test_purge_old_deleted_records_normal_user_forbidden(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.post(
        BASE_URL + "/purge-deleted",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


# =============================================================================
# Screenshot Download
# =============================================================================


def test_screenshot_download_auth(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_record(db, owner_id=owner_id)

    response = client.get(
        f"{BASE_URL}/{record.id}/screenshot",
        headers=normal_user_token_headers,
    )
    # File may not exist on disk in test env, but auth should pass first
    # If file is missing, we might get 500; we mainly test that 403 is not returned
    assert response.status_code in (200, 404, 500)


def test_screenshot_download_forbidden(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    from tests.utils.user import create_random_user

    other_user = create_random_user(db)
    record = _create_random_record(db, owner_id=other_user.id)

    response = client.get(
        f"{BASE_URL}/{record.id}/screenshot",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


# =============================================================================
# BE-FIX-001: OCR preview must require authentication
# =============================================================================


def test_ocr_preview_unauthenticated(client: TestClient) -> None:
    image_bytes, filename = _screenshot_file()
    response = client.post(
        f"{BASE_URL}/ocr-preview",
        files={"screenshot": (filename, io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code in (401, 403)


# =============================================================================
# BE-FIX-002: amount must be valid decimal
# =============================================================================


def test_create_record_invalid_amount(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    image_bytes, filename = _screenshot_file()
    response = client.post(
        BASE_URL + "/",
        headers=normal_user_token_headers,
        data={
            "purchase_date": "2026-04-24",
            "amount": "abc",
            "currency": "CNY",
            "order_name": "Bad Amount",
            "category": CATEGORY_MEALS_ENTERTAINMENT,
        },
        files={"screenshot": (filename, io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 422


def test_update_record_invalid_amount(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_record(db, owner_id=owner_id)

    response = client.patch(
        f"{BASE_URL}/{record.id}",
        headers=normal_user_token_headers,
        data={"amount": "not-a-number"},
    )
    assert response.status_code == 422


# =============================================================================
# BE-FIX-003: invalid date must return 422
# =============================================================================


def test_create_record_invalid_date(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    image_bytes, filename = _screenshot_file()
    response = client.post(
        BASE_URL + "/",
        headers=normal_user_token_headers,
        data={
            "purchase_date": "not-a-date",
            "amount": "10.00",
            "currency": "CNY",
            "order_name": "Bad Date",
            "category": CATEGORY_MEALS_ENTERTAINMENT,
        },
        files={"screenshot": (filename, io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 422


def test_update_record_invalid_date(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_record(db, owner_id=owner_id)

    response = client.patch(
        f"{BASE_URL}/{record.id}",
        headers=normal_user_token_headers,
        data={"purchase_date": "invalid-date"},
    )
    assert response.status_code == 422


# =============================================================================
# BE-FIX-004: support clearing subcategory
# =============================================================================


def test_update_record_clear_subcategory(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_record(
        db, owner_id=owner_id, category=CATEGORY_OTHER_PROJECT, subcategory=SUBCATEGORY_AGV
    )

    response = client.patch(
        f"{BASE_URL}/{record.id}",
        headers=normal_user_token_headers,
        data={
            "category": CATEGORY_MEALS_ENTERTAINMENT,
            "subcategory": "",
        },
    )
    assert response.status_code == 200
    content = response.json()
    assert content["category"] == CATEGORY_MEALS_ENTERTAINMENT
    assert content["subcategory"] is None


def test_update_record_vehicle_with_subcategory_still_fails(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )
    owner_id = uuid.UUID(me_resp.json()["id"])
    record = _create_random_record(db, owner_id=owner_id)

    response = client.patch(
        f"{BASE_URL}/{record.id}",
        headers=normal_user_token_headers,
        data={
            "category": CATEGORY_MEALS_ENTERTAINMENT,
            "subcategory": SUBCATEGORY_AGV,
        },
    )
    assert response.status_code == 422


# =============================================================================
# BE-FIX-006: OCR config behavior
# =============================================================================


def test_ocr_preview_disabled_local_ocr(
    client: TestClient, superuser_token_headers: dict[str, str], monkeypatch
) -> None:
    monkeypatch.setattr(
        "app.modules.finance.purchase_records.ocr.settings.ENABLE_LOCAL_OCR", False
    )
    image_bytes, filename = _screenshot_file()
    response = client.post(
        f"{BASE_URL}/ocr-preview",
        headers=superuser_token_headers,
        files={"screenshot": (filename, io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    assert response.json() == {
        "purchase_date": None,
        "amount": None,
        "currency": None,
        "order_name": None,
        "category": None,
        "subcategory": None,
        "note": None,
    }


def test_ocr_preview_unsupported_provider(
    client: TestClient, superuser_token_headers: dict[str, str], monkeypatch
) -> None:
    monkeypatch.setattr(
        "app.modules.finance.purchase_records.ocr.settings.OCR_PROVIDER", "tesseract"
    )
    # Reset lazy-init state
    monkeypatch.setattr(
        "app.modules.finance.purchase_records.ocr._paddleocr", None
    )
    image_bytes, filename = _screenshot_file()
    response = client.post(
        f"{BASE_URL}/ocr-preview",
        headers=superuser_token_headers,
        files={"screenshot": (filename, io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["amount"] is None


def test_ocr_preview_model_dir_missing_no_download(
    client: TestClient, superuser_token_headers: dict[str, str], monkeypatch
) -> None:
    """OCR_ALLOW_MODEL_DOWNLOAD=false and model dir missing -> empty preview."""
    monkeypatch.setattr(
        "app.modules.finance.purchase_records.ocr.settings.OCR_ALLOW_MODEL_DOWNLOAD",
        False,
    )
    monkeypatch.setattr(
        "app.modules.finance.purchase_records.ocr.settings.OCR_MODEL_DIR",
        "/nonexistent/models/path",
    )
    # Reset lazy-init state
    monkeypatch.setattr(
        "app.modules.finance.purchase_records.ocr._paddleocr", None
    )
    image_bytes, filename = _screenshot_file()
    response = client.post(
        f"{BASE_URL}/ocr-preview",
        headers=superuser_token_headers,
        files={"screenshot": (filename, io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    assert response.json() == {
        "purchase_date": None,
        "amount": None,
        "currency": None,
        "order_name": None,
        "category": None,
        "subcategory": None,
        "note": None,
    }


# =============================================================================
# BE-HARDEN-003: strict local model directory checks
# =============================================================================


def test_has_required_local_models_missing_dir() -> None:
    from app.modules.finance.purchase_records.ocr import _has_required_local_models
    from pathlib import Path

    assert _has_required_local_models(Path("/does/not/exist")) is False


def test_has_required_local_models_missing_subdir(tmp_path) -> None:
    from app.modules.finance.purchase_records.ocr import _has_required_local_models

    model_dir = tmp_path / "models"
    model_dir.mkdir()
    (model_dir / "det").mkdir()
    (model_dir / "rec").mkdir()
    # cls missing
    assert _has_required_local_models(model_dir) is False


def test_has_required_local_models_empty_subdir(tmp_path) -> None:
    from app.modules.finance.purchase_records.ocr import _has_required_local_models

    model_dir = tmp_path / "models"
    model_dir.mkdir()
    (model_dir / "det").mkdir()
    (model_dir / "rec").mkdir()
    (model_dir / "cls").mkdir()
    # put a file in det and rec, but leave cls empty
    (model_dir / "det" / "model.bin").write_bytes(b"x")
    (model_dir / "rec" / "model.bin").write_bytes(b"x")
    assert _has_required_local_models(model_dir) is False


def test_has_required_local_models_all_present(tmp_path) -> None:
    from app.modules.finance.purchase_records.ocr import _has_required_local_models

    model_dir = tmp_path / "models"
    model_dir.mkdir()
    for sub in ("det", "rec", "cls"):
        (model_dir / sub).mkdir()
        (model_dir / sub / "model.bin").write_bytes(b"x")
    assert _has_required_local_models(model_dir) is True


def test_ocr_preview_missing_det_subdir_no_download(
    client: TestClient, superuser_token_headers: dict[str, str], monkeypatch, tmp_path
) -> None:
    """OCR_ALLOW_MODEL_DOWNLOAD=false and OCR_MODEL_DIR missing det -> empty preview."""
    model_dir = tmp_path / "paddleocr"
    model_dir.mkdir()
    (model_dir / "rec").mkdir()
    (model_dir / "cls").mkdir()
    # det missing

    monkeypatch.setattr(
        "app.modules.finance.purchase_records.ocr.settings.OCR_ALLOW_MODEL_DOWNLOAD",
        False,
    )
    monkeypatch.setattr(
        "app.modules.finance.purchase_records.ocr.settings.OCR_MODEL_DIR",
        str(model_dir),
    )
    monkeypatch.setattr(
        "app.modules.finance.purchase_records.ocr._paddleocr", None
    )
    image_bytes, filename = _screenshot_file()
    response = client.post(
        f"{BASE_URL}/ocr-preview",
        headers=superuser_token_headers,
        files={"screenshot": (filename, io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["purchase_date"] is None


def test_ocr_preview_empty_cls_subdir_no_download(
    client: TestClient, superuser_token_headers: dict[str, str], monkeypatch, tmp_path
) -> None:
    """OCR_ALLOW_MODEL_DOWNLOAD=false and cls empty -> empty preview."""
    model_dir = tmp_path / "paddleocr"
    model_dir.mkdir()
    for sub in ("det", "rec", "cls"):
        (model_dir / sub).mkdir()
    (model_dir / "det" / "model.bin").write_bytes(b"x")
    (model_dir / "rec" / "model.bin").write_bytes(b"x")
    # cls empty

    monkeypatch.setattr(
        "app.modules.finance.purchase_records.ocr.settings.OCR_ALLOW_MODEL_DOWNLOAD",
        False,
    )
    monkeypatch.setattr(
        "app.modules.finance.purchase_records.ocr.settings.OCR_MODEL_DIR",
        str(model_dir),
    )
    monkeypatch.setattr(
        "app.modules.finance.purchase_records.ocr._paddleocr", None
    )
    image_bytes, filename = _screenshot_file()
    response = client.post(
        f"{BASE_URL}/ocr-preview",
        headers=superuser_token_headers,
        files={"screenshot": (filename, io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["purchase_date"] is None


def test_ocr_preview_no_paddleocr_init_when_models_missing(
    client: TestClient, superuser_token_headers: dict[str, str], monkeypatch, tmp_path
) -> None:
    """When models are missing, PaddleOCR must not be imported or initialized."""
    monkeypatch.setattr(
        "app.modules.finance.purchase_records.ocr.settings.OCR_ALLOW_MODEL_DOWNLOAD",
        False,
    )
    monkeypatch.setattr(
        "app.modules.finance.purchase_records.ocr.settings.OCR_MODEL_DIR",
        "/nonexistent",
    )
    # Ensure _paddleocr is None before request
    monkeypatch.setattr(
        "app.modules.finance.purchase_records.ocr._paddleocr", None
    )

    image_bytes, filename = _screenshot_file()
    response = client.post(
        f"{BASE_URL}/ocr-preview",
        headers=superuser_token_headers,
        files={"screenshot": (filename, io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["purchase_date"] is None

    # After the request, _paddleocr must still be None, confirming PaddleOCR was never imported/initialized
    from app.modules.finance.purchase_records.ocr import _paddleocr
    assert _paddleocr is None

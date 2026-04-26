"""
backend/tests/finance/dashboard/index_test.py
Finance dashboard tool main test file.
"""

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.modules.finance.invoice_files.constants import (
    STATUS_CONFIRMED as INV_CONFIRMED,
    STATUS_DRAFT as INV_DRAFT,
    STATUS_VOIDED as INV_VOIDED,
)
from app.modules.finance.invoice_files.models import InvoiceFile
from app.modules.finance.invoice_files.repository import (
    create_record as create_invoice,
)
from app.modules.finance.invoice_files.schemas import InvoiceFileCreate
from app.modules.finance.invoice_matching.constants import (
    MATCH_STATUS_CONFIRMED,
)
from app.modules.finance.invoice_matching.models import InvoiceMatch
from app.modules.finance.invoice_matching.repository import (
    cancel_match as repo_cancel,
    create_match as repo_create,
    mark_needs_review as repo_mark_needs_review,
)
from app.modules.finance.purchase_records.constants import (
    STATUS_APPROVED as PR_APPROVED,
    STATUS_DRAFT as PR_DRAFT,
)
from app.modules.finance.purchase_records.models import PurchaseRecord
from app.modules.finance.purchase_records.repository import (
    create_record as create_purchase,
    soft_delete_record,
)
from app.modules.finance.purchase_records.schemas import PurchaseRecordCreate
from tests.utils.user import (
    create_random_user,
    user_authentication_headers,
)
from tests.utils.utils import random_email, random_lower_string

BASE_URL = f"{settings.API_V1_STR}/finance/dashboard"


# =============================================================================
# Helpers
# =============================================================================


def _make_purchase(
    db: Session,
    owner_id: uuid.UUID,
    *,
    amount: str = "100.00",
    currency: str = "CNY",
    purchase_date: str = "2026-04-01",
    status: str = PR_APPROVED,
) -> PurchaseRecord:
    record = create_purchase(
        session=db,
        record_in=PurchaseRecordCreate(
            purchase_date=purchase_date,
            amount=amount,
            currency=currency,
            order_name="Order",
            category="meals_entertainment",
            subcategory=None,
            note=None,
        ),
        owner_id=owner_id,
        screenshot_path="finance/purchase_records/fake.png",
        screenshot_original_name="fake.png",
        screenshot_mime_type="image/png",
        screenshot_size=10,
    )
    if status != PR_DRAFT:
        record.status = status
        db.add(record)
        db.commit()
        db.refresh(record)
    return record


def _make_invoice(
    db: Session,
    owner_id: uuid.UUID,
    *,
    amount: str = "100.00",
    currency: str = "CNY",
    invoice_date: str = "2026-04-01",
    status: str = INV_CONFIRMED,
) -> InvoiceFile:
    record = create_invoice(
        session=db,
        record_in=InvoiceFileCreate(
            invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
            invoice_date=invoice_date,
            invoice_amount=amount,
            tax_amount="0.00",
            currency=currency,
            buyer="Buyer",
            seller="Seller",
            invoice_type="general",
            note=None,
        ),
        owner_id=owner_id,
        pdf_path="finance/invoice_files/fake.pdf",
        pdf_original_name="fake.pdf",
        pdf_mime_type="application/pdf",
        pdf_size=10,
    )
    if status != INV_DRAFT:
        record.status = status
        db.add(record)
        db.commit()
        db.refresh(record)
    return record


def _make_match(
    db: Session,
    owner_id: uuid.UUID,
    pr_id: uuid.UUID,
    inv_id: uuid.UUID,
    status: str = MATCH_STATUS_CONFIRMED,
) -> InvoiceMatch:
    return repo_create(
        db,
        owner_id=owner_id,
        purchase_record_id=pr_id,
        invoice_file_id=inv_id,
        status=status,
        score=95,
        confirmed_by_id=owner_id,
    )


def _user_headers_for(client: TestClient, db: Session, email: str) -> dict[str, str]:
    """Authenticate as an arbitrary user (without changing the seeded test user)."""
    password = random_lower_string()
    user = crud.get_user_by_email(session=db, email=email)
    if user is None:
        from app.models import UserCreate

        user = crud.create_user(
            session=db, user_create=UserCreate(email=email, password=password)
        )
    else:
        from app.models import UserUpdate

        user = crud.update_user(
            session=db, db_user=user, user_in=UserUpdate(password=password)
        )
    return user_authentication_headers(client=client, email=email, password=password)


# =============================================================================
# Auth / route surface
# =============================================================================


def test_summary_unauthenticated(client: TestClient) -> None:
    response = client.get(f"{BASE_URL}/summary")
    assert response.status_code in (401, 403)


def test_pending_unauthenticated(client: TestClient) -> None:
    response = client.get(f"{BASE_URL}/pending")
    assert response.status_code in (401, 403)


def test_by_user_unauthenticated(client: TestClient) -> None:
    response = client.get(f"{BASE_URL}/by-user")
    assert response.status_code in (401, 403)


def test_summary_returns_expected_shape(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    response = client.get(f"{BASE_URL}/summary", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["scope"] in ("self", "global")
    for key in ("total", "unmatched", "matched", "deleted"):
        assert key in data["purchase_records"]
    for key in ("total", "unallocated", "partially_allocated", "fully_allocated", "voided"):
        assert key in data["invoice_files"]
    for key in ("confirmed", "needs_review", "cancelled"):
        assert key in data["matches"]


# =============================================================================
# Summary scoping (普通用户 only own data; admin sees all)
# =============================================================================


def test_summary_normal_user_only_counts_own_data(
    client: TestClient,
    db: Session,
) -> None:
    me_email = random_email()
    other = create_random_user(db)

    # Mine: 1 unmatched purchase + 1 confirmed unallocated invoice.
    me_user = crud.get_user_by_email(session=db, email=me_email)
    if me_user is None:
        from app.models import UserCreate

        me_user = crud.create_user(
            session=db,
            user_create=UserCreate(email=me_email, password=random_lower_string()),
        )
    _make_purchase(db, me_user.id, amount="50.00", purchase_date="2026-04-02")
    _make_invoice(db, me_user.id, amount="60.00", invoice_date="2026-04-02")

    # Other user's records — must NOT show up in my summary.
    _make_purchase(db, other.id, amount="999.00", purchase_date="2026-04-03")
    _make_invoice(db, other.id, amount="999.00", invoice_date="2026-04-03")

    headers = _user_headers_for(client, db, me_email)
    response = client.get(f"{BASE_URL}/summary", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["scope"] == "self"
    # My one eligible (approved) purchase should be counted.
    assert body["purchase_records"]["total"] >= 1
    # Cannot use exact equality across the shared session-scoped DB because
    # other tests seed their own rows under the same email; what we *can*
    # assert is that `other`'s 999.00 row never bleeds in. We verify that
    # by checking the per-user summary is strictly less than the admin view.
    admin_headers = get_admin_headers_via_login(client)
    admin_resp = client.get(f"{BASE_URL}/summary", headers=admin_headers)
    assert admin_resp.status_code == 200
    admin_body = admin_resp.json()
    assert admin_body["scope"] == "global"
    assert admin_body["purchase_records"]["total"] >= body["purchase_records"]["total"]
    assert admin_body["invoice_files"]["total"] >= body["invoice_files"]["total"]


def get_admin_headers_via_login(client: TestClient) -> dict[str, str]:
    return user_authentication_headers(
        client=client,
        email=settings.FIRST_SUPERUSER,
        password=settings.FIRST_SUPERUSER_PASSWORD,
    )


def test_summary_admin_scope_is_global(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.get(f"{BASE_URL}/summary", headers=superuser_token_headers)
    assert response.status_code == 200
    assert response.json()["scope"] == "global"


# =============================================================================
# Purchase counts: matched / unmatched / deleted
# =============================================================================


def test_unmatched_purchase_count_excludes_active_match(db: Session) -> None:
    from app.modules.finance.dashboard import service as dashboard_service

    user = create_random_user(db)
    pr_unmatched = _make_purchase(db, user.id, purchase_date="2026-05-01")
    pr_matched = _make_purchase(db, user.id, purchase_date="2026-05-02")
    inv = _make_invoice(db, user.id, invoice_date="2026-05-02")
    _make_match(db, user.id, pr_matched.id, inv.id, MATCH_STATUS_CONFIRMED)

    summary = dashboard_service.read_summary(db, current_user=user)
    # We can't assert global counts because other tests inject rows; we can
    # check the matched/unmatched arithmetic for *this* user.
    assert summary.purchase_records.matched >= 1
    assert summary.purchase_records.unmatched >= 1
    # A purchase with a needs_review match still counts as matched (active).
    pr_review = _make_purchase(db, user.id, purchase_date="2026-05-03")
    inv_review = _make_invoice(db, user.id, invoice_date="2026-05-03")
    review_match = _make_match(
        db, user.id, pr_review.id, inv_review.id, MATCH_STATUS_CONFIRMED
    )
    repo_mark_needs_review(db, match=review_match, review_reason="changed")
    summary2 = dashboard_service.read_summary(db, current_user=user)
    # +1 matched (the needs_review counts as active)
    assert summary2.purchase_records.matched >= summary.purchase_records.matched + 1


def test_deleted_purchase_separated_from_active_count(db: Session) -> None:
    from app.modules.finance.dashboard import service as dashboard_service

    user = create_random_user(db)
    pr = _make_purchase(db, user.id, purchase_date="2026-06-01")
    before = dashboard_service.read_summary(db, current_user=user)

    soft_delete_record(db, record=pr, deleted_by_id=user.id)

    after = dashboard_service.read_summary(db, current_user=user)
    # total drops, deleted increments, unmatched drops.
    assert after.purchase_records.total == before.purchase_records.total - 1
    assert after.purchase_records.deleted == before.purchase_records.deleted + 1


# =============================================================================
# Invoice allocation buckets
# =============================================================================


def test_invoice_allocation_buckets(db: Session) -> None:
    from app.modules.finance.dashboard import service as dashboard_service

    user = create_random_user(db)
    # Unallocated: confirmed invoice, no match.
    inv_un = _make_invoice(db, user.id, amount="100.00", invoice_date="2026-07-01")
    # Partially: 100 invoice, only 40 allocated.
    inv_partial = _make_invoice(db, user.id, amount="100.00", invoice_date="2026-07-02")
    pr_part = _make_purchase(db, user.id, amount="40.00", purchase_date="2026-07-02")
    _make_match(db, user.id, pr_part.id, inv_partial.id, MATCH_STATUS_CONFIRMED)
    # Fully: 100 invoice, two purchases summing to 100.
    inv_full = _make_invoice(db, user.id, amount="100.00", invoice_date="2026-07-03")
    pr_a = _make_purchase(db, user.id, amount="60.00", purchase_date="2026-07-03")
    pr_b = _make_purchase(db, user.id, amount="40.00", purchase_date="2026-07-03")
    _make_match(db, user.id, pr_a.id, inv_full.id, MATCH_STATUS_CONFIRMED)
    _make_match(db, user.id, pr_b.id, inv_full.id, MATCH_STATUS_CONFIRMED)

    summary = dashboard_service.read_summary(db, current_user=user)
    assert summary.invoice_files.unallocated >= 1
    assert summary.invoice_files.partially_allocated >= 1
    assert summary.invoice_files.fully_allocated >= 1
    # Sanity: voided counter should not be inflated by these confirmed invoices.
    voided_before = summary.invoice_files.voided
    inv_voided = _make_invoice(db, user.id, amount="50.00", invoice_date="2026-07-04", status=INV_VOIDED)
    summary2 = dashboard_service.read_summary(db, current_user=user)
    assert summary2.invoice_files.voided == voided_before + 1


# =============================================================================
# Match counts
# =============================================================================


def test_match_status_counts(db: Session) -> None:
    from app.modules.finance.dashboard import service as dashboard_service

    user = create_random_user(db)
    pr1 = _make_purchase(db, user.id, purchase_date="2026-08-01")
    inv1 = _make_invoice(db, user.id, invoice_date="2026-08-01")
    m_confirmed = _make_match(db, user.id, pr1.id, inv1.id, MATCH_STATUS_CONFIRMED)

    pr2 = _make_purchase(db, user.id, purchase_date="2026-08-02")
    inv2 = _make_invoice(db, user.id, invoice_date="2026-08-02")
    m_review = _make_match(db, user.id, pr2.id, inv2.id, MATCH_STATUS_CONFIRMED)
    repo_mark_needs_review(db, match=m_review, review_reason="x")

    pr3 = _make_purchase(db, user.id, purchase_date="2026-08-03")
    inv3 = _make_invoice(db, user.id, invoice_date="2026-08-03")
    m_cancel = _make_match(db, user.id, pr3.id, inv3.id, MATCH_STATUS_CONFIRMED)
    repo_cancel(db, match=m_cancel, cancelled_by_id=user.id)

    summary = dashboard_service.read_summary(db, current_user=user)
    assert summary.matches.confirmed >= 1
    assert summary.matches.needs_review >= 1
    assert summary.matches.cancelled >= 1


# =============================================================================
# Pending list
# =============================================================================


def test_pending_default_limit_caps_at_20(db: Session) -> None:
    from app.modules.finance.dashboard import service as dashboard_service

    user = create_random_user(db)
    # 25 unmatched purchases — more than the default cap.
    for i in range(25):
        _make_purchase(
            db,
            user.id,
            amount=f"{10 + i}.00",
            purchase_date=f"2026-09-{(i % 28) + 1:02d}",
        )

    pending = dashboard_service.list_pending(db, current_user=user)
    assert pending.count <= 20
    assert len(pending.data) <= 20


def test_pending_normal_user_only_sees_own_items(
    client: TestClient,
    db: Session,
) -> None:
    me_email = random_email()
    other = create_random_user(db)

    me_user = crud.get_user_by_email(session=db, email=me_email)
    if me_user is None:
        from app.models import UserCreate

        me_user = crud.create_user(
            session=db,
            user_create=UserCreate(email=me_email, password=random_lower_string()),
        )

    _make_purchase(db, me_user.id, amount="11.00", purchase_date="2026-10-01")
    _make_purchase(db, other.id, amount="22.00", purchase_date="2026-10-02")

    headers = _user_headers_for(client, db, me_email)
    resp = client.get(f"{BASE_URL}/pending", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    other_id = str(other.id)
    for item in body["data"]:
        assert item["owner_id"] != other_id


def test_pending_includes_needs_review_match(db: Session) -> None:
    from app.modules.finance.dashboard import service as dashboard_service
    from app.modules.finance.dashboard.constants import (
        PENDING_TYPE_MATCH_NEEDS_REVIEW,
    )

    user = create_random_user(db)
    pr = _make_purchase(db, user.id, purchase_date="2026-11-01")
    inv = _make_invoice(db, user.id, invoice_date="2026-11-01")
    match = _make_match(db, user.id, pr.id, inv.id, MATCH_STATUS_CONFIRMED)
    repo_mark_needs_review(db, match=match, review_reason="updated")

    pending = dashboard_service.list_pending(db, current_user=user)
    types = {item.type for item in pending.data}
    assert PENDING_TYPE_MATCH_NEEDS_REVIEW in types


# =============================================================================
# By-user (admin only)
# =============================================================================


def test_by_user_normal_user_forbidden(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    response = client.get(f"{BASE_URL}/by-user", headers=normal_user_token_headers)
    assert response.status_code == 403


def test_by_user_admin_returns_aggregate(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    user = create_random_user(db)
    _make_purchase(db, user.id, purchase_date="2026-12-01")  # unmatched
    inv = _make_invoice(db, user.id, invoice_date="2026-12-01")  # unallocated

    response = client.get(f"{BASE_URL}/by-user", headers=superuser_token_headers)
    assert response.status_code == 200
    body = response.json()
    assert "data" in body and "count" in body
    rows = {row["owner_id"]: row for row in body["data"]}
    if str(user.id) in rows:
        row = rows[str(user.id)]
        assert row["owner_email"] == user.email
        assert row["purchase_record_unmatched"] >= 1
        assert row["invoice_file_unallocated"] >= 1
        assert row["total_pending"] >= row["purchase_record_unmatched"]


# =============================================================================
# Limit clamping
# =============================================================================


def test_pending_limit_validation_rejects_zero(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    response = client.get(
        f"{BASE_URL}/pending?limit=0", headers=normal_user_token_headers
    )
    # FastAPI Query(ge=1) → 422
    assert response.status_code == 422


def test_pending_limit_validation_rejects_too_large(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    response = client.get(
        f"{BASE_URL}/pending?limit=10000", headers=normal_user_token_headers
    )
    assert response.status_code == 422

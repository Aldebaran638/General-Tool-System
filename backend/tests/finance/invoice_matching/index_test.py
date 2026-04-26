"""
backend/tests/finance/invoice_matching/index_test.py
invoice_matching tool main test file
"""

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.modules.finance.invoice_files.constants import STATUS_CONFIRMED as INV_CONFIRMED, STATUS_DRAFT as INV_DRAFT
from app.modules.finance.invoice_files.models import InvoiceFile
from app.modules.finance.invoice_files.repository import create_record as create_invoice
from app.modules.finance.invoice_files.schemas import InvoiceFileCreate
from app.modules.finance.invoice_matching.constants import (
    MATCH_STATUS_CANCELLED,
    MATCH_STATUS_CONFIRMED,
    MATCH_STATUS_NEEDS_REVIEW,
)
from app.modules.finance.invoice_matching.models import InvoiceMatch
from app.modules.finance.invoice_matching.repository import (
    cancel_match as repo_cancel,
    create_match as repo_create,
    get_match as repo_get,
    mark_matches_needing_review_for_purchase_record,
)
from app.modules.finance.purchase_records.constants import STATUS_APPROVED as PR_APPROVED, STATUS_DRAFT as PR_DRAFT
from app.modules.finance.purchase_records.models import PurchaseRecord
from app.modules.finance.purchase_records.repository import create_record as create_purchase
from app.modules.finance.purchase_records.schemas import PurchaseRecordCreate
from tests.utils.user import create_random_user

BASE_URL = f"{settings.API_V1_STR}/finance/invoice-matching"


def _make_purchase(
    db: Session,
    owner_id: uuid.UUID,
    amount: str = "123.45",
    currency: str = "CNY",
    purchase_date: str = "2026-04-24",
    status: str = PR_APPROVED,
    deleted_at=None,
) -> PurchaseRecord:
    data = PurchaseRecordCreate(
        purchase_date=purchase_date,
        amount=amount,
        currency=currency,
        order_name="Test Order",
        category="meals_entertainment",
        subcategory=None,
        note=None,
    )
    record = create_purchase(
        session=db,
        record_in=data,
        owner_id=owner_id,
        screenshot_path="finance/purchase_records/fake.png",
        screenshot_original_name="fake.png",
        screenshot_mime_type="image/png",
        screenshot_size=100,
    )
    if status != PR_DRAFT:
        record.status = status
    if deleted_at is not None:
        record.deleted_at = deleted_at
    if status != PR_DRAFT or deleted_at is not None:
        db.add(record)
        db.commit()
        db.refresh(record)
    return record


def _make_invoice(
    db: Session,
    owner_id: uuid.UUID,
    amount: str = "123.45",
    currency: str = "CNY",
    invoice_date: str = "2026-04-24",
    status: str = INV_CONFIRMED,
    deleted_at=None,
) -> InvoiceFile:
    data = InvoiceFileCreate(
        invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
        invoice_date=invoice_date,
        invoice_amount=amount,
        tax_amount="10.00",
        currency=currency,
        buyer="Test Buyer",
        seller="Test Seller",
        invoice_type="general",
        note=None,
    )
    record = create_invoice(
        session=db,
        record_in=data,
        owner_id=owner_id,
        pdf_path="finance/invoice_files/fake.pdf",
        pdf_original_name="fake.pdf",
        pdf_mime_type="application/pdf",
        pdf_size=100,
    )
    if status != INV_DRAFT:
        record.status = status
    if deleted_at is not None:
        record.deleted_at = deleted_at
    if status != INV_DRAFT or deleted_at is not None:
        db.add(record)
        db.commit()
        db.refresh(record)
    return record


def _make_match(db: Session, owner_id: uuid.UUID, pr_id: uuid.UUID, inv_id: uuid.UUID, status: str = MATCH_STATUS_CONFIRMED) -> InvoiceMatch:
    return repo_create(
        db,
        owner_id=owner_id,
        purchase_record_id=pr_id,
        invoice_file_id=inv_id,
        status=status,
        score=95,
        confirmed_by_id=owner_id,
    )


# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------


def test_summary_auth(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    response = client.get(f"{BASE_URL}/summary", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "total_confirmed" in data
    assert "total_cancelled" in data
    assert "total_needs_review" in data
    assert "total_unmatched_purchase_records" in data
    assert "total_available_invoices" in data


def test_summary_unauthenticated(client: TestClient) -> None:
    response = client.get(f"{BASE_URL}/summary")
    assert response.status_code in (401, 403)


# -----------------------------------------------------------------------------
# Unmatched Purchase Records
# -----------------------------------------------------------------------------


def test_unmatched_purchase_records_empty(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    response = client.get(f"{BASE_URL}/unmatched-purchase-records", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["data"] == []


# -----------------------------------------------------------------------------
# Available Invoices
# -----------------------------------------------------------------------------


def test_available_invoices_empty(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    response = client.get(f"{BASE_URL}/available-invoices", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0


# -----------------------------------------------------------------------------
# Candidates
# -----------------------------------------------------------------------------


def test_candidates_missing_params(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    response = client.get(f"{BASE_URL}/candidates", headers=normal_user_token_headers)
    assert response.status_code == 422


def test_candidates_not_found(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    response = client.get(
        f"{BASE_URL}/candidates",
        headers=normal_user_token_headers,
        params={"purchase_record_id": str(uuid.uuid4())},
    )
    assert response.status_code == 404


# -----------------------------------------------------------------------------
# Matches (list)
# -----------------------------------------------------------------------------


def test_read_matches_empty(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    response = client.get(f"{BASE_URL}/matches", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0


def test_read_matches_unauthenticated(client: TestClient) -> None:
    response = client.get(f"{BASE_URL}/matches")
    assert response.status_code in (401, 403)


# -----------------------------------------------------------------------------
# Confirm
# -----------------------------------------------------------------------------


def test_confirm_match_unauthenticated(client: TestClient) -> None:
    response = client.post(
        f"{BASE_URL}/confirm",
        json={"purchase_record_id": str(uuid.uuid4()), "invoice_file_id": str(uuid.uuid4())},
    )
    assert response.status_code in (401, 403)


def test_confirm_match_not_found_purchase(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    # Body contains only the documented fields. Backend rejects unknown fields
    # via extra="forbid" — see test_confirm_rejects_extra_score_fields.
    response = client.post(
        f"{BASE_URL}/confirm",
        headers=normal_user_token_headers,
        json={
            "purchase_record_id": str(uuid.uuid4()),
            "invoice_file_id": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 404


# -----------------------------------------------------------------------------
# Cancel
# -----------------------------------------------------------------------------


def test_cancel_match_not_found(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    response = client.post(
        f"{BASE_URL}/{uuid.uuid4()}/cancel",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404


# -----------------------------------------------------------------------------
# Reconfirm
# -----------------------------------------------------------------------------


def test_reconfirm_match_not_found(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    response = client.post(
        f"{BASE_URL}/{uuid.uuid4()}/reconfirm",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404


# -----------------------------------------------------------------------------
# Repository-level integration tests
# -----------------------------------------------------------------------------


def test_create_and_cancel_match(db: Session) -> None:
    user = create_random_user(db)
    pr = _make_purchase(db, user.id)
    inv = _make_invoice(db, user.id)
    match = _make_match(db, user.id, pr.id, inv.id, MATCH_STATUS_CONFIRMED)
    assert match.status == MATCH_STATUS_CONFIRMED
    assert match.purchase_record_id == pr.id
    assert match.invoice_file_id == inv.id

    cancelled = repo_cancel(db, match=match, cancelled_by_id=user.id)
    assert cancelled.status == MATCH_STATUS_CANCELLED
    assert cancelled.cancelled_by_id == user.id


def test_reconfirm_match(db: Session) -> None:
    user = create_random_user(db)
    pr = _make_purchase(db, user.id)
    inv = _make_invoice(db, user.id)
    match = _make_match(db, user.id, pr.id, inv.id, MATCH_STATUS_CONFIRMED)
    from app.modules.finance.invoice_matching.repository import (
        mark_needs_review as repo_mark_needs_review,
        reconfirm_match as repo_reconfirm,
    )
    repo_mark_needs_review(db, match=match, review_reason="test")
    refreshed = repo_get(db, match_id=match.id)
    assert refreshed.status == MATCH_STATUS_NEEDS_REVIEW
    reconfirmed = repo_reconfirm(db, match=refreshed, confirmed_by_id=user.id)
    assert reconfirmed.status == MATCH_STATUS_CONFIRMED
    assert reconfirmed.review_reason is None


def test_mark_needs_review(db: Session) -> None:
    user = create_random_user(db)
    pr = _make_purchase(db, user.id)
    inv = _make_invoice(db, user.id)
    match = _make_match(db, user.id, pr.id, inv.id, MATCH_STATUS_CONFIRMED)
    marked = mark_matches_needing_review_for_purchase_record(
        db, purchase_record_id=pr.id, review_reason="purchase record updated"
    )
    assert marked >= 1
    refreshed = repo_get(db, match_id=match.id)
    assert refreshed.status == MATCH_STATUS_NEEDS_REVIEW
    assert refreshed.review_reason is not None


# -----------------------------------------------------------------------------
# Round 005 hardening: admin write-permission lockout
# -----------------------------------------------------------------------------


def _normal_user(db: Session):
    from app import crud
    return crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)


def test_admin_cannot_confirm_match(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    other = create_random_user(db)
    pr = _make_purchase(db, other.id)
    inv = _make_invoice(db, other.id)
    response = client.post(
        f"{BASE_URL}/confirm",
        headers=superuser_token_headers,
        json={
            "purchase_record_id": str(pr.id),
            "invoice_file_id": str(inv.id),
        },
    )
    assert response.status_code == 403


def test_admin_cannot_cancel_match(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    other = create_random_user(db)
    pr = _make_purchase(db, other.id)
    inv = _make_invoice(db, other.id)
    match = _make_match(db, other.id, pr.id, inv.id, MATCH_STATUS_CONFIRMED)
    response = client.post(
        f"{BASE_URL}/{match.id}/cancel",
        headers=superuser_token_headers,
    )
    assert response.status_code == 403


def test_admin_cannot_reconfirm_match(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    from app.modules.finance.invoice_matching.repository import (
        mark_needs_review as repo_mark_needs_review,
    )

    other = create_random_user(db)
    pr = _make_purchase(db, other.id)
    inv = _make_invoice(db, other.id)
    match = _make_match(db, other.id, pr.id, inv.id, MATCH_STATUS_CONFIRMED)
    repo_mark_needs_review(db, match=match, review_reason="test")
    response = client.post(
        f"{BASE_URL}/{match.id}/reconfirm",
        headers=superuser_token_headers,
    )
    assert response.status_code == 403


# -----------------------------------------------------------------------------
# Round 005 hardening: only confirmed invoices and submitted/approved
# purchases participate in matching surfaces
# -----------------------------------------------------------------------------


def test_available_invoices_only_includes_confirmed(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    from app.modules.finance.invoice_files.constants import STATUS_VOIDED as INV_VOIDED

    user = _normal_user(db)
    inv_draft = _make_invoice(db, user.id, status=INV_DRAFT)
    inv_confirmed = _make_invoice(db, user.id, status=INV_CONFIRMED)
    inv_voided = _make_invoice(db, user.id, status=INV_VOIDED)

    response = client.get(
        f"{BASE_URL}/available-invoices",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    ids = {inv["id"] for inv in response.json()["data"]}
    assert str(inv_confirmed.id) in ids
    assert str(inv_draft.id) not in ids
    assert str(inv_voided.id) not in ids


def test_unmatched_only_includes_submitted_or_approved(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    from app.modules.finance.purchase_records.constants import STATUS_SUBMITTED as PR_SUBMITTED

    user = _normal_user(db)
    pr_draft = _make_purchase(db, user.id, status=PR_DRAFT)
    pr_submitted = _make_purchase(db, user.id, status=PR_SUBMITTED)
    pr_approved = _make_purchase(db, user.id, status=PR_APPROVED)

    response = client.get(
        f"{BASE_URL}/unmatched-purchase-records",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    ids = {pr["id"] for pr in response.json()["data"]}
    assert str(pr_submitted.id) in ids
    assert str(pr_approved.id) in ids
    assert str(pr_draft.id) not in ids


# -----------------------------------------------------------------------------
# Round 005 hardening: candidate filter (date window + currency)
# -----------------------------------------------------------------------------


def test_candidates_excludes_far_dates(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    user = _normal_user(db)
    pr = _make_purchase(
        db, user.id, amount="100.00", currency="CNY", purchase_date="2026-04-10"
    )
    inv_near = _make_invoice(
        db, user.id, amount="100.00", currency="CNY", invoice_date="2026-04-13"
    )  # 3 days
    inv_far = _make_invoice(
        db, user.id, amount="100.00", currency="CNY", invoice_date="2026-04-20"
    )  # 10 days, > 7 day window

    response = client.get(
        f"{BASE_URL}/candidates",
        headers=normal_user_token_headers,
        params={"purchase_record_id": str(pr.id)},
    )
    assert response.status_code == 200
    ids = {c["invoice_file_id"] for c in response.json()["data"]}
    assert str(inv_near.id) in ids
    assert str(inv_far.id) not in ids


def test_candidates_excludes_currency_mismatch(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    user = _normal_user(db)
    pr = _make_purchase(
        db, user.id, amount="100.00", currency="CNY", purchase_date="2026-05-01"
    )
    inv_same = _make_invoice(
        db, user.id, amount="100.00", currency="CNY", invoice_date="2026-05-01"
    )
    inv_other = _make_invoice(
        db, user.id, amount="100.00", currency="USD", invoice_date="2026-05-01"
    )

    response = client.get(
        f"{BASE_URL}/candidates",
        headers=normal_user_token_headers,
        params={"purchase_record_id": str(pr.id)},
    )
    assert response.status_code == 200
    ids = {c["invoice_file_id"] for c in response.json()["data"]}
    assert str(inv_same.id) in ids
    assert str(inv_other.id) not in ids


# -----------------------------------------------------------------------------
# Round 005 hardening: invoice amount allocation and over-allocation
# -----------------------------------------------------------------------------


def test_two_purchases_share_one_invoice(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    user = _normal_user(db)
    inv = _make_invoice(
        db, user.id, amount="100.00", currency="CNY", invoice_date="2026-06-10"
    )
    pr1 = _make_purchase(
        db, user.id, amount="40.00", currency="CNY", purchase_date="2026-06-10"
    )
    pr2 = _make_purchase(
        db, user.id, amount="50.00", currency="CNY", purchase_date="2026-06-10"
    )

    r1 = client.post(
        f"{BASE_URL}/confirm",
        headers=normal_user_token_headers,
        json={"purchase_record_id": str(pr1.id), "invoice_file_id": str(inv.id)},
    )
    assert r1.status_code == 200, r1.text

    r2 = client.post(
        f"{BASE_URL}/confirm",
        headers=normal_user_token_headers,
        json={"purchase_record_id": str(pr2.id), "invoice_file_id": str(inv.id)},
    )
    assert r2.status_code == 200, r2.text

    # Allocation must surface in the candidate query of an unrelated purchase.
    # We pick pr3 with amount equal to the invoice total so it clears the
    # SCORE_THRESHOLD_WEAK gate and the candidate row is returned. The row's
    # allocated/remaining figures still reflect the existing pr1+pr2 matches
    # (90 allocated, 10 remaining) regardless of pr3's own amount.
    pr3 = _make_purchase(
        db, user.id, amount="100.00", currency="CNY", purchase_date="2026-06-10"
    )
    cand = client.get(
        f"{BASE_URL}/candidates",
        headers=normal_user_token_headers,
        params={"purchase_record_id": str(pr3.id)},
    )
    assert cand.status_code == 200
    rows = [c for c in cand.json()["data"] if c["invoice_file_id"] == str(inv.id)]
    assert rows, "invoice should still surface as candidate with remaining amount"
    assert rows[0]["allocated_amount"] in ("90.00", "90")
    assert rows[0]["remaining_amount"] in ("10.00", "10")


def test_over_allocation_rejected(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    user = _normal_user(db)
    inv = _make_invoice(
        db, user.id, amount="100.00", currency="CNY", invoice_date="2026-06-15"
    )
    pr1 = _make_purchase(
        db, user.id, amount="40.00", currency="CNY", purchase_date="2026-06-15"
    )
    pr2 = _make_purchase(
        db, user.id, amount="70.00", currency="CNY", purchase_date="2026-06-15"
    )

    r1 = client.post(
        f"{BASE_URL}/confirm",
        headers=normal_user_token_headers,
        json={"purchase_record_id": str(pr1.id), "invoice_file_id": str(inv.id)},
    )
    assert r1.status_code == 200

    r2 = client.post(
        f"{BASE_URL}/confirm",
        headers=normal_user_token_headers,
        json={"purchase_record_id": str(pr2.id), "invoice_file_id": str(inv.id)},
    )
    # 40 + 70 = 110 > 100 + 0.01 → must be rejected.
    assert r2.status_code == 400, r2.text


# -----------------------------------------------------------------------------
# Round 005 hardening: confirm contract — extras forbidden, score recomputed
# -----------------------------------------------------------------------------


def test_confirm_rejects_extra_score_fields(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    user = _normal_user(db)
    pr = _make_purchase(
        db, user.id, amount="55.00", currency="CNY", purchase_date="2026-07-01"
    )
    inv = _make_invoice(
        db, user.id, amount="55.00", currency="CNY", invoice_date="2026-07-01"
    )
    response = client.post(
        f"{BASE_URL}/confirm",
        headers=normal_user_token_headers,
        json={
            "purchase_record_id": str(pr.id),
            "invoice_file_id": str(inv.id),
            "score": 9999,
            "score_breakdown": {"forged": 9999},
        },
    )
    # Pydantic extra="forbid" → 422 Unprocessable Entity.
    assert response.status_code == 422


def test_confirm_recomputes_score_from_authoritative_state(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    from app.modules.finance.invoice_matching.constants import (
        SCORE_AMOUNT_MATCH,
        SCORE_CURRENCY_MATCH,
        SCORE_DATE_EXACT,
    )

    user = _normal_user(db)
    pr = _make_purchase(
        db,
        user.id,
        amount="77.00",
        currency="CNY",
        purchase_date="2026-07-10",
    )
    inv = _make_invoice(
        db,
        user.id,
        amount="77.00",
        currency="CNY",
        invoice_date="2026-07-10",
    )
    response = client.post(
        f"{BASE_URL}/confirm",
        headers=normal_user_token_headers,
        json={
            "purchase_record_id": str(pr.id),
            "invoice_file_id": str(inv.id),
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    expected_min = SCORE_AMOUNT_MATCH + SCORE_CURRENCY_MATCH + SCORE_DATE_EXACT
    assert body["score"] >= expected_min
    assert body["score_breakdown"].get("amount") == SCORE_AMOUNT_MATCH
    assert body["score_breakdown"].get("currency") == SCORE_CURRENCY_MATCH
    assert body["score_breakdown"].get("date") == SCORE_DATE_EXACT
    # The forged value cannot survive because the route ignores any client-sent
    # score; the previous test already proved the field is rejected outright.


# -----------------------------------------------------------------------------
# Round 005 hardening: needs_review integration with cross-module mutations
# -----------------------------------------------------------------------------


def test_purchase_update_marks_match_needs_review(db: Session) -> None:
    from decimal import Decimal

    from app.modules.finance.purchase_records.schemas import PurchaseRecordUpdate
    from app.modules.finance.purchase_records.service import update_record as pr_update

    user = create_random_user(db)
    # PR must be draft for update_record to allow the edit. The match-against-
    # draft-PR shape is artificial but exercises the hook truthfully.
    pr = _make_purchase(
        db,
        user.id,
        amount="100.00",
        currency="CNY",
        purchase_date="2026-08-01",
        status=PR_DRAFT,
    )
    inv = _make_invoice(
        db, user.id, amount="100.00", currency="CNY", invoice_date="2026-08-01"
    )
    match = _make_match(db, user.id, pr.id, inv.id, MATCH_STATUS_CONFIRMED)

    pr_update(
        db,
        current_user=user,
        record_id=pr.id,
        record_in=PurchaseRecordUpdate(amount=Decimal("110.00")),
        screenshot=None,
    )

    refreshed = repo_get(db, match_id=match.id)
    assert refreshed.status == MATCH_STATUS_NEEDS_REVIEW
    assert refreshed.review_reason is not None


def test_purchase_delete_marks_match_needs_review(db: Session) -> None:
    from app.modules.finance.purchase_records.service import delete_record as pr_delete

    user = create_random_user(db)
    pr = _make_purchase(db, user.id)
    inv = _make_invoice(db, user.id)
    match = _make_match(db, user.id, pr.id, inv.id, MATCH_STATUS_CONFIRMED)

    pr_delete(db, current_user=user, record_id=pr.id)

    refreshed = repo_get(db, match_id=match.id)
    assert refreshed.status == MATCH_STATUS_NEEDS_REVIEW
    assert refreshed.review_reason is not None


def test_invoice_void_marks_match_needs_review(db: Session) -> None:
    from app.modules.finance.invoice_files.service import void_record as inv_void

    user = create_random_user(db)
    pr = _make_purchase(db, user.id)
    inv = _make_invoice(db, user.id)
    match = _make_match(db, user.id, pr.id, inv.id, MATCH_STATUS_CONFIRMED)

    inv_void(db, current_user=user, record_id=inv.id)

    refreshed = repo_get(db, match_id=match.id)
    assert refreshed.status == MATCH_STATUS_NEEDS_REVIEW
    assert refreshed.review_reason is not None


def test_invoice_delete_marks_match_needs_review(db: Session) -> None:
    from app.modules.finance.invoice_files.service import delete_record as inv_delete

    user = create_random_user(db)
    pr = _make_purchase(db, user.id)
    inv = _make_invoice(db, user.id)
    match = _make_match(db, user.id, pr.id, inv.id, MATCH_STATUS_CONFIRMED)

    inv_delete(db, current_user=user, record_id=inv.id)

    refreshed = repo_get(db, match_id=match.id)
    assert refreshed.status == MATCH_STATUS_NEEDS_REVIEW
    assert refreshed.review_reason is not None


# -----------------------------------------------------------------------------
# Round 005 patch: matching eligibility lifecycle
# -----------------------------------------------------------------------------


def test_candidates_rejects_draft_purchase(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    user = _normal_user(db)
    pr = _make_purchase(
        db,
        user.id,
        amount="100.00",
        currency="CNY",
        purchase_date="2026-09-01",
        status=PR_DRAFT,
    )
    response = client.get(
        f"{BASE_URL}/candidates",
        headers=normal_user_token_headers,
        params={"purchase_record_id": str(pr.id)},
    )
    assert response.status_code == 400
    assert "not eligible" in response.json()["detail"].lower()


def test_candidates_rejects_rejected_purchase(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    from app.modules.finance.purchase_records.constants import STATUS_REJECTED as PR_REJECTED

    user = _normal_user(db)
    pr = _make_purchase(
        db,
        user.id,
        amount="100.00",
        currency="CNY",
        purchase_date="2026-09-02",
        status=PR_REJECTED,
    )
    response = client.get(
        f"{BASE_URL}/candidates",
        headers=normal_user_token_headers,
        params={"purchase_record_id": str(pr.id)},
    )
    assert response.status_code == 400
    assert "not eligible" in response.json()["detail"].lower()


def test_invoice_withdraw_confirmation_marks_match_needs_review(db: Session) -> None:
    from app.modules.finance.invoice_files.service import (
        withdraw_confirmation as inv_withdraw,
    )

    user = create_random_user(db)
    pr = _make_purchase(db, user.id)
    inv = _make_invoice(db, user.id)
    match = _make_match(db, user.id, pr.id, inv.id, MATCH_STATUS_CONFIRMED)

    inv_withdraw(db, current_user=user, record_id=inv.id)

    refreshed = repo_get(db, match_id=match.id)
    assert refreshed.status == MATCH_STATUS_NEEDS_REVIEW
    assert refreshed.review_reason is not None


def test_purchase_withdraw_marks_match_needs_review(db: Session) -> None:
    from app.modules.finance.purchase_records.constants import STATUS_SUBMITTED as PR_SUBMITTED
    from app.modules.finance.purchase_records.service import (
        withdraw_record as pr_withdraw,
    )

    user = create_random_user(db)
    # Submitted is the only status that withdraw_record will accept.
    pr = _make_purchase(db, user.id, status=PR_SUBMITTED)
    inv = _make_invoice(db, user.id)
    match = _make_match(db, user.id, pr.id, inv.id, MATCH_STATUS_CONFIRMED)

    pr_withdraw(db, current_user=user, record_id=pr.id)

    refreshed = repo_get(db, match_id=match.id)
    assert refreshed.status == MATCH_STATUS_NEEDS_REVIEW
    assert refreshed.review_reason is not None


def test_purchase_reject_marks_match_needs_review(db: Session) -> None:
    from app import crud
    from app.modules.finance.purchase_records.constants import STATUS_SUBMITTED as PR_SUBMITTED
    from app.modules.finance.purchase_records.service import reject_record as pr_reject

    owner = create_random_user(db)
    admin = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert admin is not None and admin.is_superuser

    pr = _make_purchase(db, owner.id, status=PR_SUBMITTED)
    inv = _make_invoice(db, owner.id)
    match = _make_match(db, owner.id, pr.id, inv.id, MATCH_STATUS_CONFIRMED)

    pr_reject(db, current_user=admin, record_id=pr.id)

    refreshed = repo_get(db, match_id=match.id)
    assert refreshed.status == MATCH_STATUS_NEEDS_REVIEW
    assert refreshed.review_reason is not None

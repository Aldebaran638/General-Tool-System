"""
Purchase Records Service

Business logic layer for the purchase_records tool module.
"""

import uuid

from fastapi import HTTPException, UploadFile
from sqlmodel import Session

from app.models_core import User

from . import repository
from .constants import (
    CATEGORY_OTHER_PROJECT,
    STATUS_APPROVED,
    STATUS_DRAFT,
    STATUS_REJECTED,
    STATUS_SUBMITTED,
    VALID_CATEGORIES,
    VALID_CURRENCIES,
    VALID_SUBCATEGORIES,
)
from .models import PurchaseRecord
from .schemas import (
    Message,
    OCRPreviewResponse,
    PurchaseRecordCreate,
    PurchaseRecordUpdate,
    PurchaseRecordsPublic,
)
from .storage import delete_screenshot, save_screenshot


# =============================================================================
# Validation Helpers
# =============================================================================


def _validate_category_subcategory(*, category: str, subcategory: str | None) -> None:
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"Invalid category: {category}")
    if category == CATEGORY_OTHER_PROJECT:
        if subcategory is not None and subcategory != "" and subcategory not in VALID_SUBCATEGORIES:
            raise HTTPException(
                status_code=422, detail=f"Invalid subcategory: {subcategory}"
            )
    else:
        if subcategory is not None and subcategory != "":
            raise HTTPException(
                status_code=422,
                detail="subcategory must be empty when category is not other_project",
            )


def _validate_currency(*, currency: str) -> None:
    if currency not in VALID_CURRENCIES:
        raise HTTPException(status_code=422, detail=f"Invalid currency: {currency}")


# =============================================================================
# Access Control Helpers
# =============================================================================


def _require_record_access(
    *, record: PurchaseRecord | None, current_user: User
) -> PurchaseRecord:
    if not record:
        raise HTTPException(status_code=404, detail="Purchase record not found")
    # Deleted records are only visible to the deleter
    if record.deleted_at is not None:
        if record.deleted_by_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return record
    # Normal records: owner sees own; superuser sees all
    if not current_user.is_superuser and record.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return record


# =============================================================================
# Service Functions
# =============================================================================


def read_records(
    session: Session,
    *,
    current_user: User,
    skip: int = 0,
    limit: int = 100,
    deleted: bool = False,
) -> PurchaseRecordsPublic:
    if deleted:
        # Only the deleter can see deleted records
        count = repository.count_records(
            session, deleted=True, deleted_by_id=current_user.id
        )
        records = repository.list_records(
            session,
            skip=skip,
            limit=limit,
            deleted=True,
            deleted_by_id=current_user.id,
        )
    else:
        owner_id = None if current_user.is_superuser else current_user.id
        count = repository.count_records(session, owner_id=owner_id, deleted=False)
        records = repository.list_records(
            session,
            skip=skip,
            limit=limit,
            owner_id=owner_id,
            deleted=False,
        )
    return PurchaseRecordsPublic(data=records, count=count)


def read_record(
    session: Session, *, current_user: User, record_id: uuid.UUID
) -> PurchaseRecord:
    record = repository.get_record(session, record_id=record_id)
    return _require_record_access(record=record, current_user=current_user)


def create_record(
    session: Session,
    *,
    current_user: User,
    record_in: PurchaseRecordCreate,
    screenshot: UploadFile,
) -> PurchaseRecord:
    _validate_currency(currency=record_in.currency)
    _validate_category_subcategory(
        category=record_in.category, subcategory=record_in.subcategory
    )

    path, orig_name, mime, size = save_screenshot(file=screenshot)
    return repository.create_record(
        session,
        record_in=record_in,
        owner_id=current_user.id,
        screenshot_path=path,
        screenshot_original_name=orig_name,
        screenshot_mime_type=mime,
        screenshot_size=size,
    )


def update_record(
    session: Session,
    *,
    current_user: User,
    record_id: uuid.UUID,
    record_in: PurchaseRecordUpdate,
    screenshot: UploadFile | None = None,
) -> PurchaseRecord:
    record = repository.get_record(session, record_id=record_id)
    record = _require_record_access(record=record, current_user=current_user)

    if record.status not in (STATUS_DRAFT, STATUS_REJECTED):
        raise HTTPException(
            status_code=403,
            detail="Only draft or rejected records can be edited",
        )

    # Only owner can edit business fields (admin does not edit on behalf)
    if record.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    update_dict = record_in.model_dump(exclude_unset=True)
    category = update_dict.get("category", record.category)
    subcategory = update_dict.get("subcategory", record.subcategory)
    _validate_category_subcategory(category=category, subcategory=subcategory)

    if "currency" in update_dict:
        _validate_currency(currency=update_dict["currency"])

    if screenshot is not None:
        # Delete old screenshot and save new one
        delete_screenshot(relative_path=record.screenshot_path)
        path, orig_name, mime, size = save_screenshot(file=screenshot)
        record.screenshot_path = path
        record.screenshot_original_name = orig_name
        record.screenshot_mime_type = mime
        record.screenshot_size = size

    updated = repository.update_record(session, record=record, record_in=record_in)

    # Cross-module hook: any active match referencing this record must be
    # re-reviewed because key fields may have changed.
    from app.modules.finance.invoice_matching.service import (
        mark_needs_review_for_purchase_record,
    )

    mark_needs_review_for_purchase_record(
        session,
        purchase_record_id=updated.id,
        review_reason="purchase record updated",
    )
    session.refresh(updated)

    return updated


def submit_record(
    session: Session, *, current_user: User, record_id: uuid.UUID
) -> PurchaseRecord:
    record = repository.get_record(session, record_id=record_id)
    record = _require_record_access(record=record, current_user=current_user)
    if record.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if record.status not in (STATUS_DRAFT, STATUS_REJECTED):
        raise HTTPException(
            status_code=403,
            detail="Only draft or rejected records can be submitted",
        )
    return repository.update_record_status(session, record=record, status=STATUS_SUBMITTED)


def withdraw_record(
    session: Session, *, current_user: User, record_id: uuid.UUID
) -> PurchaseRecord:
    record = repository.get_record(session, record_id=record_id)
    record = _require_record_access(record=record, current_user=current_user)
    if record.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if record.status != STATUS_SUBMITTED:
        raise HTTPException(
            status_code=403,
            detail="Only submitted records can be withdrawn",
        )
    updated = repository.update_record_status(session, record=record, status=STATUS_DRAFT)

    from app.modules.finance.invoice_matching.service import (
        mark_needs_review_for_purchase_record,
    )

    mark_needs_review_for_purchase_record(
        session,
        purchase_record_id=updated.id,
        review_reason="purchase record withdrawn to draft",
    )
    session.refresh(updated)

    return updated


def approve_record(
    session: Session, *, current_user: User, record_id: uuid.UUID
) -> PurchaseRecord:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    record = repository.get_record(session, record_id=record_id)
    record = _require_record_access(record=record, current_user=current_user)
    if record.status != STATUS_SUBMITTED:
        raise HTTPException(
            status_code=403,
            detail="Only submitted records can be approved",
        )
    return repository.update_record_status(session, record=record, status=STATUS_APPROVED)


def reject_record(
    session: Session, *, current_user: User, record_id: uuid.UUID
) -> PurchaseRecord:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    record = repository.get_record(session, record_id=record_id)
    record = _require_record_access(record=record, current_user=current_user)
    if record.status != STATUS_SUBMITTED:
        raise HTTPException(
            status_code=403,
            detail="Only submitted records can be rejected",
        )
    updated = repository.update_record_status(session, record=record, status=STATUS_REJECTED)

    from app.modules.finance.invoice_matching.service import (
        mark_needs_review_for_purchase_record,
    )

    mark_needs_review_for_purchase_record(
        session,
        purchase_record_id=updated.id,
        review_reason="purchase record rejected",
    )
    session.refresh(updated)

    return updated


def unapprove_record(
    session: Session, *, current_user: User, record_id: uuid.UUID
) -> PurchaseRecord:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    record = repository.get_record(session, record_id=record_id)
    record = _require_record_access(record=record, current_user=current_user)
    if record.status != STATUS_APPROVED:
        raise HTTPException(
            status_code=403,
            detail="Only approved records can be unapproved",
        )
    return repository.update_record_status(session, record=record, status=STATUS_SUBMITTED)


def delete_record(
    session: Session, *, current_user: User, record_id: uuid.UUID
) -> Message:
    record = repository.get_record(session, record_id=record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Purchase record not found")
    # Normal users can delete their own; superusers can delete any
    if not current_user.is_superuser and record.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    repository.soft_delete_record(session, record=record, deleted_by_id=current_user.id)

    from app.modules.finance.invoice_matching.service import (
        mark_needs_review_for_purchase_record,
    )

    mark_needs_review_for_purchase_record(
        session,
        purchase_record_id=record.id,
        review_reason="purchase record deleted",
    )

    return Message(message="Purchase record deleted successfully")


def restore_record(
    session: Session, *, current_user: User, record_id: uuid.UUID
) -> PurchaseRecord:
    record = repository.get_record(session, record_id=record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Purchase record not found")
    if record.deleted_at is None:
        raise HTTPException(status_code=400, detail="Record is not deleted")
    if record.deleted_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    restored = repository.restore_record(session, record=record)

    from app.modules.finance.invoice_matching.service import (
        mark_needs_review_for_purchase_record,
    )

    mark_needs_review_for_purchase_record(
        session,
        purchase_record_id=restored.id,
        review_reason="purchase record restored",
    )
    session.refresh(restored)

    return restored


def purge_deleted_records(
    session: Session, *, current_user: User
) -> Message:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    records = repository.purge_old_deleted_records(session, days=30)
    for record in records:
        delete_screenshot(relative_path=record.screenshot_path)
    return Message(message=f"Purged {len(records)} old deleted records")


def get_screenshot(
    session: Session, *, current_user: User, record_id: uuid.UUID
) -> PurchaseRecord:
    # Reuse read_record for permission check
    return read_record(session, current_user=current_user, record_id=record_id)

"""
Invoice Files Service

Business logic layer for the invoice_files tool module.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile
from sqlmodel import Session

from app.models_core import User

from . import repository
from .constants import STATUS_CONFIRMED, STATUS_DRAFT, STATUS_VOIDED, VALID_CURRENCIES, VALID_INVOICE_TYPES
from .models import InvoiceFile, InvoiceFilePublic
from .schemas import InvoiceFileCreate, InvoiceFileUpdate, InvoiceFilesPublic, Message
from .storage import delete_pdf, save_pdf


# =============================================================================
# Validation Helpers
# =============================================================================


def _validate_invoice_type(*, invoice_type: str) -> None:
    if invoice_type not in VALID_INVOICE_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid invoice_type: {invoice_type}")


def _validate_currency(*, currency: str) -> None:
    if currency not in VALID_CURRENCIES:
        raise HTTPException(status_code=422, detail=f"Invalid currency: {currency}")


def _check_duplicate_invoice_number(
    session: Session,
    *,
    owner_id: uuid.UUID,
    invoice_number: str,
    exclude_id: uuid.UUID | None = None,
) -> None:
    existing = repository.get_record_by_invoice_number(
        session,
        owner_id=owner_id,
        invoice_number=invoice_number,
        exclude_id=exclude_id,
    )
    if existing:
        raise HTTPException(
            status_code=422,
            detail=f"Invoice number '{invoice_number}' already exists for this user",
        )


# =============================================================================
# Access Control
# =============================================================================


def _require_record_access(
    *,
    record: InvoiceFile | None,
    current_user: User,
    allow_deleted: bool = False,
) -> InvoiceFile:
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if not allow_deleted and record.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Record not found")
    # Everyone only sees their own records
    if record.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return record


def _require_owner_access(
    *,
    record: InvoiceFile | None,
    current_user: User,
) -> InvoiceFile:
    """Require that the current user is the owner of the record.

    Admin users are NOT allowed for business write operations.
    """
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return record


# =============================================================================
# Duplicate Info Helpers
# =============================================================================


def _get_duplicate_info(
    session: Session,
    record: InvoiceFile,
    current_user: User,
) -> tuple[str | None, int | None]:
    if not current_user.is_superuser:
        return None, None
    count = repository.count_duplicates(
        session,
        invoice_number=record.invoice_number,
        exclude_owner_id=record.owner_id,
    )
    if count > 0:
        warning = f"Invoice number '{record.invoice_number}' appears in {count} other user(s)"
        return warning, count
    return None, None


def _to_public(
    record: InvoiceFile,
    *,
    duplicate_warning: str | None = None,
    duplicate_invoice_owner_count: int | None = None,
) -> InvoiceFilePublic:
    data = record.model_dump()
    data["duplicate_warning"] = duplicate_warning
    data["duplicate_invoice_owner_count"] = duplicate_invoice_owner_count
    return InvoiceFilePublic.model_validate(data)


# =============================================================================
# Read
# =============================================================================


def read_records(
    session: Session,
    *,
    current_user: User,
    deleted: bool = False,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> InvoiceFilesPublic:
    if deleted:
        count = repository.count_records(
            session,
            deleted=True,
            deleted_by_id=current_user.id,
            status=status,
        )
        records = repository.list_records(
            session,
            deleted=True,
            deleted_by_id=current_user.id,
            status=status,
            skip=skip,
            limit=limit,
        )
    else:
        count = repository.count_records(
            session,
            owner_id=current_user.id,
            deleted=False,
            status=status,
        )
        records = repository.list_records(
            session,
            owner_id=current_user.id,
            deleted=False,
            status=status,
            skip=skip,
            limit=limit,
        )

    public_records = []
    for record in records:
        warning, dup_count = _get_duplicate_info(session, record, current_user)
        public_records.append(_to_public(
            record,
            duplicate_warning=warning,
            duplicate_invoice_owner_count=dup_count,
        ))

    return InvoiceFilesPublic(data=public_records, count=count)


def read_record(
    session: Session,
    *,
    current_user: User,
    record_id: uuid.UUID,
) -> InvoiceFilePublic:
    record = repository.get_record(session, record_id=record_id)
    _require_record_access(record=record, current_user=current_user)
    warning, dup_count = _get_duplicate_info(session, record, current_user)
    return _to_public(
        record,
        duplicate_warning=warning,
        duplicate_invoice_owner_count=dup_count,
    )


# =============================================================================
# Create
# =============================================================================


def create_record(
    session: Session,
    *,
    current_user: User,
    record_in: InvoiceFileCreate,
    pdf: UploadFile,
) -> InvoiceFilePublic:
    _validate_invoice_type(invoice_type=record_in.invoice_type)
    _validate_currency(currency=record_in.currency)
    _check_duplicate_invoice_number(
        session,
        owner_id=current_user.id,
        invoice_number=record_in.invoice_number,
    )

    pdf_path, pdf_original_name, pdf_mime_type, pdf_size = save_pdf(file=pdf)

    record = repository.create_record(
        session,
        record_in=record_in,
        owner_id=current_user.id,
        pdf_path=pdf_path,
        pdf_original_name=pdf_original_name,
        pdf_mime_type=pdf_mime_type,
        pdf_size=pdf_size,
    )

    warning, dup_count = _get_duplicate_info(session, record, current_user)
    return _to_public(
        record,
        duplicate_warning=warning,
        duplicate_invoice_owner_count=dup_count,
    )


# =============================================================================
# Update
# =============================================================================


def update_record(
    session: Session,
    *,
    current_user: User,
    record_id: uuid.UUID,
    record_in: InvoiceFileUpdate,
    pdf: UploadFile | None,
) -> InvoiceFilePublic:
    record = repository.get_record(session, record_id=record_id)
    _require_owner_access(record=record, current_user=current_user)

    if record.status != STATUS_DRAFT:
        raise HTTPException(status_code=403, detail="Only draft records can be edited")

    update_data = record_in.model_dump(exclude_unset=True)

    if "invoice_type" in update_data:
        _validate_invoice_type(invoice_type=update_data["invoice_type"])
    if "currency" in update_data:
        _validate_currency(currency=update_data["currency"])
    if "invoice_number" in update_data:
        _check_duplicate_invoice_number(
            session,
            owner_id=record.owner_id,
            invoice_number=update_data["invoice_number"],
            exclude_id=record.id,
        )

    old_pdf_path = None
    if pdf:
        old_pdf_path = record.pdf_path
        pdf_path, pdf_original_name, pdf_mime_type, pdf_size = save_pdf(file=pdf)
        record.pdf_path = pdf_path
        record.pdf_original_name = pdf_original_name
        record.pdf_mime_type = pdf_mime_type
        record.pdf_size = pdf_size

    try:
        record = repository.update_record(session, record=record, record_in=record_in)
    except Exception:
        if pdf:
            # Rollback: remove the newly saved PDF if DB commit fails
            delete_pdf(relative_path=record.pdf_path)
        raise

    if old_pdf_path:
        delete_pdf(relative_path=old_pdf_path)

    from app.modules.finance.invoice_matching.service import (
        mark_needs_review_for_invoice_file,
    )

    mark_needs_review_for_invoice_file(
        session,
        invoice_file_id=record.id,
        review_reason="invoice file updated",
    )
    # The hook commits, which expires attributes on `record`. Refresh so the
    # response builder below can read the live row.
    session.refresh(record)

    warning, dup_count = _get_duplicate_info(session, record, current_user)
    return _to_public(
        record,
        duplicate_warning=warning,
        duplicate_invoice_owner_count=dup_count,
    )


# =============================================================================
# State Transitions
# =============================================================================


def confirm_record(
    session: Session,
    *,
    current_user: User,
    record_id: uuid.UUID,
) -> InvoiceFilePublic:
    record = repository.get_record(session, record_id=record_id)
    _require_owner_access(record=record, current_user=current_user)
    if record.status != STATUS_DRAFT:
        raise HTTPException(status_code=403, detail="Only draft records can be confirmed")
    record = repository.update_record_status(session, record=record, status=STATUS_CONFIRMED)
    warning, dup_count = _get_duplicate_info(session, record, current_user)
    return _to_public(
        record,
        duplicate_warning=warning,
        duplicate_invoice_owner_count=dup_count,
    )


def withdraw_confirmation(
    session: Session,
    *,
    current_user: User,
    record_id: uuid.UUID,
) -> InvoiceFilePublic:
    record = repository.get_record(session, record_id=record_id)
    _require_owner_access(record=record, current_user=current_user)
    if record.status != STATUS_CONFIRMED:
        raise HTTPException(status_code=403, detail="Only confirmed records can be withdrawn")
    record = repository.update_record_status(session, record=record, status=STATUS_DRAFT)

    from app.modules.finance.invoice_matching.service import (
        mark_needs_review_for_invoice_file,
    )

    mark_needs_review_for_invoice_file(
        session,
        invoice_file_id=record.id,
        review_reason="invoice file withdrawn to draft",
    )
    session.refresh(record)

    warning, dup_count = _get_duplicate_info(session, record, current_user)
    return _to_public(
        record,
        duplicate_warning=warning,
        duplicate_invoice_owner_count=dup_count,
    )


def void_record(
    session: Session,
    *,
    current_user: User,
    record_id: uuid.UUID,
) -> InvoiceFilePublic:
    record = repository.get_record(session, record_id=record_id)
    _require_owner_access(record=record, current_user=current_user)
    if record.status != STATUS_CONFIRMED:
        raise HTTPException(status_code=403, detail="Only confirmed records can be voided")
    record = repository.update_record_status(session, record=record, status=STATUS_VOIDED)

    from app.modules.finance.invoice_matching.service import (
        mark_needs_review_for_invoice_file,
    )

    mark_needs_review_for_invoice_file(
        session,
        invoice_file_id=record.id,
        review_reason="invoice file voided",
    )
    session.refresh(record)

    warning, dup_count = _get_duplicate_info(session, record, current_user)
    return _to_public(
        record,
        duplicate_warning=warning,
        duplicate_invoice_owner_count=dup_count,
    )


def restore_draft(
    session: Session,
    *,
    current_user: User,
    record_id: uuid.UUID,
) -> InvoiceFilePublic:
    record = repository.get_record(session, record_id=record_id)
    _require_owner_access(record=record, current_user=current_user)
    if record.status != STATUS_VOIDED:
        raise HTTPException(status_code=403, detail="Only voided records can be restored to draft")
    record = repository.update_record_status(session, record=record, status=STATUS_DRAFT)

    from app.modules.finance.invoice_matching.service import (
        mark_needs_review_for_invoice_file,
    )

    mark_needs_review_for_invoice_file(
        session,
        invoice_file_id=record.id,
        review_reason="invoice file restored to draft",
    )
    session.refresh(record)

    warning, dup_count = _get_duplicate_info(session, record, current_user)
    return _to_public(
        record,
        duplicate_warning=warning,
        duplicate_invoice_owner_count=dup_count,
    )


# =============================================================================
# Soft Delete / Restore / Purge
# =============================================================================


def delete_record(
    session: Session,
    *,
    current_user: User,
    record_id: uuid.UUID,
) -> Message:
    record = repository.get_record(session, record_id=record_id)
    _require_record_access(record=record, current_user=current_user)
    repository.soft_delete_record(session, record=record, deleted_by_id=current_user.id)

    from app.modules.finance.invoice_matching.service import (
        mark_needs_review_for_invoice_file,
    )

    mark_needs_review_for_invoice_file(
        session,
        invoice_file_id=record.id,
        review_reason="invoice file deleted",
    )

    return Message(message="Invoice file deleted successfully")


def restore_record(
    session: Session,
    *,
    current_user: User,
    record_id: uuid.UUID,
) -> InvoiceFilePublic:
    record = repository.get_record(session, record_id=record_id)
    _require_record_access(record=record, current_user=current_user, allow_deleted=True)
    if record.deleted_by_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    record = repository.restore_record(session, record=record)

    from app.modules.finance.invoice_matching.service import (
        mark_needs_review_for_invoice_file,
    )

    mark_needs_review_for_invoice_file(
        session,
        invoice_file_id=record.id,
        review_reason="invoice file restored",
    )
    session.refresh(record)

    warning, dup_count = _get_duplicate_info(session, record, current_user)
    return _to_public(
        record,
        duplicate_warning=warning,
        duplicate_invoice_owner_count=dup_count,
    )


def purge_deleted_records(
    session: Session,
    *,
    current_user: User,
) -> Message:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    records, pdf_paths = repository.purge_old_deleted_records(session, days=30)
    for path in pdf_paths:
        try:
            delete_pdf(relative_path=path)
        except Exception:
            pass
    return Message(message=f"Purged {len(records)} old deleted invoice file(s)")


# =============================================================================
# PDF Download
# =============================================================================


def get_pdf(
    session: Session,
    *,
    current_user: User,
    record_id: uuid.UUID,
) -> InvoiceFile:
    record = repository.get_record(session, record_id=record_id)
    _require_record_access(record=record, current_user=current_user)
    return record

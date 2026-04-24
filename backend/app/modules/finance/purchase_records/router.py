"""
Purchase Records Router

Interface layer (HTTP endpoints) for the purchase_records tool module.
"""

import uuid
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.deps import CurrentUser, SessionDep

from . import service
from .schemas import (
    Message,
    OCRPreviewResponse,
    PurchaseRecordCreate,
    PurchaseRecordPublic,
    PurchaseRecordsPublic,
    PurchaseRecordUpdate,
)

router = APIRouter(prefix="/finance/purchase-records", tags=["purchase-records"])


# =============================================================================
# OCR Preview
# =============================================================================

@router.post("/ocr-preview", response_model=OCRPreviewResponse)
def ocr_preview(
    *,
    current_user: CurrentUser,
    screenshot: UploadFile = File(...),
) -> Any:
    from .ocr import run_ocr_preview

    return run_ocr_preview(file=screenshot)


# =============================================================================
# List
# =============================================================================

@router.get("/", response_model=PurchaseRecordsPublic)
def read_records(
    session: SessionDep,
    current_user: CurrentUser,
    deleted: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    return service.read_records(
        session,
        current_user=current_user,
        deleted=deleted,
        skip=skip,
        limit=limit,
    )


# =============================================================================
# Detail
# =============================================================================

@router.get("/{id}", response_model=PurchaseRecordPublic)
def read_record(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    return service.read_record(session, current_user=current_user, record_id=id)


# =============================================================================
# Create
# =============================================================================

@router.post("/", response_model=PurchaseRecordPublic)
def create_record(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    purchase_date: str = Form(...),
    amount: str = Form(...),
    currency: str = Form(...),
    order_name: str = Form(...),
    category: str = Form(...),
    subcategory: str | None = Form(None),
    note: str | None = Form(None),
    screenshot: UploadFile = File(...),
) -> Any:
    from datetime import date
    from decimal import Decimal, InvalidOperation

    try:
        parsed_date = date.fromisoformat(purchase_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid purchase_date format")

    try:
        parsed_amount = Decimal(amount)
    except InvalidOperation:
        raise HTTPException(status_code=422, detail="Invalid amount")

    # Treat empty string as None for subcategory
    if subcategory == "":
        subcategory = None

    record_in = PurchaseRecordCreate(
        purchase_date=parsed_date,
        amount=parsed_amount,
        currency=currency,
        order_name=order_name,
        category=category,
        subcategory=subcategory,
        note=note,
    )
    return service.create_record(
        session,
        current_user=current_user,
        record_in=record_in,
        screenshot=screenshot,
    )


# =============================================================================
# Update
# =============================================================================

@router.patch("/{id}", response_model=PurchaseRecordPublic)
def update_record(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    purchase_date: str | None = Form(None),
    amount: str | None = Form(None),
    currency: str | None = Form(None),
    order_name: str | None = Form(None),
    category: str | None = Form(None),
    subcategory: str | None = Form(None),
    note: str | None = Form(None),
    screenshot: UploadFile | None = File(None),
) -> Any:
    from datetime import date
    from decimal import Decimal, InvalidOperation

    update_data: dict[str, Any] = {}
    if purchase_date is not None:
        try:
            update_data["purchase_date"] = date.fromisoformat(purchase_date)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid purchase_date format")
    if amount is not None:
        try:
            update_data["amount"] = Decimal(amount)
        except InvalidOperation:
            raise HTTPException(status_code=422, detail="Invalid amount")
    if currency is not None:
        update_data["currency"] = currency
    if order_name is not None:
        update_data["order_name"] = order_name
    if category is not None:
        update_data["category"] = category
    if subcategory is not None:
        # Treat empty string as explicit clear to None
        update_data["subcategory"] = None if subcategory == "" else subcategory
    if note is not None:
        update_data["note"] = note

    record_in = PurchaseRecordUpdate.model_validate(update_data)
    return service.update_record(
        session,
        current_user=current_user,
        record_id=id,
        record_in=record_in,
        screenshot=screenshot,
    )


# =============================================================================
# State Transitions
# =============================================================================

@router.post("/{id}/submit", response_model=PurchaseRecordPublic)
def submit_record(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    return service.submit_record(session, current_user=current_user, record_id=id)


@router.post("/{id}/withdraw", response_model=PurchaseRecordPublic)
def withdraw_record(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    return service.withdraw_record(session, current_user=current_user, record_id=id)


@router.post("/{id}/approve", response_model=PurchaseRecordPublic)
def approve_record(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    return service.approve_record(session, current_user=current_user, record_id=id)


@router.post("/{id}/reject", response_model=PurchaseRecordPublic)
def reject_record(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    return service.reject_record(session, current_user=current_user, record_id=id)


@router.post("/{id}/unapprove", response_model=PurchaseRecordPublic)
def unapprove_record(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    return service.unapprove_record(session, current_user=current_user, record_id=id)


# =============================================================================
# Soft Delete / Restore / Purge
# =============================================================================

@router.delete("/{id}")
def delete_record(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Message:
    return service.delete_record(session, current_user=current_user, record_id=id)


@router.post("/{id}/restore", response_model=PurchaseRecordPublic)
def restore_record(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    return service.restore_record(session, current_user=current_user, record_id=id)


@router.post("/purge-deleted")
def purge_deleted_records(
    session: SessionDep,
    current_user: CurrentUser,
) -> Message:
    return service.purge_deleted_records(session, current_user=current_user)


# =============================================================================
# Screenshot Download
# =============================================================================

@router.get("/{id}/screenshot")
def download_screenshot(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    from fastapi import HTTPException
    from fastapi.responses import FileResponse

    record = service.get_screenshot(session, current_user=current_user, record_id=id)
    from .storage import get_screenshot_path

    file_path = get_screenshot_path(relative_path=record.screenshot_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Screenshot file not found")
    return FileResponse(
        path=str(file_path),
        filename=record.screenshot_original_name,
        media_type=record.screenshot_mime_type,
    )

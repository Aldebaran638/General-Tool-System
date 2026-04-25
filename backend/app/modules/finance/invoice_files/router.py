"""
Invoice Files Router

Interface layer (HTTP endpoints) for the invoice_files tool module.
"""

import uuid
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.deps import CurrentUser, SessionDep

from . import service
from .schemas import (
    InvoiceFileCreate,
    InvoiceFilePublic,
    InvoiceFilesPublic,
    InvoiceFileUpdate,
    Message,
    ParsePreviewResponse,
)

router = APIRouter(prefix="/finance/invoice-files", tags=["invoice-files"])


# =============================================================================
# Parse Preview
# =============================================================================

@router.post("/parse-preview", response_model=ParsePreviewResponse)
def parse_preview(
    *,
    current_user: CurrentUser,
    pdf: UploadFile = File(...),
) -> Any:
    from .pdf_parser import run_parse_preview
    from .storage import validate_pdf_file

    validate_pdf_file(file=pdf)
    return run_parse_preview(file=pdf)


# =============================================================================
# List
# =============================================================================

@router.get("/", response_model=InvoiceFilesPublic)
def read_records(
    session: SessionDep,
    current_user: CurrentUser,
    deleted: bool = False,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    return service.read_records(
        session,
        current_user=current_user,
        deleted=deleted,
        status=status,
        skip=skip,
        limit=limit,
    )


# =============================================================================
# Detail
# =============================================================================

@router.get("/{id}", response_model=InvoiceFilePublic)
def read_record(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    return service.read_record(session, current_user=current_user, record_id=id)


# =============================================================================
# Create
# =============================================================================

@router.post("/", response_model=InvoiceFilePublic)
def create_record(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    invoice_number: str = Form(...),
    invoice_date: str = Form(...),
    invoice_amount: str = Form(...),
    tax_amount: str = Form("0.00"),
    currency: str = Form(...),
    buyer: str = Form(...),
    seller: str = Form(...),
    invoice_type: str = Form(...),
    note: str | None = Form(None),
    pdf: UploadFile = File(...),
) -> Any:
    from datetime import date
    from decimal import Decimal, InvalidOperation

    try:
        parsed_date = date.fromisoformat(invoice_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid invoice_date format")

    try:
        parsed_amount = Decimal(invoice_amount)
    except InvalidOperation:
        raise HTTPException(status_code=422, detail="Invalid invoice_amount")

    try:
        parsed_tax = Decimal(tax_amount) if tax_amount else Decimal("0.00")
    except InvalidOperation:
        raise HTTPException(status_code=422, detail="Invalid tax_amount")

    record_in = InvoiceFileCreate(
        invoice_number=invoice_number,
        invoice_date=parsed_date,
        invoice_amount=parsed_amount,
        tax_amount=parsed_tax,
        currency=currency,
        buyer=buyer,
        seller=seller,
        invoice_type=invoice_type,
        note=note,
    )
    return service.create_record(
        session,
        current_user=current_user,
        record_in=record_in,
        pdf=pdf,
    )


# =============================================================================
# Update
# =============================================================================

@router.patch("/{id}", response_model=InvoiceFilePublic)
def update_record(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    invoice_number: str | None = Form(None),
    invoice_date: str | None = Form(None),
    invoice_amount: str | None = Form(None),
    tax_amount: str | None = Form(None),
    currency: str | None = Form(None),
    buyer: str | None = Form(None),
    seller: str | None = Form(None),
    invoice_type: str | None = Form(None),
    note: str | None = Form(None),
    pdf: UploadFile | None = File(None),
) -> Any:
    from datetime import date
    from decimal import Decimal, InvalidOperation

    update_data: dict[str, Any] = {}
    if invoice_number is not None:
        update_data["invoice_number"] = invoice_number
    if invoice_date is not None:
        try:
            update_data["invoice_date"] = date.fromisoformat(invoice_date)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid invoice_date format")
    if invoice_amount is not None:
        try:
            update_data["invoice_amount"] = Decimal(invoice_amount)
        except InvalidOperation:
            raise HTTPException(status_code=422, detail="Invalid invoice_amount")
    if tax_amount is not None:
        try:
            update_data["tax_amount"] = Decimal(tax_amount)
        except InvalidOperation:
            raise HTTPException(status_code=422, detail="Invalid tax_amount")
    if currency is not None:
        update_data["currency"] = currency
    if buyer is not None:
        update_data["buyer"] = buyer
    if seller is not None:
        update_data["seller"] = seller
    if invoice_type is not None:
        update_data["invoice_type"] = invoice_type
    if note is not None:
        update_data["note"] = note

    record_in = InvoiceFileUpdate.model_validate(update_data)
    return service.update_record(
        session,
        current_user=current_user,
        record_id=id,
        record_in=record_in,
        pdf=pdf,
    )


# =============================================================================
# State Transitions
# =============================================================================

@router.post("/{id}/confirm", response_model=InvoiceFilePublic)
def confirm_record(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    return service.confirm_record(session, current_user=current_user, record_id=id)


@router.post("/{id}/withdraw-confirmation", response_model=InvoiceFilePublic)
def withdraw_confirmation(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    return service.withdraw_confirmation(session, current_user=current_user, record_id=id)


@router.post("/{id}/void", response_model=InvoiceFilePublic)
def void_record(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    return service.void_record(session, current_user=current_user, record_id=id)


@router.post("/{id}/restore-draft", response_model=InvoiceFilePublic)
def restore_draft(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    return service.restore_draft(session, current_user=current_user, record_id=id)


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


@router.post("/{id}/restore", response_model=InvoiceFilePublic)
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
# PDF Download
# =============================================================================

@router.get("/{id}/pdf")
def download_pdf(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    from fastapi.responses import FileResponse

    record = service.get_pdf(session, current_user=current_user, record_id=id)
    from .storage import get_pdf_path

    file_path = get_pdf_path(relative_path=record.pdf_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    return FileResponse(
        path=str(file_path),
        filename=record.pdf_original_name,
        media_type=record.pdf_mime_type,
    )

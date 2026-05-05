"""
Unified file download router.

Provides type-prefixed endpoints for downloading files across all modules.
"""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, SessionDep

router = APIRouter(prefix="/files", tags=["files"])


# =============================================================================
# Invoice PDFs
# =============================================================================

@router.get("/invoices/{id}")
def download_invoice_file(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    from app.modules.finance.invoice_files import service as invoice_service
    from app.modules.finance.invoice_files.storage import get_pdf_path

    record = invoice_service.get_pdf(session, current_user=current_user, record_id=id)
    file_path = get_pdf_path(relative_path=record.pdf_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    return FileResponse(
        path=str(file_path),
        filename=record.pdf_original_name,
        media_type=record.pdf_mime_type,
    )


# =============================================================================
# Purchase Record Screenshots
# =============================================================================

@router.get("/screenshots/{id}")
def download_screenshot_file(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    from app.modules.finance.purchase_records import service as purchase_service
    from app.modules.finance.purchase_records.storage import get_screenshot_path

    record = purchase_service.get_screenshot(session, current_user=current_user, record_id=id)
    file_path = get_screenshot_path(relative_path=record.screenshot_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Screenshot file not found")
    return FileResponse(
        path=str(file_path),
        filename=record.screenshot_original_name,
        media_type=record.screenshot_mime_type,
    )


# =============================================================================
# Reimbursement Export Excel Files
# =============================================================================

@router.get("/exports/{export_id}")
def download_export_file(
    session: SessionDep,
    current_user: CurrentUser,
    export_id: uuid.UUID,
) -> FileResponse:
    from app.modules.finance.reimbursement_exports import service as export_service

    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Admin access required.",
        )
    file_path, file_name = export_service.download_export(session, export_id=export_id)
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

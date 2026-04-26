"""
Reimbursement Exports Router

Interface layer for the reimbursement_exports tool module.
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.models_core import Message

from .schemas import (
    GenerateRequest,
    RecordsFilter,
    ReimbursementExportDetailPublic,
    ReimbursementExportsPublic,
    ReimbursementExportPublic,
    SettingsResponse,
    SettingsUpdate,
)
from . import service

router = APIRouter(prefix="/finance/reimbursement-exports", tags=["reimbursement_exports"])


# =============================================================================
# GET /records
# =============================================================================

@router.get("/records")
def read_records(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: str | None = None,
    end_date: str | None = None,
    category: str | None = None,
    subcategory: str | None = None,
    currency: str | None = None,
    owner_id: uuid.UUID | None = None,
    exported: str | None = Query(None, pattern="^(all|exported|not_exported)$"),
    q: str | None = None,
) -> Any:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    from datetime import date

    filters = RecordsFilter()
    if start_date:
        try:
            filters.start_date = date.fromisoformat(start_date)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid start_date format.",
            ) from exc
    if end_date:
        try:
            filters.end_date = date.fromisoformat(end_date)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid end_date format.",
            ) from exc
    filters.category = category
    filters.subcategory = subcategory
    filters.currency = currency
    filters.owner_id = owner_id
    filters.exported = exported
    filters.q = q
    return service.read_records(session, skip=skip, limit=limit, filters=filters)


# =============================================================================
# POST /generate
# =============================================================================

@router.post("/generate", response_model=ReimbursementExportPublic)
def generate_export(
    session: SessionDep,
    current_user: CurrentUser,
    data_in: GenerateRequest,
) -> ReimbursementExportPublic:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return service.generate_export(
        session=session,
        data_in=data_in,
        generated_by_id=current_user.id,
    )


# =============================================================================
# GET /history
# =============================================================================

@router.get("/history", response_model=ReimbursementExportsPublic)
def read_history(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    created_at_from: datetime | None = None,
    created_at_to: datetime | None = None,
    created_by_id: uuid.UUID | None = None,
    currency: str | None = None,
) -> ReimbursementExportsPublic:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return service.read_history(
        session,
        skip=skip,
        limit=limit,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        created_by_id=created_by_id,
        currency=currency,
    )


# =============================================================================
# GET /settings
# =============================================================================

@router.get("/settings", response_model=SettingsResponse)
def read_settings(
    session: SessionDep,
    current_user: CurrentUser,
) -> SettingsResponse:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return service.read_settings(session)


# =============================================================================
# PUT /settings
# =============================================================================

@router.put("/settings", response_model=SettingsResponse)
def update_settings(
    session: SessionDep,
    current_user: CurrentUser,
    data_in: SettingsUpdate,
) -> SettingsResponse:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return service.update_settings(session, data_in=data_in, updated_by_id=current_user.id)


# =============================================================================
# GET /{id}
# =============================================================================

@router.get("/{export_id}", response_model=ReimbursementExportDetailPublic)
def read_export(
    session: SessionDep,
    current_user: CurrentUser,
    export_id: uuid.UUID,
) -> ReimbursementExportDetailPublic:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return service.read_export(session, export_id=export_id)


# =============================================================================
# GET /{id}/download
# =============================================================================

@router.get("/{export_id}/download")
def download_export(
    session: SessionDep,
    current_user: CurrentUser,
    export_id: uuid.UUID,
) -> FileResponse:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    file_path, file_name = service.download_export(session, export_id=export_id)
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# =============================================================================
# POST /purge-expired-files
# =============================================================================

@router.post("/purge-expired-files")
def purge_expired_files(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return service.purge_expired_files(session)

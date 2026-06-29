"""
Equipment Purchase Contract Filler Router

API endpoints for the equipment_purchase_filler tool module.
"""

import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import Session

from app.api.deps import CurrentUser, SessionDep
from app.models_core import Message

from .models import (
    EquipmentPurchaseFilledVersionCreate,
    EquipmentPurchaseFilledVersionPublic,
    EquipmentPurchaseFilledVersionUpdate,
    EquipmentPurchaseFilledVersionsPublic,
)
from .schemas import (
    ContractFieldsPublic,
    ContractPreviewPublic,
    ExportRequest,
    ExportResponse,
    FilledValuesPayload,
)
from . import service

router = APIRouter(prefix="/contracts/equipment-purchase-filler", tags=["equipment-purchase-filler"])


@router.get("/fields", response_model=ContractFieldsPublic)
def read_fields() -> Any:
    """Return the list of fillable fields for the built-in contract template."""
    return service.list_fields()


@router.get("/preview", response_model=ContractPreviewPublic)
def read_preview() -> Any:
    """Return a text preview of the built-in contract template."""
    return service.get_preview()


@router.post("/versions", response_model=EquipmentPurchaseFilledVersionPublic)
def create_version(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_in: EquipmentPurchaseFilledVersionCreate,
) -> Any:
    """Save a filled version of the contract."""
    return service.create_version(
        session,
        current_user=current_user,
        version_in=version_in,
    )


@router.get("/versions", response_model=EquipmentPurchaseFilledVersionsPublic)
def read_versions(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List saved filled versions for the current user."""
    return service.read_versions(
        session,
        current_user=current_user,
        skip=skip,
        limit=limit,
    )


@router.get("/versions/{version_id}", response_model=EquipmentPurchaseFilledVersionPublic)
def read_version(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
) -> Any:
    """Get a single filled version."""
    return service.read_version(session, current_user=current_user, version_id=version_id)


@router.patch("/versions/{version_id}", response_model=EquipmentPurchaseFilledVersionPublic)
def update_version(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
    version_in: EquipmentPurchaseFilledVersionUpdate,
) -> Any:
    """Update a filled version (name, description, or field values)."""
    return service.update_version(
        session,
        current_user=current_user,
        version_id=version_id,
        version_in=version_in,
    )


@router.delete("/versions/{version_id}")
def delete_version(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
) -> Message:
    """Delete a filled version."""
    service.delete_version(session, current_user=current_user, version_id=version_id)
    return Message(message="Version deleted successfully")


@router.post("/versions/{version_id}/export", response_model=ExportResponse)
def export_version(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
    export_in: ExportRequest,
) -> ExportResponse:
    """Generate/export a filled DOCX for the version."""
    file_path, output_filename = service.export_version(
        session,
        current_user=current_user,
        version_id=version_id,
        filename=export_in.filename,
    )
    return ExportResponse(
        download_url=f"/api/v1/files/equipment-purchase-filler/{version_id}",
        filename=output_filename,
    )


@router.post("/versions/{version_id}/fill-and-export", response_model=ExportResponse)
def fill_and_export(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
    payload: FilledValuesPayload,
    export_in: ExportRequest,
) -> ExportResponse:
    """Update field values and immediately export."""
    service.update_version(
        session,
        current_user=current_user,
        version_id=version_id,
        version_in=EquipmentPurchaseFilledVersionUpdate(
            field_values=payload.field_values,
            equipment_items=payload.equipment_items,
        ),
    )
    file_path, output_filename = service.export_version(
        session=session,
        current_user=current_user,
        version_id=version_id,
        filename=export_in.filename,
    )
    return ExportResponse(
        download_url=f"/api/v1/files/equipment-purchase-filler/{version_id}",
        filename=output_filename,
    )

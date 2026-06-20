"""
Equipment Purchase Contract Filler Service

Business logic for the equipment_purchase_filler tool module.
"""

import uuid
from pathlib import Path

from fastapi import HTTPException
from sqlmodel import Session

from app.models_core import User

from .docx_filler import (
    CONTRACT_FIELDS,
    deserialize_equipment_items,
    deserialize_field_values,
    extract_preview,
    generate_filled_docx,
    serialize_equipment_items,
    serialize_field_values,
)
from .models import (
    EquipmentPurchaseFilledVersion,
    EquipmentPurchaseFilledVersionCreate,
    EquipmentPurchaseFilledVersionUpdate,
)
from .schemas import ContractFieldsPublic, ContractPreviewPublic
from . import repository
from .storage import delete_filled_docx, get_filled_path, get_template_path, save_filled_docx


def _require_owner(*, version: EquipmentPurchaseFilledVersion | None, current_user: User) -> EquipmentPurchaseFilledVersion:
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    if version.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return version


def list_fields() -> ContractFieldsPublic:
    return ContractFieldsPublic(data=CONTRACT_FIELDS)


def get_preview() -> ContractPreviewPublic:
    template_path = get_template_path()
    segments = extract_preview(template_path)
    return ContractPreviewPublic(data=segments)


def read_versions(
    session: Session,
    *,
    current_user: User,
    skip: int = 0,
    limit: int = 100,
) -> list[EquipmentPurchaseFilledVersion]:
    return repository.list_versions(
        session,
        created_by_id=current_user.id,
        skip=skip,
        limit=limit,
    )


def read_version(
    session: Session,
    *,
    current_user: User,
    version_id: uuid.UUID,
) -> EquipmentPurchaseFilledVersion:
    version = repository.get_version(session, version_id=version_id)
    return _require_owner(version=version, current_user=current_user)


def create_version(
    session: Session,
    *,
    current_user: User,
    version_in: EquipmentPurchaseFilledVersionCreate,
) -> EquipmentPurchaseFilledVersion:
    field_values_raw = serialize_field_values(version_in.field_values)
    equipment_items_raw = serialize_equipment_items(version_in.equipment_items)
    return repository.create_version(
        session,
        version_in=version_in,
        created_by_id=current_user.id,
        field_values_raw=field_values_raw,
        equipment_items_raw=equipment_items_raw,
    )


def update_version(
    session: Session,
    *,
    current_user: User,
    version_id: uuid.UUID,
    version_in: EquipmentPurchaseFilledVersionUpdate,
) -> EquipmentPurchaseFilledVersion:
    version = read_version(session, current_user=current_user, version_id=version_id)
    field_values_raw: str | None = None
    equipment_items_raw: str | None = None
    if version_in.field_values is not None:
        field_values_raw = serialize_field_values(version_in.field_values)
    if version_in.equipment_items is not None:
        equipment_items_raw = serialize_equipment_items(version_in.equipment_items)
    return repository.update_version(
        session,
        version=version,
        version_in=version_in,
        field_values_raw=field_values_raw,
        equipment_items_raw=equipment_items_raw,
    )


def delete_version(
    session: Session,
    *,
    current_user: User,
    version_id: uuid.UUID,
) -> None:
    version = read_version(session, current_user=current_user, version_id=version_id)
    if version.output_file_path:
        delete_filled_docx(relative_path=version.output_file_path)
    repository.delete_version(session, version=version)


def export_version(
    session: Session,
    *,
    current_user: User,
    version_id: uuid.UUID,
    filename: str | None = None,
) -> Path:
    version = read_version(session, current_user=current_user, version_id=version_id)
    field_values = deserialize_field_values(version.field_values)
    equipment_items = deserialize_equipment_items(version.equipment_items)

    template_path = get_template_path()
    filled_path = generate_filled_docx(
        template_path=template_path,
        field_values=field_values,
        equipment_items=equipment_items or [],
    )

    output_filename = filename or version.version_name
    if not output_filename.endswith(".docx"):
        output_filename = f"{output_filename}.docx"

    relative_path, file_size = save_filled_docx(
        source_path=filled_path,
        version_id=version.id,
        filename=output_filename,
    )

    # Update version record with output file info
    version.output_filename = output_filename
    version.output_file_path = relative_path
    version.output_file_size = file_size
    session.add(version)
    session.commit()
    session.refresh(version)

    return get_filled_path(relative_path=relative_path)

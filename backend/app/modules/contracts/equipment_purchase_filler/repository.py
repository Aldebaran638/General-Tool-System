"""
Equipment Purchase Contract Filler Repository

Database queries for EquipmentPurchaseFilledVersion records.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from .models import EquipmentPurchaseFilledVersion


def count_versions(
    session: Session,
    *,
    created_by_id: uuid.UUID,
) -> int:
    statement = (
        select(func.count())
        .select_from(EquipmentPurchaseFilledVersion)
        .where(EquipmentPurchaseFilledVersion.created_by_id == created_by_id)
    )
    return session.exec(statement).one()  # type: ignore


def list_versions(
    session: Session,
    *,
    created_by_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> list[EquipmentPurchaseFilledVersion]:
    statement = (
        select(EquipmentPurchaseFilledVersion)
        .where(EquipmentPurchaseFilledVersion.created_by_id == created_by_id)
        .order_by(EquipmentPurchaseFilledVersion.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


def get_version(session: Session, *, version_id: uuid.UUID) -> EquipmentPurchaseFilledVersion | None:
    return session.get(EquipmentPurchaseFilledVersion, version_id)


def create_version(
    session: Session,
    *,
    version_in: EquipmentPurchaseFilledVersion,
    created_by_id: uuid.UUID,
    field_values_raw: str,
    equipment_items_raw: str | None,
) -> EquipmentPurchaseFilledVersion:
    version = EquipmentPurchaseFilledVersion.model_validate(
        version_in,
        update={
            "created_by_id": created_by_id,
            "field_values": field_values_raw,
            "equipment_items": equipment_items_raw,
        },
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    return version


def update_version(
    session: Session,
    *,
    version: EquipmentPurchaseFilledVersion,
    version_in: EquipmentPurchaseFilledVersion,
    field_values_raw: str | None = None,
    equipment_items_raw: str | None = None,
) -> EquipmentPurchaseFilledVersion:
    update_data = version_in.model_dump(exclude_unset=True)
    if field_values_raw is not None:
        update_data["field_values"] = field_values_raw
    if equipment_items_raw is not None:
        update_data["equipment_items"] = equipment_items_raw
    version.sqlmodel_update(update_data)
    version.updated_at = datetime.now(timezone.utc)
    session.add(version)
    session.commit()
    session.refresh(version)
    return version


def delete_version(session: Session, *, version: EquipmentPurchaseFilledVersion) -> None:
    session.delete(version)
    session.commit()

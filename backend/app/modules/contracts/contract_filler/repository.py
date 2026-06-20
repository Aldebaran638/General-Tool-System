"""
Contract Filler Repository

Database queries for FilledVersion records.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from .models import FilledVersion


def count_versions(
    session: Session,
    *,
    created_by_id: uuid.UUID,
) -> int:
    statement = (
        select(func.count())
        .select_from(FilledVersion)
        .where(FilledVersion.created_by_id == created_by_id)
    )
    return session.exec(statement).one()  # type: ignore


def list_versions(
    session: Session,
    *,
    created_by_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> list[FilledVersion]:
    statement = (
        select(FilledVersion)
        .where(FilledVersion.created_by_id == created_by_id)
        .order_by(FilledVersion.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


def get_version(session: Session, *, version_id: uuid.UUID) -> FilledVersion | None:
    return session.get(FilledVersion, version_id)


def create_version(
    session: Session,
    *,
    version_in: FilledVersion,
    created_by_id: uuid.UUID,
    field_values_raw: str,
) -> FilledVersion:
    version = FilledVersion.model_validate(
        version_in,
        update={
            "created_by_id": created_by_id,
            "field_values": field_values_raw,
        },
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    return version


def update_version(
    session: Session,
    *,
    version: FilledVersion,
    version_in: FilledVersion,
    field_values_raw: str | None = None,
) -> FilledVersion:
    update_data = version_in.model_dump(exclude_unset=True)
    if field_values_raw is not None:
        update_data["field_values"] = field_values_raw
    version.sqlmodel_update(update_data)
    version.updated_at = datetime.now(timezone.utc)
    session.add(version)
    session.commit()
    session.refresh(version)
    return version


def delete_version(session: Session, *, version: FilledVersion) -> None:
    session.delete(version)
    session.commit()

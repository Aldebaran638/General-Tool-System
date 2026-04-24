"""
Purchase Records Repository

Persistence layer for purchase_record data access.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, func, select

from .models import PurchaseRecord
from .schemas import PurchaseRecordCreate, PurchaseRecordUpdate


def count_records(
    session: Session,
    *,
    owner_id: uuid.UUID | None = None,
    deleted: bool = False,
    deleted_by_id: uuid.UUID | None = None,
) -> int:
    statement = select(func.count()).select_from(PurchaseRecord)
    if deleted:
        statement = statement.where(PurchaseRecord.deleted_at.isnot(None))
        if deleted_by_id is not None:
            statement = statement.where(PurchaseRecord.deleted_by_id == deleted_by_id)
    else:
        statement = statement.where(PurchaseRecord.deleted_at.is_(None))
        if owner_id is not None:
            statement = statement.where(PurchaseRecord.owner_id == owner_id)
    return session.exec(statement).one()


def list_records(
    session: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    owner_id: uuid.UUID | None = None,
    deleted: bool = False,
    deleted_by_id: uuid.UUID | None = None,
) -> list[PurchaseRecord]:
    statement = select(PurchaseRecord)
    if deleted:
        statement = statement.where(PurchaseRecord.deleted_at.isnot(None))
        if deleted_by_id is not None:
            statement = statement.where(PurchaseRecord.deleted_by_id == deleted_by_id)
    else:
        statement = statement.where(PurchaseRecord.deleted_at.is_(None))
        if owner_id is not None:
            statement = statement.where(PurchaseRecord.owner_id == owner_id)
    statement = statement.order_by(PurchaseRecord.created_at.desc()).offset(skip).limit(limit)
    return session.exec(statement).all()


def get_record(session: Session, *, record_id: uuid.UUID) -> PurchaseRecord | None:
    return session.get(PurchaseRecord, record_id)


def create_record(
    session: Session,
    *,
    record_in: PurchaseRecordCreate,
    owner_id: uuid.UUID,
    screenshot_path: str,
    screenshot_original_name: str,
    screenshot_mime_type: str,
    screenshot_size: int,
) -> PurchaseRecord:
    record = PurchaseRecord.model_validate(
        record_in,
        update={
            "owner_id": owner_id,
            "screenshot_path": screenshot_path,
            "screenshot_original_name": screenshot_original_name,
            "screenshot_mime_type": screenshot_mime_type,
            "screenshot_size": screenshot_size,
        },
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def update_record(
    session: Session,
    *,
    record: PurchaseRecord,
    record_in: PurchaseRecordUpdate,
) -> PurchaseRecord:
    update_dict = record_in.model_dump(exclude_unset=True)
    record.sqlmodel_update(update_dict)
    record.updated_at = datetime.now(timezone.utc)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def update_record_status(
    session: Session,
    *,
    record: PurchaseRecord,
    status: str,
) -> PurchaseRecord:
    record.status = status
    record.updated_at = datetime.now(timezone.utc)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def soft_delete_record(
    session: Session,
    *,
    record: PurchaseRecord,
    deleted_by_id: uuid.UUID,
) -> PurchaseRecord:
    record.deleted_at = datetime.now(timezone.utc)
    record.deleted_by_id = deleted_by_id
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def restore_record(session: Session, *, record: PurchaseRecord) -> PurchaseRecord:
    record.deleted_at = None
    record.deleted_by_id = None
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def purge_old_deleted_records(session: Session, *, days: int = 30) -> list[PurchaseRecord]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    statement = select(PurchaseRecord).where(
        PurchaseRecord.deleted_at.isnot(None),
        PurchaseRecord.deleted_at < cutoff,
    )
    records = session.exec(statement).all()
    for record in records:
        session.delete(record)
    session.commit()
    return list(records)

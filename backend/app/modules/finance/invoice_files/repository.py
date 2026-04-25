"""
Invoice Files Repository

Persistence layer for invoice_file data access.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, func, select

from .models import InvoiceFile
from .schemas import InvoiceFileCreate, InvoiceFileUpdate


def count_records(
    session: Session,
    *,
    owner_id: uuid.UUID | None = None,
    deleted: bool = False,
    deleted_by_id: uuid.UUID | None = None,
    status: str | None = None,
) -> int:
    statement = select(func.count()).select_from(InvoiceFile)
    if deleted:
        statement = statement.where(InvoiceFile.deleted_at.isnot(None))
        if deleted_by_id is not None:
            statement = statement.where(InvoiceFile.deleted_by_id == deleted_by_id)
    else:
        statement = statement.where(InvoiceFile.deleted_at.is_(None))
        if owner_id is not None:
            statement = statement.where(InvoiceFile.owner_id == owner_id)
    if status is not None:
        statement = statement.where(InvoiceFile.status == status)
    return session.exec(statement).one()


def list_records(
    session: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    owner_id: uuid.UUID | None = None,
    deleted: bool = False,
    deleted_by_id: uuid.UUID | None = None,
    status: str | None = None,
) -> list[InvoiceFile]:
    statement = select(InvoiceFile)
    if deleted:
        statement = statement.where(InvoiceFile.deleted_at.isnot(None))
        if deleted_by_id is not None:
            statement = statement.where(InvoiceFile.deleted_by_id == deleted_by_id)
    else:
        statement = statement.where(InvoiceFile.deleted_at.is_(None))
        if owner_id is not None:
            statement = statement.where(InvoiceFile.owner_id == owner_id)
    if status is not None:
        statement = statement.where(InvoiceFile.status == status)
    statement = statement.order_by(InvoiceFile.created_at.desc()).offset(skip).limit(limit)
    return session.exec(statement).all()


def get_record(session: Session, *, record_id: uuid.UUID) -> InvoiceFile | None:
    return session.get(InvoiceFile, record_id)


def get_record_by_invoice_number(
    session: Session,
    *,
    owner_id: uuid.UUID,
    invoice_number: str,
    exclude_id: uuid.UUID | None = None,
) -> InvoiceFile | None:
    statement = select(InvoiceFile).where(
        InvoiceFile.owner_id == owner_id,
        InvoiceFile.invoice_number == invoice_number,
        InvoiceFile.deleted_at.is_(None),
    )
    if exclude_id is not None:
        statement = statement.where(InvoiceFile.id != exclude_id)
    return session.exec(statement).first()


def count_duplicates(
    session: Session,
    *,
    invoice_number: str,
    exclude_owner_id: uuid.UUID | None = None,
) -> int:
    """Count how many other (non-deleted) records share this invoice number across users."""
    statement = select(func.count()).select_from(InvoiceFile).where(
        InvoiceFile.invoice_number == invoice_number,
        InvoiceFile.deleted_at.is_(None),
    )
    if exclude_owner_id is not None:
        statement = statement.where(InvoiceFile.owner_id != exclude_owner_id)
    return session.exec(statement).one()


def create_record(
    session: Session,
    *,
    record_in: InvoiceFileCreate,
    owner_id: uuid.UUID,
    pdf_path: str,
    pdf_original_name: str,
    pdf_mime_type: str,
    pdf_size: int,
) -> InvoiceFile:
    record = InvoiceFile.model_validate(
        record_in,
        update={
            "owner_id": owner_id,
            "pdf_path": pdf_path,
            "pdf_original_name": pdf_original_name,
            "pdf_mime_type": pdf_mime_type,
            "pdf_size": pdf_size,
        },
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def update_record(
    session: Session,
    *,
    record: InvoiceFile,
    record_in: InvoiceFileUpdate,
) -> InvoiceFile:
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
    record: InvoiceFile,
    status: str,
) -> InvoiceFile:
    record.status = status
    record.updated_at = datetime.now(timezone.utc)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def soft_delete_record(
    session: Session,
    *,
    record: InvoiceFile,
    deleted_by_id: uuid.UUID,
) -> InvoiceFile:
    record.deleted_at = datetime.now(timezone.utc)
    record.deleted_by_id = deleted_by_id
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def restore_record(session: Session, *, record: InvoiceFile) -> InvoiceFile:
    record.deleted_at = None
    record.deleted_by_id = None
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def purge_old_deleted_records(session: Session, *, days: int = 30) -> tuple[list[InvoiceFile], list[str]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    statement = select(InvoiceFile).where(
        InvoiceFile.deleted_at.isnot(None),
        InvoiceFile.deleted_at < cutoff,
    )
    records = session.exec(statement).all()
    # Collect pdf_paths BEFORE commit to avoid detached state issues
    pdf_paths = [r.pdf_path for r in records]
    for record in records:
        session.delete(record)
    session.commit()
    return list(records), pdf_paths

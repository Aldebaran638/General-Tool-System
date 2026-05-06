"""
Reimbursement Exports Repository

Persistence layer for reimbursement export records.
"""

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlmodel import Session, select

from app.models_core import AppSetting

from .constants import DEFAULT_RETENTION_DAYS, STATUS_GENERATED, STATUS_PURGED
from .models import ReimbursementExport, ReimbursementExportItem
from .schemas import RecordsFilter


# =============================================================================
# Export History
# =============================================================================

def count_exports(
    session: Session,
    *,
    created_at_from: datetime | None = None,
    created_at_to: datetime | None = None,
    created_by_id: uuid.UUID | None = None,
    currency: str | None = None,
) -> int:
    statement = select(func.count()).select_from(ReimbursementExport)
    statement = _apply_history_filters(
        statement,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        created_by_id=created_by_id,
        currency=currency,
    )
    return session.exec(statement).one()  # type: ignore


def list_exports(
    session: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    created_at_from: datetime | None = None,
    created_at_to: datetime | None = None,
    created_by_id: uuid.UUID | None = None,
    currency: str | None = None,
) -> list[ReimbursementExport]:
    statement = select(ReimbursementExport)
    statement = _apply_history_filters(
        statement,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        created_by_id=created_by_id,
        currency=currency,
    )
    statement = (
        statement
        .order_by(ReimbursementExport.created_at.desc())  # type: ignore
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def _apply_history_filters(
    statement,
    *,
    created_at_from: datetime | None,
    created_at_to: datetime | None,
    created_by_id: uuid.UUID | None,
    currency: str | None,
):
    if created_at_from is not None:
        statement = statement.where(ReimbursementExport.created_at >= created_at_from)  # type: ignore
    if created_at_to is not None:
        statement = statement.where(ReimbursementExport.created_at <= created_at_to)  # type: ignore
    if created_by_id is not None:
        statement = statement.where(ReimbursementExport.created_by_id == created_by_id)  # type: ignore
    if currency is not None:
        statement = statement.where(ReimbursementExport.currency == currency)  # type: ignore
    return statement


def get_export(session: Session, *, export_id: uuid.UUID) -> ReimbursementExport | None:
    return session.get(ReimbursementExport, export_id)


def create_export(
    session: Session,
    *,
    created_by_id: uuid.UUID,
    department: str | None,
    business_unit: str | None,
    reimburser: str | None,
    reimbursement_date: date | None,
    currency: str,
    total_amount: Any,
    item_count: int,
    original_filename: str,
    stored_filename: str,
    file_path: str,
    mime_type: str,
    file_size: int,
    file_expires_at: datetime,
) -> ReimbursementExport:
    export = ReimbursementExport(
        created_by_id=created_by_id,
        department=department,
        business_unit=business_unit,
        reimburser=reimburser,
        reimbursement_date=reimbursement_date,
        currency=currency,
        total_amount=total_amount,
        item_count=item_count,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=file_path,
        mime_type=mime_type,
        file_size=file_size,
        file_expires_at=file_expires_at,
    )
    session.add(export)
    session.commit()
    session.refresh(export)
    return export


def create_export_items(
    session: Session,
    *,
    export_id: uuid.UUID,
    records: list[dict],
) -> list[ReimbursementExportItem]:
    items = []
    for rec in records:
        item = ReimbursementExportItem(
            export_id=export_id,
            purchase_record_id=rec["purchase_record_id"],
            invoice_file_id=rec.get("invoice_file_id"),
            invoice_match_id=rec.get("invoice_match_id"),
            document_number=rec["document_number"],
            purchase_date=rec["purchase_date"],
            amount=rec["amount"],
            currency=rec["currency"],
            category=rec["category"],
            subcategory=rec.get("subcategory"),
            order_name=rec["order_name"],
            remark=rec.get("remark"),
            description_snapshot=rec.get("description_snapshot"),
            department_snapshot=rec.get("department_snapshot"),
        )
        session.add(item)
        items.append(item)
    session.commit()
    for item in items:
        session.refresh(item)
    return items


def get_export_items(
    session: Session,
    *,
    export_id: uuid.UUID,
) -> list[ReimbursementExportItem]:
    statement = (
        select(ReimbursementExportItem)
        .where(ReimbursementExportItem.export_id == export_id)
        .order_by(ReimbursementExportItem.document_number)  # type: ignore
    )
    return list(session.exec(statement).all())


def list_expired_exports(session: Session) -> list[ReimbursementExport]:
    now = datetime.now(timezone.utc)
    statement = select(ReimbursementExport).where(
        ReimbursementExport.file_expires_at < now,
        ReimbursementExport.file_deleted_at.is_(None),  # type: ignore
    )
    return list(session.exec(statement).all())


def mark_file_deleted(session: Session, *, export: ReimbursementExport) -> ReimbursementExport:
    export.file_deleted_at = datetime.now(timezone.utc)
    session.add(export)
    session.commit()
    session.refresh(export)
    return export


# =============================================================================
# Purchase Record Query (read-only, from sibling module)
# =============================================================================

from app.modules.finance.purchase_records.models import PurchaseRecord  # noqa: E402
from app.modules.finance.invoice_matching.models import InvoiceMatch  # noqa: E402
from app.modules.finance.invoice_matching.constants import (
    MATCH_STATUS_APPROVED,
)
from app.modules.finance.invoice_files.models import InvoiceFile  # noqa: E402


def count_eligible_records(session: Session, filters: RecordsFilter) -> int:
    base_stmt = _build_eligible_base(filters)
    return session.exec(select(func.count()).select_from(base_stmt.subquery())).one()  # type: ignore


def list_eligible_records(
    session: Session,
    filters: RecordsFilter,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Any]:
    base_stmt = _build_eligible_base(filters)
    stmt = (
        base_stmt
        .order_by(PurchaseRecord.purchase_date.asc(), PurchaseRecord.created_at.asc(), PurchaseRecord.id.asc())  # type: ignore
        .offset(skip)
        .limit(limit)
    )
    rows = list(session.exec(stmt).all())
    return [_row_to_dict(r) for r in rows]


def get_eligible_record_by_id(session: Session, record_id: uuid.UUID) -> dict | None:
    stmt = _build_eligible_base(RecordsFilter()).where(PurchaseRecord.id == record_id)  # type: ignore
    row = session.exec(stmt).first()
    if row is None:
        return None
    return _row_to_dict(row)


def get_eligible_records_by_ids(
    session: Session,
    record_ids: list[uuid.UUID],
) -> list[dict]:
    if not record_ids:
        return []
    stmt = (
        _build_eligible_base(RecordsFilter())
        .where(PurchaseRecord.id.in_(record_ids))  # type: ignore
    )
    rows = session.exec(stmt).all()
    return [_row_to_dict(r) for r in rows]


def _build_eligible_base(filters: RecordsFilter):
    """Build query joining PurchaseRecord -> InvoiceMatch -> InvoiceFile."""
    stmt = (
        select(PurchaseRecord, InvoiceMatch, InvoiceFile)
        .join(InvoiceMatch, PurchaseRecord.id == InvoiceMatch.purchase_record_id)
        .join(InvoiceFile, InvoiceMatch.invoice_file_id == InvoiceFile.id)
        .where(
            PurchaseRecord.deleted_at.is_(None),  # type: ignore
            InvoiceMatch.status == MATCH_STATUS_APPROVED,
            InvoiceFile.deleted_at.is_(None),  # type: ignore
            InvoiceFile.status != "voided",
        )
    )

    if filters.start_date:
        stmt = stmt.where(PurchaseRecord.purchase_date >= filters.start_date)  # type: ignore
    if filters.end_date:
        stmt = stmt.where(PurchaseRecord.purchase_date <= filters.end_date)  # type: ignore
    if filters.category:
        stmt = stmt.where(PurchaseRecord.category == filters.category)  # type: ignore
    if filters.subcategory:
        stmt = stmt.where(PurchaseRecord.subcategory == filters.subcategory)  # type: ignore
    if filters.currency:
        stmt = stmt.where(PurchaseRecord.currency == filters.currency)  # type: ignore
    if filters.owner_id:
        stmt = stmt.where(PurchaseRecord.owner_id == filters.owner_id)  # type: ignore
    if filters.q:
        q = f"%{filters.q}%"
        stmt = stmt.where(
            (PurchaseRecord.order_name.ilike(q)) | (PurchaseRecord.note.ilike(q))  # type: ignore
        )
    if filters.exported in ("exported", "not_exported"):
        # Push the exported filter into SQL so count and data stay aligned.
        # A purchase record is "exported" iff a ReimbursementExportItem references it.
        exported_subq = (
            select(ReimbursementExportItem.id)
            .where(ReimbursementExportItem.purchase_record_id == PurchaseRecord.id)  # type: ignore
        )
        if filters.exported == "exported":
            stmt = stmt.where(exported_subq.exists())
        else:
            stmt = stmt.where(~exported_subq.exists())

    return stmt


def _row_to_dict(row: Any) -> dict:
    """Convert (PurchaseRecord, InvoiceMatch, InvoiceFile) row to flat dict."""
    pr, im, inv = row
    return {
        "id": pr.id,
        "owner_id": pr.owner_id,
        "purchase_date": pr.purchase_date,
        "amount": pr.amount,
        "currency": pr.currency,
        "order_name": pr.order_name,
        "category": pr.category,
        "subcategory": pr.subcategory,
        "note": pr.note,
        "status": pr.status,
        "created_at": pr.created_at,
        "screenshot_path": pr.screenshot_path,
        "invoice_match_id": im.id,
        "invoice_file_id": inv.id,
        "invoice_number": inv.invoice_number,
        "invoice_date": inv.invoice_date,
        "invoice_amount": inv.invoice_amount,
        "seller": inv.seller,
    }


# =============================================================================
# Exported metadata helpers
# =============================================================================

def get_export_metadata_for_records(
    session: Session,
    record_ids: list[uuid.UUID],
) -> dict[uuid.UUID, dict]:
    """Return {purchase_record_id: {latest_exported_at, latest_exported_by}}."""
    if not record_ids:
        return {}
    # Find the latest export.created_at for each purchase_record_id, then join back
    # to get the corresponding created_by_id. PostgreSQL does not support max(uuid).
    subq = (
        select(
            ReimbursementExportItem.purchase_record_id,
            func.max(ReimbursementExport.created_at).label("latest_at"),  # type: ignore
        )
        .join(ReimbursementExport, ReimbursementExportItem.export_id == ReimbursementExport.id)
        .where(ReimbursementExportItem.purchase_record_id.in_(record_ids))  # type: ignore
        .group_by(ReimbursementExportItem.purchase_record_id)
        .subquery()
    )
    stmt = (
        select(
            subq.c.purchase_record_id,
            subq.c.latest_at,
            ReimbursementExport.created_by_id.label("latest_by"),
        )
        .join(ReimbursementExport, ReimbursementExport.created_at == subq.c.latest_at)
    )
    result: dict[uuid.UUID, dict] = {}
    for row in session.exec(stmt).all():
        result[row.purchase_record_id] = {
            "latest_exported_at": row.latest_at,
            "latest_exported_by": row.latest_by,
        }
    return result


# =============================================================================
# Settings
# =============================================================================

def get_setting(session: Session, key: str) -> AppSetting | None:
    return session.get(AppSetting, key)


def get_setting_int(session: Session, key: str, default: int) -> int:
    row = get_setting(session, key)
    if row is None:
        return default
    try:
        return int(row.value)
    except Exception:
        return default


def set_setting(session: Session, key: str, value: str, *, updated_by_id: uuid.UUID | None = None) -> AppSetting:
    row = get_setting(session, key)
    now = datetime.now(timezone.utc)
    if row is None:
        row = AppSetting(
            key=key,
            value=value,
            value_type="int",
            description="Reimbursement export file retention days",
            updated_by_id=updated_by_id,
            updated_at=now,
        )
        session.add(row)
    else:
        row.value = value
        row.updated_by_id = updated_by_id
        row.updated_at = now
        session.add(row)
    session.commit()
    session.refresh(row)
    return row

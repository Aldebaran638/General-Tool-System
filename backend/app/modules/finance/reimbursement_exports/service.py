"""
Reimbursement Exports Service

Application layer for reimbursement export business logic.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session

from .constants import (
    CATEGORY_ORDER,
    DEFAULT_RETENTION_DAYS,
    SETTING_RETENTION_DAYS,
    STATUS_PURGED,
)
from .excel_builder import build_excel
from .models import ReimbursementExport, ReimbursementExportItem
from .repository import (
    count_eligible_records,
    count_exports,
    create_export,
    create_export_items,
    get_eligible_records_by_ids,
    get_export,
    get_export_items,
    get_export_metadata_for_records,
    get_setting_int,
    list_exports,
    list_expired_exports,
    mark_file_deleted,
    set_setting,
)
from .schemas import (
    GenerateRequest,
    InvoiceFileBriefPublic,
    PurchaseRecordWithExportInfo,
    RecordsFilter,
    RecordsPublic,
    ReimbursementExportDetailPublic,
    ReimbursementExportItemPublic,
    ReimbursementExportPublic,
    ReimbursementExportsPublic,
    SettingsResponse,
    SettingsUpdate,
)
from .storage import delete_excel, save_excel


# =============================================================================
# Read Records
# =============================================================================

def read_records(
    session: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    filters: RecordsFilter,
) -> RecordsPublic:
    count = count_eligible_records(session, filters)
    records = get_eligible_records_by_ids_with_filter(session, filters, skip=skip, limit=limit)

    record_ids = [r["id"] for r in records]
    export_meta = get_export_metadata_for_records(session, record_ids)

    data: list[PurchaseRecordWithExportInfo] = []
    for r in records:
        meta = export_meta.get(r["id"], {})
        invoice_brief = None
        if r.get("invoice_file_id"):
            invoice_brief = InvoiceFileBriefPublic(
                id=r["invoice_file_id"],
                invoice_number=r.get("invoice_number", ""),
                invoice_date=r.get("invoice_date"),
                invoice_amount=r.get("invoice_amount", Decimal("0")),
                currency=r.get("currency", ""),
                seller=r.get("seller", ""),
            )

        exported = r["id"] in export_meta
        info = PurchaseRecordWithExportInfo(
            id=r["id"],
            owner_id=r["owner_id"],
            purchase_date=r["purchase_date"],
            amount=r["amount"],
            currency=r["currency"],
            order_name=r["order_name"],
            category=r["category"],
            subcategory=r.get("subcategory"),
            note=r.get("note"),
            status=r["status"],
            created_at=r.get("created_at"),
            invoice_file=invoice_brief,
            exported=exported,
            latest_exported_at=meta.get("latest_exported_at"),
            latest_exported_by=meta.get("latest_exported_by"),
        )
        data.append(info)

    return RecordsPublic(data=data, count=count)


def get_eligible_records_by_ids_with_filter(
    session: Session,
    filters: RecordsFilter,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    from .repository import list_eligible_records
    all_records = list_eligible_records(session, filters, skip=0, limit=10000)

    if filters.exported:
        record_ids = [r["id"] for r in all_records]
        meta = get_export_metadata_for_records(session, record_ids)
        if filters.exported == "exported":
            all_records = [r for r in all_records if r["id"] in meta]
        elif filters.exported == "not_exported":
            all_records = [r for r in all_records if r["id"] not in meta]

    count = len(all_records)
    paged = all_records[skip : skip + limit]
    return paged


# =============================================================================
# Generate Export
# =============================================================================

def generate_export(
    session: Session,
    *,
    data_in: GenerateRequest,
    generated_by_id: uuid.UUID,
) -> ReimbursementExportPublic:
    purchase_record_ids = data_in.purchase_record_ids
    if not purchase_record_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one purchase record must be selected.",
        )

    records = get_eligible_records_by_ids(session, purchase_record_ids)
    if not records:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No eligible records found for export.",
        )

    # Validate all requested IDs were found and eligible
    found_ids = {r["id"] for r in records}
    missing_ids = set(purchase_record_ids) - found_ids
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Selected records are not eligible for export: {missing_ids}",
        )

    # Validate single currency
    currencies = {r["currency"] for r in records}
    if len(currencies) > 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Multiple currencies selected: {currencies}. Only one currency per export is allowed.",
        )
    currency = list(currencies)[0]

    # Sort by category order, then purchase_date ASC, created_at ASC, id ASC
    def _sort_key(r: dict) -> tuple:
        cat_index = CATEGORY_ORDER.index(r["category"]) if r["category"] in CATEGORY_ORDER else 999
        created_at = r.get("created_at") or datetime.min
        return (cat_index, r["purchase_date"], created_at, r["id"])

    records.sort(key=_sort_key)

    # Assign document numbers
    total_amount = Decimal("0.00")
    for idx, rec in enumerate(records, start=1):
        rec["document_number"] = idx
        total_amount += rec["amount"]

    # Build category groups for Excel
    category_groups: dict[str, list[dict]] = {cat: [] for cat in CATEGORY_ORDER}
    for rec in records:
        cat = rec["category"]
        if cat in category_groups:
            category_groups[cat].append(rec)

    # Build Excel
    try:
        excel_bytes = build_excel(
            records=records,
            category_groups=category_groups,
            department=data_in.department or "",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build Excel file: {exc}",
        ) from exc

    # Save file
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    stored_filename = f"reimbursement_export_{timestamp}_{uuid.uuid4().hex[:8]}.xlsx"
    file_path, file_size = save_excel(data=excel_bytes, filename=stored_filename)

    retention_days = data_in.retention_days or DEFAULT_RETENTION_DAYS
    file_expires_at = datetime.now(timezone.utc) + timedelta(days=retention_days)

    # Persist export record
    export = create_export(
        session=session,
        created_by_id=generated_by_id,
        department=data_in.department,
        business_unit=data_in.business_unit,
        reimburser=data_in.reimburser,
        reimbursement_date=data_in.reimbursement_date,
        currency=currency,
        total_amount=total_amount,
        item_count=len(records),
        original_filename=stored_filename,
        stored_filename=stored_filename,
        file_path=file_path,
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        file_size=file_size,
        file_expires_at=file_expires_at,
    )

    # Build snapshot records
    snapshot_records = []
    for rec in records:
        snapshot_records.append({
            "purchase_record_id": rec["id"],
            "invoice_file_id": rec.get("invoice_file_id"),
            "invoice_match_id": rec.get("invoice_match_id"),
            "document_number": rec["document_number"],
            "purchase_date": rec["purchase_date"],
            "amount": rec["amount"],
            "currency": rec["currency"],
            "category": rec["category"],
            "subcategory": rec.get("subcategory"),
            "order_name": rec["order_name"],
            "remark": rec.get("note"),
            "description_snapshot": rec.get("note") or rec["order_name"],
            "department_snapshot": data_in.department,
        })

    create_export_items(session=session, export_id=export.id, records=snapshot_records)

    return ReimbursementExportPublic(
        id=export.id,
        created_by_id=export.created_by_id,
        created_at=export.created_at,
        department=export.department,
        business_unit=export.business_unit,
        reimburser=export.reimburser,
        reimbursement_date=export.reimbursement_date,
        currency=export.currency,
        total_amount=export.total_amount,
        item_count=export.item_count,
        original_filename=export.original_filename,
        stored_filename=export.stored_filename,
        file_path=export.file_path,
        mime_type=export.mime_type,
        file_size=export.file_size,
        file_expires_at=export.file_expires_at,
        file_deleted_at=export.file_deleted_at,
    )


# =============================================================================
# Export History
# =============================================================================

def read_history(
    session: Session,
    *,
    skip: int = 0,
    limit: int = 100,
) -> ReimbursementExportsPublic:
    count = count_exports(session)
    exports = list_exports(session, skip=skip, limit=limit)
    return ReimbursementExportsPublic(
        data=[_export_to_public(e) for e in exports],
        count=count,
    )


def read_export(session: Session, *, export_id: uuid.UUID) -> ReimbursementExportDetailPublic:
    export = get_export(session, export_id=export_id)
    if export is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found.",
        )
    items = get_export_items(session, export_id=export_id)
    return ReimbursementExportDetailPublic(
        id=export.id,
        created_by_id=export.created_by_id,
        created_at=export.created_at,
        department=export.department,
        business_unit=export.business_unit,
        reimburser=export.reimburser,
        reimbursement_date=export.reimbursement_date,
        currency=export.currency,
        total_amount=export.total_amount,
        item_count=export.item_count,
        original_filename=export.original_filename,
        stored_filename=export.stored_filename,
        file_path=export.file_path,
        mime_type=export.mime_type,
        file_size=export.file_size,
        file_expires_at=export.file_expires_at,
        file_deleted_at=export.file_deleted_at,
        items=[
            ReimbursementExportItemPublic(
                id=i.id,
                export_id=i.export_id,
                purchase_record_id=i.purchase_record_id,
                invoice_file_id=i.invoice_file_id,
                invoice_match_id=i.invoice_match_id,
                document_number=i.document_number,
                purchase_date=i.purchase_date,
                amount=i.amount,
                currency=i.currency,
                category=i.category,
                subcategory=i.subcategory,
                order_name=i.order_name,
                remark=i.remark,
                description_snapshot=i.description_snapshot,
                department_snapshot=i.department_snapshot,
                created_at=i.created_at,
            )
            for i in items
        ],
    )


def download_export(session: Session, *, export_id: uuid.UUID) -> tuple[str, str]:
    export = get_export(session, export_id=export_id)
    if export is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found.",
        )
    if export.file_deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="File expired. Please regenerate.",
        )
    if export.file_expires_at is not None and export.file_expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="File expired. Please regenerate.",
        )
    if not export.file_path:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="File expired. Please regenerate.",
        )
    from pathlib import Path
    if not Path(export.file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="File expired. Please regenerate.",
        )
    return export.file_path, export.original_filename or export.stored_filename or "export.xlsx"


# =============================================================================
# Purge Expired
# =============================================================================

def purge_expired_files(session: Session) -> dict[str, Any]:
    expired = list_expired_exports(session)
    purged_exports: list[ReimbursementExport] = []
    for export in expired:
        if export.file_path:
            delete_excel(file_path=export.file_path)
        mark_file_deleted(session, export=export)
        purged_exports.append(export)
    return {
        "purged_count": len(purged_exports),
        "purged_ids": [e.id for e in purged_exports],
    }


# =============================================================================
# Settings
# =============================================================================

def read_settings(session: Session) -> SettingsResponse:
    retention_days = get_setting_int(
        session, SETTING_RETENTION_DAYS, DEFAULT_RETENTION_DAYS
    )
    return SettingsResponse(retention_days=retention_days)


def update_settings(
    session: Session,
    *,
    data_in: SettingsUpdate,
    updated_by_id: uuid.UUID | None = None,
) -> SettingsResponse:
    if data_in.retention_days is not None:
        set_setting(
            session,
            SETTING_RETENTION_DAYS,
            str(data_in.retention_days),
            updated_by_id=updated_by_id,
        )
    return read_settings(session)


# =============================================================================
# Helpers
# =============================================================================

def _export_to_public(export: ReimbursementExport) -> ReimbursementExportPublic:
    return ReimbursementExportPublic(
        id=export.id,
        created_by_id=export.created_by_id,
        created_at=export.created_at,
        department=export.department,
        business_unit=export.business_unit,
        reimburser=export.reimburser,
        reimbursement_date=export.reimbursement_date,
        currency=export.currency,
        total_amount=export.total_amount,
        item_count=export.item_count,
        original_filename=export.original_filename,
        stored_filename=export.stored_filename,
        file_path=export.file_path,
        mime_type=export.mime_type,
        file_size=export.file_size,
        file_expires_at=export.file_expires_at,
        file_deleted_at=export.file_deleted_at,
    )

"""Invoice Matching Router."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from app.api.deps import CurrentUser, SessionDep
from .schemas import CandidateInvoice, InvoiceMatchPublic, InvoiceMatchesPublic, Message
from . import service

router = APIRouter(prefix="/finance/invoice-matching", tags=["invoice-matching"])


@router.get("/summary")
def read_summary(session: SessionDep, current_user: CurrentUser) -> dict:
    return service.read_summary(session=session, current_user=current_user)


@router.get("/unmatched-purchase-records")
def list_unmatched_purchase_records(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> dict:
    records = service.list_unmatched_purchase_records(
        session=session, current_user=current_user, skip=skip, limit=limit
    )
    data = [
        {
            "id": r.id,
            "owner_id": r.owner_id,
            "purchase_date": str(r.purchase_date) if r.purchase_date else None,
            "amount": str(r.amount) if r.amount else "0",
            "currency": r.currency or "",
            "order_name": r.order_name or "",
            "category": r.category or "",
            "subcategory": r.subcategory or "",
            "note": r.note or "",
            "status": r.status or "",
        }
        for r in records
    ]
    return {"count": len(data), "data": data}


@router.get("/available-invoices")
def list_available_invoices(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> dict:
    invoices = service.list_available_invoices(
        session=session, current_user=current_user, skip=skip, limit=limit
    )
    data = [
        {
            "id": inv.id,
            "owner_id": inv.owner_id,
            "invoice_number": inv.invoice_number or "",
            "invoice_date": str(inv.invoice_date) if inv.invoice_date else "",
            "invoice_amount": str(inv.invoice_amount) if inv.invoice_amount else "0",
            "currency": inv.currency or "",
            "seller": inv.seller or "",
            "status": inv.status or "",
        }
        for inv in invoices
    ]
    return {"count": len(data), "data": data}


@router.get("/available-invoices/search")
def search_available_invoices(
    session: SessionDep,
    current_user: CurrentUser,
    purchase_record_id: uuid.UUID,
    search: str | None = None,
) -> dict:
    try:
        invoices = service.search_available_invoices(
            session=session,
            current_user=current_user,
            purchase_record_id=purchase_record_id,
            search=search,
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    return {"count": len(invoices), "data": invoices}


@router.get("/candidates")
def list_candidates(
    session: SessionDep,
    current_user: CurrentUser,
    purchase_record_id: uuid.UUID,
) -> dict:
    try:
        candidates = service.list_candidates(
            session=session,
            current_user=current_user,
            purchase_record_id=purchase_record_id,
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    return {"count": len(candidates), "data": candidates}


@router.get("/matches")
def read_matches(
    session: SessionDep,
    current_user: CurrentUser,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> dict:
    data = service.read_matches(
        session=session,
        current_user=current_user,
        status=status,
        skip=skip,
        limit=limit,
    )
    return {"count": len(data), "data": data}


from pydantic import BaseModel


class ConfirmMatchRequest(BaseModel):
    """Confirm body. score/score_breakdown are deliberately omitted —
    the backend recomputes them from authoritative purchase/invoice state.
    """

    purchase_record_id: uuid.UUID
    invoice_file_id: uuid.UUID

    model_config = {"extra": "forbid"}


@router.post("/confirm")
def confirm_match(
    session: SessionDep,
    current_user: CurrentUser,
    req: ConfirmMatchRequest,
) -> dict:
    try:
        return service.confirm_match(
            session=session,
            current_user=current_user,
            purchase_record_id=req.purchase_record_id,
            invoice_file_id=req.invoice_file_id,
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/{match_id}/cancel")
def cancel_match(
    session: SessionDep,
    current_user: CurrentUser,
    match_id: uuid.UUID,
) -> dict:
    try:
        return service.cancel_match(
            session=session, current_user=current_user, match_id=match_id
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/{match_id}/reconfirm")
def reconfirm_match(
    session: SessionDep,
    current_user: CurrentUser,
    match_id: uuid.UUID,
) -> dict:
    try:
        return service.reconfirm_match(
            session=session, current_user=current_user, match_id=match_id
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

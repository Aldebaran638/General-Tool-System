"""Finance Dashboard Router."""

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep

from . import service
from .constants import PENDING_DEFAULT_LIMIT, PENDING_MAX_LIMIT
from .schemas import ByUserList, DashboardSummary, PendingList

router = APIRouter(prefix="/finance/dashboard", tags=["finance-dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def read_summary(
    session: SessionDep,
    current_user: CurrentUser,
) -> DashboardSummary:
    return service.read_summary(session=session, current_user=current_user)


@router.get("/pending", response_model=PendingList)
def list_pending(
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = Query(
        default=PENDING_DEFAULT_LIMIT, ge=1, le=PENDING_MAX_LIMIT
    ),
) -> PendingList:
    return service.list_pending(
        session=session, current_user=current_user, limit=limit
    )


@router.get("/by-user", response_model=ByUserList)
def list_by_user(
    session: SessionDep,
    current_user: CurrentUser,
) -> ByUserList:
    return service.list_by_user(session=session, current_user=current_user)

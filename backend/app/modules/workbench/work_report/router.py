import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.modules.workbench.work_report import service
from app.modules.workbench.work_report.schemas import (
    FieldConfigsPublic,
    FieldConfigsUpdate,
    ReportType,
    WorkReportDetail,
    WorkReportsPublic,
    WorkReportSubmissionResult,
    WorkReportSubmit,
)

router = APIRouter(prefix="/work-reports", tags=["work-reports"])


@router.get("/mine", response_model=WorkReportsPublic)
def read_my_work_reports(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    report_type: ReportType | None = None,
    period_from: date | None = None,
    period_to: date | None = None,
    submitted_from: date | None = None,
    submitted_to: date | None = None,
    keyword: str | None = Query(default=None, max_length=255),
) -> WorkReportsPublic:
    return service.list_work_reports(
        session=session,
        current_user=current_user,
        include_all=False,
        skip=skip,
        limit=limit,
        report_type=report_type,
        period_from=period_from,
        period_to=period_to,
        submitted_from=submitted_from,
        submitted_to=submitted_to,
        keyword=keyword,
    )


@router.get(
    "/admin",
    response_model=WorkReportsPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
def read_all_work_reports(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    report_type: ReportType | None = None,
    reporter: str | None = Query(default=None, max_length=255),
    period_from: date | None = None,
    period_to: date | None = None,
    submitted_from: date | None = None,
    submitted_to: date | None = None,
    keyword: str | None = Query(default=None, max_length=255),
) -> WorkReportsPublic:
    return service.list_work_reports(
        session=session,
        current_user=current_user,
        include_all=True,
        skip=skip,
        limit=limit,
        report_type=report_type,
        reporter=reporter,
        period_from=period_from,
        period_to=period_to,
        submitted_from=submitted_from,
        submitted_to=submitted_to,
        keyword=keyword,
    )


@router.get("/field-config", response_model=FieldConfigsPublic)
def read_field_config(
    session: SessionDep, _current_user: CurrentUser
) -> FieldConfigsPublic:
    return FieldConfigsPublic(data=service.get_field_configs(session))


@router.put(
    "/field-config",
    response_model=FieldConfigsPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
def update_field_config(
    *, session: SessionDep, current_user: CurrentUser, body: FieldConfigsUpdate
) -> FieldConfigsPublic:
    return FieldConfigsPublic(
        data=service.update_field_configs(
            session=session, updates=body.data, current_user=current_user
        )
    )


@router.post(
    "",
    response_model=WorkReportSubmissionResult,
    status_code=status.HTTP_201_CREATED,
)
def create_or_supplement_work_report(
    *, session: SessionDep, current_user: CurrentUser, body: WorkReportSubmit
) -> WorkReportSubmissionResult:
    return service.submit_work_report(
        session=session, payload=body, current_user=current_user
    )


@router.get("/{report_id}", response_model=WorkReportDetail)
def read_work_report(
    report_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> WorkReportDetail:
    return service.get_work_report_detail(
        session=session, report_id=report_id, current_user=current_user
    )

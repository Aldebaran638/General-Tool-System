from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.modules.workbench.work_report import service
from app.modules.workbench.work_report.schemas import (
    FieldConfigsPublic,
    FieldConfigsUpdate,
    WorkReportSubmissionResult,
    WorkReportSubmit,
)

router = APIRouter(prefix="/work-reports", tags=["work-reports"])


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

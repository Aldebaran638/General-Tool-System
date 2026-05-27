"""
WeCom Gateway Router  (/api/v1/wecom/*)

Admin & operational endpoints:

  GET  /api/v1/wecom/status           – check WeCom config + token health
  GET  /api/v1/wecom/centers          – list 中心 (root-level departments)
  GET  /api/v1/wecom/departments      – list 部门 (center's first-level children)
  POST /api/v1/wecom/sync/departments – admin: pull department tree from WeCom
  POST /api/v1/wecom/sync/users       – admin: pull user list from WeCom
  POST /api/v1/wecom/sync/all         – admin: sync departments + users

Auth routes (/api/auth/wecom/*) live in app/api/routes/wecom_auth.py
and are registered directly on the ASGI app, outside /api/v1.
"""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser
from app.modules.wecom_gateway.deps import RequireSuperAdmin
from app.modules.wecom_gateway.schemas import (
    WecomDepartment,
    WecomStatusResponse,
    WecomSyncResult,
)
from app.services.wecom import WecomNotConfiguredError, get_wecom_client

router = APIRouter(prefix="/wecom", tags=["wecom-gateway"])


# ─── Health / config ──────────────────────────────────────────────────────────

@router.get(
    "/status",
    response_model=WecomStatusResponse,
    summary="Check WeCom configuration and token health",
)
async def wecom_status(current_user: CurrentUser) -> WecomStatusResponse:
    """
    Verifies that WeCom credentials are present and that a token can be
    obtained.  Safe to call frequently; uses the cached token.
    """
    try:
        client = get_wecom_client()
    except WecomNotConfiguredError as exc:
        return WecomStatusResponse(configured=False, error=str(exc))

    try:
        token = await client.get_access_token()
        return WecomStatusResponse(
            configured=True,
            token_ok=bool(token),
            corp_id=client.corp_id,
            agent_id=client.agent_id,
        )
    except Exception as exc:
        return WecomStatusResponse(
            configured=True,
            token_ok=False,
            corp_id=client.corp_id,
            agent_id=client.agent_id,
            error=str(exc),
        )


# ─── Organization queries ─────────────────────────────────────────────────────

@router.get(
    "/centers",
    response_model=list[WecomDepartment],
    summary="List all 中心 (root-level WeCom departments)",
)
async def list_centers(current_user: CurrentUser) -> list[WecomDepartment]:
    """
    Returns every department whose parentid == 1 (i.e., direct children of the
    WeCom root).  Per the requirements these are called "中心".
    """
    try:
        client = get_wecom_client()
        departments = await client.list_departments()
    except WecomNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"WeCom API error: {exc}",
        )

    centers = [d for d in departments if d.get("parentid") == 1]
    return [
        WecomDepartment(
            id=d["id"],
            name=d["name"],
            parentid=d["parentid"],
            order=d.get("order", 0),
        )
        for d in centers
    ]


@router.get(
    "/departments",
    response_model=list[WecomDepartment],
    summary="List 部门 (center's first-level children)",
)
async def list_departments(
    current_user: CurrentUser,
    center_id: int | None = None,
) -> list[WecomDepartment]:
    """
    Returns departments that are direct children of a center.

    - If center_id is provided: returns only that center's first-level children.
    - Otherwise: returns all first-level children of all centers.
    """
    try:
        client = get_wecom_client()
        all_depts = await client.list_departments()
    except WecomNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"WeCom API error: {exc}",
        )

    if center_id is not None:
        result = [d for d in all_depts if d.get("parentid") == center_id]
    else:
        center_ids = {d["id"] for d in all_depts if d.get("parentid") == 1}
        result = [d for d in all_depts if d.get("parentid") in center_ids]

    return [
        WecomDepartment(
            id=d["id"],
            name=d["name"],
            parentid=d["parentid"],
            order=d.get("order", 0),
        )
        for d in result
    ]


# ─── Sync operations (admin only) ─────────────────────────────────────────────

@router.post(
    "/sync/departments",
    response_model=WecomSyncResult,
    summary="Pull department tree from WeCom (admin)",
)
async def sync_departments(current_user: RequireSuperAdmin) -> WecomSyncResult:
    """
    Fetches the full department tree from WeCom.

    Currently returns a summary.  Persistence into wecom_department table
    will be implemented in the contact-sync module.
    """
    errors: list[str] = []
    try:
        client = get_wecom_client()
        departments = await client.list_departments()
        return WecomSyncResult(departments_synced=len(departments), errors=errors)
    except Exception as exc:
        return WecomSyncResult(errors=[str(exc)])


@router.post(
    "/sync/users",
    response_model=WecomSyncResult,
    summary="Pull user list from WeCom root department (admin)",
)
async def sync_users(current_user: RequireSuperAdmin) -> WecomSyncResult:
    """
    Fetches all users from WeCom root department (fetch_child=1).

    Persistence will be implemented in the contact-sync module.
    """
    errors: list[str] = []
    try:
        client = get_wecom_client()
        users = await client.list_department_users(department_id=1, fetch_child=1)
        return WecomSyncResult(users_synced=len(users), errors=errors)
    except Exception as exc:
        return WecomSyncResult(errors=[str(exc)])


@router.post(
    "/sync/all",
    response_model=WecomSyncResult,
    summary="Sync departments + users from WeCom (admin)",
)
async def sync_all(current_user: RequireSuperAdmin) -> WecomSyncResult:
    """
    One-shot full sync: departments then users.
    """
    errors: list[str] = []
    departments_synced = 0
    users_synced = 0

    try:
        client = get_wecom_client()
        departments = await client.list_departments()
        departments_synced = len(departments)
    except Exception as exc:
        errors.append(f"Department sync: {exc}")

    try:
        client = get_wecom_client()
        users = await client.list_department_users(department_id=1, fetch_child=1)
        users_synced = len(users)
    except Exception as exc:
        errors.append(f"User sync: {exc}")

    return WecomSyncResult(
        departments_synced=departments_synced,
        users_synced=users_synced,
        errors=errors,
    )

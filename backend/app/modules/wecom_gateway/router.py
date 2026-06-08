"""
WeCom Gateway Router  (/api/v1/wecom/*)

Admin & operational endpoints:

  GET  /api/v1/wecom/status           – check WeCom config + token health
  GET  /api/v1/wecom/centers          – list 中心 (root-level departments)
  GET  /api/v1/wecom/departments      – list 部门 (center's first-level children)

Sync endpoints have been moved to the data_sync module:
  /api/v1/data-sync/wecom-department/*
  /api/v1/data-sync/wecom-member/*

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


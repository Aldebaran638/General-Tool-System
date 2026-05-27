"""
WeCom Gateway Dependencies

Provides FastAPI-compatible dependency annotations for role-based access:

    CurrentWecomUser   – any logged-in user with a WeCom identity
    RequireSuperAdmin  – SUPER_ADMIN or is_superuser
    RequireExamAdmin   – SUPER_ADMIN | EXAM_ADMIN | is_superuser

Usage in a route
----------------
    from app.modules.wecom_gateway.deps import RequireExamAdmin

    @router.get("/exams")
    def list_exams(current_user: RequireExamAdmin) -> list[ExamOut]:
        ...
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import SystemUserRole, User


# ─── WeCom identity check ─────────────────────────────────────────────────────

def _require_wecom_user(current_user: CurrentUser) -> User:
    """Reject users who have not authenticated via WeCom."""
    if not current_user.wecom_userid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "This endpoint requires a WeCom identity. "
                "Please log in via the WeCom app."
            ),
        )
    return current_user


CurrentWecomUser = Annotated[User, Depends(_require_wecom_user)]


# ─── Role-based access ────────────────────────────────────────────────────────

def _make_role_checker(*role_codes: str):
    """
    Dependency factory for role enforcement.

    is_superuser flag bypasses all role checks (always granted).
    Otherwise the user must have one of the given role_codes in
    the system_user_role table.

    Example
    -------
        RequireExamAdmin = Annotated[
            User, Depends(_make_role_checker("SUPER_ADMIN", "EXAM_ADMIN"))
        ]
    """

    def _check(current_user: CurrentWecomUser, session: SessionDep) -> User:
        if current_user.is_superuser:
            return current_user

        role = session.exec(
            select(SystemUserRole).where(
                SystemUserRole.userid == current_user.wecom_userid,
                SystemUserRole.role_code.in_(list(role_codes)),
            )
        ).first()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {' or '.join(role_codes)}.",
            )
        return current_user

    return _check


# Pre-built role dependency types
# Import these in route handlers directly.

RequireSuperAdmin = Annotated[
    User,
    Depends(_make_role_checker("SUPER_ADMIN")),
]

RequireExamAdmin = Annotated[
    User,
    Depends(_make_role_checker("SUPER_ADMIN", "EXAM_ADMIN")),
]

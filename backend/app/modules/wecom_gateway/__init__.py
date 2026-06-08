"""
WeCom Gateway Module

Acts as the gateway between WeCom and the rest of the application.

What this module owns
---------------------
• /api/v1/wecom/status          – config + token health check
• /api/v1/wecom/centers         – list 中心
• /api/v1/wecom/departments     – list 部门
• /api/v1/wecom/sync/*          – admin contact-sync operations
• deps.py                       – CurrentWecomUser, RequireSuperAdmin,
                                  RequireExamAdmin  (used by all other modules)

What this module does NOT own
------------------------------
• /api/auth/wecom/*  – OAuth routes; those live in api/routes/wecom_auth.py
  and are registered directly on the ASGI app outside /api/v1.

Other modules that need WeCom identity checking should import from:
    from app.modules.wecom_gateway.deps import (
        CurrentWecomUser,
        RequireSuperAdmin,
        RequireExamAdmin,
    )
"""

from app.modules.registry import register_module
from app.modules.wecom_gateway.router import router

register_module(
    name="wecom_gateway",
    group="platform",
    router=router,
    models=[],
)

__all__ = ["router"]

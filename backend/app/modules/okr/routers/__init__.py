"""
OKR Module — Router 汇总

按 OKR 总览的层级组织子路由：
  overview    — OKR 总览：Objective CRUD + /overview/departments、/overview/members 看板
  krs         — KR 管理与我的任务
  departments — 部门管理
"""

from fastapi import APIRouter

from app.modules.okr.routers import departments, krs, overview

router = APIRouter(prefix="/okr", tags=["okr"])
router.include_router(overview.router)
router.include_router(krs.router)
router.include_router(departments.router)

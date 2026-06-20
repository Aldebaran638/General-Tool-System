"""
Contract Filler Tool Module

Provides a dedicated tool for filling the construction contract template
(工程承包合同) with named versions and DOCX export.
"""

from app.modules.registry import register_module

from .models import FilledVersion
from .router import router

register_module(
    name="contract_filler",
    group="contracts",
    router=router,
    models=[FilledVersion],
)

__all__ = ["router"]

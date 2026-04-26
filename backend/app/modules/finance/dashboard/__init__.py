"""Finance Dashboard Tool Module

Read-only aggregation tool. Provides cross-module statistics built from
purchase_records, invoice_files, and invoice_matching modules. Self-registers
with the global module registry on import.
"""

from app.modules.registry import register_module

from .router import router

register_module(
    name="dashboard",
    group="finance",
    router=router,
    models=[],
)

__all__ = ["router"]

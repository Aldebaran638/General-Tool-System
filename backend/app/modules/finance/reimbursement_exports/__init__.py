"""
Reimbursement Exports Tool Module

This module provides reimbursement Excel export functionality.
It self-registers with the global module registry on import.
"""

from app.modules.registry import register_module

# Import models first (no side effects)
from .models import ReimbursementExport, ReimbursementExportItem

# Import and register router
from .router import router

# Register this module with the global registry
register_module(
    name="reimbursement_exports",
    group="finance",
    router=router,
    models=[ReimbursementExport, ReimbursementExportItem],
)

__all__ = ["router"]

"""
Invoice Files Tool Module

This module provides invoice file management functionality.
It self-registers with the global module registry on import.
"""

from app.modules.registry import register_module

# Import models first (no side effects)
from .models import InvoiceFile

# Import and register router
from .router import router

# Register this module with the global registry
register_module(
    name="invoice_files",
    group="finance",
    router=router,
    models=[InvoiceFile],
)

__all__ = ["router"]

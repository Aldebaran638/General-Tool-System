"""
Purchase Records Tool Module

This module provides purchase record management functionality.
It self-registers with the global module registry on import.
"""

from app.modules.registry import register_module

# Import models first (no side effects)
from .models import PurchaseRecord

# Import and register router
from .router import router

# Register this module with the global registry
register_module(
    name="purchase_records",
    group="finance",
    router=router,
    models=[PurchaseRecord],
)

__all__ = ["router"]

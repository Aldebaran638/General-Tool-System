"""
Invoice Matching Tool Module

This module provides invoice-purchase matching functionality.
It self-registers with the global module registry on import.
"""

from app.modules.registry import register_module

from .models import InvoiceMatch
from .router import router

register_module(
    name="invoice_matching",
    group="finance",
    router=router,
    models=[InvoiceMatch],
)

__all__ = ["router"]

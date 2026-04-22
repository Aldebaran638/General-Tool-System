"""
Project Management Tool Module

This module provides project/item management functionality.
It self-registers with the global module registry on import.
"""

from app.modules.registry import register_module

# Import models first (no side effects)
from .models import Item

# Import and register router
# Note: router imports service which imports local models,
# so we must ensure models are imported first
from .router import router

# Register this module with the global registry
register_module(
    name="project_management",
    group="workbench",
    router=router,
    models=[Item],
)

__all__ = ["router"]

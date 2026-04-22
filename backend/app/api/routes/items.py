"""
Legacy Items Route (Compatibility Layer)

⚠️  DEPRECATED: This file exists only for backward compatibility.

The actual implementation lives in:
    app/modules/workbench/project_management/

New code should import from the module directly:
    from app.modules.workbench.project_management.router import router

This file will be removed in a future major version.
"""

from app.modules.registry import registry

# Get the project_management router from the registry
# This ensures legacy code uses the same instance as the registry
router = registry.get_router("project_management")

__all__ = ["router"]

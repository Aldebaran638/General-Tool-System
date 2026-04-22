from fastapi import APIRouter

from app.api.routes import login, private, users, utils
from app.core.config import settings
from app.modules.registry import auto_discover_modules, registry

api_router = APIRouter()

# =============================================================================
# Platform Routes (always included)
# =============================================================================
# These are core platform features, not tool modules.
# They are explicitly imported because they are part of the base platform.

api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)


# =============================================================================
# Tool Module Routes (auto-discovered)
# =============================================================================
# New tool modules self-register via the module registry.
# They should NOT be manually imported here.
#
# To add a new tool:
#   1. Create module at: app/modules/<group>/<tool_name>/
#   2. In the module's __init__.py, call:
#      from app.modules.registry import register_module
#      register_module(name="tool_name", group="group", router=router, models=[...])
#   3. Done. No changes needed in this file.

# Auto-discover all modules under app.modules
auto_discover_modules("app.modules")

# Include all registered module routers
for module_name, router in registry.get_routers():
    api_router.include_router(router)


# =============================================================================
# Legacy Route Compatibility
# =============================================================================
# The following routers are kept for backward compatibility.
# They reference the same module routers already registered above.
# New code should not depend on these legacy import paths.

# Note: items.router is auto-discovered via the registry from project_management.
# The legacy import path (app.api.routes.items) still works for backward
# compatibility but is no longer the primary registration mechanism.

from app.api.routes import items  # noqa: F401 - kept for import compatibility


# =============================================================================
# Development Routes
# =============================================================================

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)

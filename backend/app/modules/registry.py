"""
Module Registry System

This module provides a registry pattern for tool modules.
New tools register themselves instead of being manually imported in legacy routes.

Usage:
    # In your module's __init__.py:
    from app.modules.registry import register_module
    
    register_module(
        name="project_management",
        group="workbench",
        router=router,
        models=[Item],  # optional
    )
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import APIRouter
    from sqlmodel import SQLModel


@dataclass
class ModuleInfo:
    """Information about a registered tool module."""

    name: str
    group: str
    router: APIRouter
    models: list[type[SQLModel]] = field(default_factory=list)


class ModuleRegistry:
    """Registry for tool modules.

    This is the central authority for module discovery.
    Legacy routes should import from here, not directly from modules.
    """

    def __init__(self) -> None:
        self._modules: dict[str, ModuleInfo] = {}
        self._groups: dict[str, list[str]] = {}

    def register(
        self,
        *,
        name: str,
        group: str,
        router: APIRouter,
        models: list[type[SQLModel]] | None = None,
    ) -> None:
        """Register a tool module.

        Args:
            name: Unique module identifier (e.g., "project_management")
            group: Module group (e.g., "workbench")
            router: FastAPI router instance
            models: SQLModel classes defined by this module

        Raises:
            ValueError: If module name already registered
        """
        if name in self._modules:
            raise ValueError(f"Module '{name}' is already registered")

        info = ModuleInfo(
            name=name,
            group=group,
            router=router,
            models=models or [],
        )
        self._modules[name] = info

        if group not in self._groups:
            self._groups[group] = []
        self._groups[group].append(name)

    def get_router(self, name: str) -> APIRouter:
        """Get router by module name."""
        if name not in self._modules:
            raise KeyError(f"Module '{name}' not found in registry")
        return self._modules[name].router

    def get_routers(self) -> list[tuple[str, APIRouter]]:
        """Get all registered routers with their names."""
        return [(name, info.router) for name, info in self._modules.items()]

    def get_modules_by_group(self, group: str) -> list[ModuleInfo]:
        """Get all modules in a group."""
        names = self._groups.get(group, [])
        return [self._modules[name] for name in names]

    def get_all_models(self) -> list[type[SQLModel]]:
        """Get all models from all registered modules."""
        models: list[type[SQLModel]] = []
        for info in self._modules.values():
            models.extend(info.models)
        return models

    def list_modules(self) -> list[str]:
        """List all registered module names."""
        return list(self._modules.keys())

    def list_groups(self) -> list[str]:
        """List all registered groups."""
        return list(self._groups.keys())


# Global registry instance
registry = ModuleRegistry()


def register_module(
    *,
    name: str,
    group: str,
    router: APIRouter,
    models: list[type[SQLModel]] | None = None,
) -> None:
    """Convenience function to register a module with the global registry."""
    registry.register(
        name=name,
        group=group,
        router=router,
        models=models,
    )


def auto_discover_modules(package_name: str = "app.modules") -> None:
    """Auto-discover and import all module packages.

    This walks the modules directory and imports each module's __init__.py,
    which should trigger the register_module() calls.

    Args:
        package_name: Root package name to scan (default: "app.modules")
    """
    try:
        package = importlib.import_module(package_name)
    except ImportError:
        return

    # Walk through groups (e.g., workbench)
    for _, group_name, ispkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        if not ispkg:
            continue

        group_module = importlib.import_module(group_name)

        # Walk through tools in each group
        for _, tool_name, ispkg in pkgutil.iter_modules(group_module.__path__, group_name + "."):
            if not ispkg:
                continue

            # Import the tool module - its __init__.py should register itself
            importlib.import_module(tool_name)

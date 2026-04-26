"""
backend/tests/platform/remove_workbench/index_test.py

验证 workbench/project_management 示例工具已彻底从后端移除。
"""

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.modules.registry import registry

API_ITEMS_URL = f"{settings.API_V1_STR}/items/"


def test_items_endpoint_returns_404(client: TestClient) -> None:
    """访问 /api/v1/items/ 应返回 404，路由不再存在。"""
    response = client.get(API_ITEMS_URL)
    assert response.status_code == 404


def test_openapi_does_not_contain_items() -> None:
    """OpenAPI schema 中不应包含 /api/v1/items/ 路径。"""
    openapi_schema = app.openapi()
    paths = openapi_schema.get("paths", {})
    # 任何包含 /items 的路径都不应存在
    items_paths = [p for p in paths if "/items" in p]
    assert len(items_paths) == 0, f"Unexpected items paths in OpenAPI: {items_paths}"


def test_registry_does_not_contain_project_management() -> None:
    """模块注册表中不应包含 project_management。"""
    modules = registry.list_modules()
    assert "project_management" not in modules, f"project_management still in registry: {modules}"


def test_registry_does_not_contain_workbench_group() -> None:
    """模块注册表中不应包含 workbench 工具组。"""
    groups = registry.list_groups()
    assert "workbench" not in groups, f"workbench group still in registry: {groups}"

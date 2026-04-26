# Round 006 Tasks - remove_workbench_project_management

## BE

- 删除 `backend/app/modules/workbench/project_management/`。
- 删除空的 `backend/app/modules/workbench/`。
- 删除 `backend/app/api/routes/items.py`。
- 删除 `backend/app/api/main.py` 中 items 兼容 import。
- 新增 Alembic migration 删除 `item` 表。
- 清理 `backend/app/models.py`、`backend/app/models_core.py`、`backend/app/crud.py` 中 Item/project_management 残留说明。
- 删除后端项目管理测试和测试 helper。
- 清理 `backend/tests/conftest.py` 中 `Item` 依赖。
- 新增后端删除验证测试。
- 执行迁移和相关后端测试。
- 输出 `docs/rounds/round-006/backend-report.md`。

## FE

- 删除 `frontend/src/tools/workbench/project_management/`。
- 删除空的 `frontend/src/tools/workbench/`。
- 删除 `frontend/src/routes/_layout/items.tsx`。
- 删除 `frontend/src/components/Items/`。
- 删除项目管理 Playwright 测试。
- 删除 `frontend/src/config/tool-navigation.tsx` 中 project_management 注册 import。
- 更新或重新生成 `frontend/src/routeTree.gen.ts`，确保无 `/items`。
- 清理用户可见文案中的 items/project management。
- 新增或更新前端删除验证测试。
- 执行前端构建。
- 输出 `docs/rounds/round-006/frontend-report.md`。

## INT

- 确认 OpenAPI 无 `/api/v1/items`。
- 确认前端侧边栏无 workbench 工具组。
- 确认财务工具组不受影响。
- 确认数据库迁移到 head 后 `item` 表不存在。
- 确认删除报告中明确记录破坏性迁移。

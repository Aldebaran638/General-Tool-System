# Round 006 Backend Report - remove_workbench_project_management

## 输入物路径

- `docs/rounds/round-006/requirements.md`
- `docs/rounds/round-006/design.md`
- `docs/rounds/round-006/test-plan.md`
- `docs/rounds/round-006/tasks.md`
- `docs/rounds/round-006/dispatch-backend.md`
- `backend/app/MODULE_ARCHITECTURE.md`
- `backend/app/modules/README.md`

## 删除文件

- `backend/app/modules/workbench/project_management/`（含 __init__.py, models.py, router.py, service.py, repository.py, schemas.py）
- `backend/app/modules/workbench/`（删除 project_management 后为空目录）
- `backend/app/api/routes/items.py`
- `backend/tests/workbench/project_management/index_test.py`
- `backend/tests/workbench/`（删除后为空的目录）
- `backend/tests/items/index_test.py`
- `backend/tests/items/helpers.py`
- `backend/tests/items/__init__.py`
- `backend/tests/utils/item.py`

## 修改文件

- `backend/app/api/routes/users.py`
  - 删除 `from app.modules.workbench.project_management.models import Item`
  - 删除 `from sqlmodel import col, delete`（不再使用）
  - 删除 `delete_user` 中的 `delete(Item)` 级联删除逻辑
- `backend/app/api/main.py`
  - 删除 Legacy Route Compatibility 整段注释及 `from app.api.routes import items` import
- `backend/app/models.py`
  - 清理 docstring 中关于 Item models have been moved to project_management 的说明
- `backend/app/models_core.py`
  - 删除 User model 中 `# Relationship to items is defined via back_populates in the Item model` 注释
- `backend/app/crud.py`
  - 删除 `# NOTE: create_item has been moved to the project_management module.` 说明

## 新增 migration

- `backend/app/alembic/versions/a4e06ea5ffad_drop_item_table.py`
  - `upgrade()`: `DROP TABLE IF EXISTS item CASCADE; DROP TYPE IF EXISTS itemstate CASCADE;`
  - `downgrade()`: 重建 item 表（UUID id, title, description, created_at, owner_id FK -> user.id ondelete CASCADE, amount, test_amount）

## 删除的 API

- `/api/v1/items/` GET（列表）
- `/api/v1/items/` POST（创建）
- `/api/v1/items/{id}` GET（详情）
- `/api/v1/items/{id}` PUT（更新）
- `/api/v1/items/{id}` DELETE（删除）

## 删除的数据表

- `item`（project_management 模块的数据表）

## 破坏性迁移说明

- 新增 migration `a4e06ea5ffad_drop_item_table` 是**破坏性迁移**。
- `upgrade()` 会永久删除 `item` 表及其索引、约束、数据。
- `downgrade()` 可重建空表结构，但已删除的数据不可恢复。
- 报告已明确记录此破坏性操作。

## 新增测试

- `backend/tests/platform/remove_workbench/index_test.py`
  - `test_items_endpoint_returns_404`: 确认 `/api/v1/items/` 返回 404
  - `test_openapi_does_not_contain_items`: 确认 OpenAPI paths 不含 `/items`
  - `test_registry_does_not_contain_project_management`: 确认注册表无 `project_management`
  - `test_registry_does_not_contain_workbench_group`: 确认注册表无 `workbench` 组

## 迁移验证结果

```bash
docker compose exec backend bash -c "cd /app/backend && alembic upgrade head && alembic current"
```

结果：`a4e06ea5ffad (head)`，升级成功，无报错。

## 后端测试结果

```bash
docker compose exec backend bash -c "cd /app/backend && pytest tests/platform/remove_workbench/index_test.py -q"
```

结果：`4 passed, 3 warnings`

```bash
docker compose exec backend bash -c "cd /app/backend && pytest tests/finance/purchase_records/index_test.py -q"
```

结果：`42 passed, 3 warnings`

```bash
docker compose exec backend bash -c "cd /app/backend && pytest tests/finance/invoice_files/index_test.py -q"
```

结果：`54 passed, 3 warnings`

```bash
docker compose exec backend bash -c "cd /app/backend && pytest tests/finance/invoice_matching/index_test.py -q"
```

结果：`35 passed, 3 warnings`

```bash
docker compose exec backend bash -c "cd /app/backend && pytest tests/api/routes/test_users.py -q"
```

结果：`27 passed, 3 warnings`

```bash
docker compose exec backend bash -c "cd /app/backend && pytest tests/crud/test_user.py -q"
```

结果：`10 passed, 3 warnings`

## OpenAPI 验证结果

- 测试 `test_openapi_does_not_contain_items` 通过。
- OpenAPI schema paths 中无任何包含 `/items` 的路径。

## 模块注册验证结果

- `registry.list_modules()` 返回 `['invoice_files', 'purchase_records', 'invoice_matching']`（`project_management` 已移除）。
- `registry.list_groups()` 返回 `['finance']`（`workbench` 组已移除）。

## 越界自检

- 未修改 `frontend/**`。
- 未修改 `skills/**`。
- 未修改 `backend/app/modules/finance/**`。
- 未修改用户表结构。
- 未修改 Round 005 发票匹配代码或文档。
- 唯一触及的非目标文件是 `backend/app/api/routes/users.py`（删除 Item 级联删除），属于删除 workbench 后的必要清理。
- `backend/app/modules/finance/dashboard/` 中出现了 `PendingItem`, `ByUserItem` 等类名，但它们是 Round007 dashboard 模块的业务概念，与 workbench 的 `Item` 模型无关，未做修改。

## 未完成项

- 无。

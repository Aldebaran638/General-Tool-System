# 后端 AI 派单 - Round 006 remove_workbench_project_management

你负责后端删除任务：移除 `workbench / project_management` 示例工具。

## 必须先读取

1. `skills/members/后端skill.md`
2. `skills/tool-module-builder/SKILL.md`
3. `docs/rounds/round-006/requirements.md`
4. `docs/rounds/round-006/design.md`
5. `docs/rounds/round-006/test-plan.md`
6. `docs/rounds/round-006/tasks.md`
7. `backend/app/MODULE_ARCHITECTURE.md`
8. `backend/app/modules/README.md`
9. `backend/app/modules/workbench/project_management/`
10. `backend/app/api/routes/items.py`
11. `backend/tests/workbench/project_management/index_test.py`
12. `backend/tests/items/index_test.py`
13. `backend/tests/conftest.py`

## 任务范围

彻底删除后端 `workbench / project_management`：

- 删除后端模块。
- 删除 `/api/v1/items` API。
- 删除 `item` 表。
- 删除相关测试和 helper。
- 清理遗留注释与兼容 import。

## 允许修改

- `backend/app/modules/workbench/**`
- `backend/app/api/routes/items.py`
- `backend/app/api/main.py`
- `backend/app/alembic/versions/**`
- `backend/app/models.py`
- `backend/app/models_core.py`
- `backend/app/crud.py`
- `backend/tests/workbench/**`
- `backend/tests/items/**`
- `backend/tests/utils/item.py`
- `backend/tests/conftest.py`
- `backend/tests/platform/remove_workbench/**`
- `docs/rounds/round-006/backend-report.md`

## 禁止修改

- `frontend/**`
- `skills/**`
- `.env`
- 财务业务模块，除非只是为了修复删除 Item 后的 import 错误
- 用户表结构
- Round 005 发票匹配文档和代码

## 必须实现

- 删除 `backend/app/modules/workbench/project_management/`。
- 如果 `backend/app/modules/workbench/` 为空，删除该目录。
- 删除 `backend/app/api/routes/items.py`。
- 删除 `backend/app/api/main.py` 中 items 兼容 import。
- 新增 Alembic migration 删除 `item` 表。
- `downgrade()` 应能重建旧 `item` 表结构，除非报告中明确说明不可逆原因。
- 删除项目管理后端测试和 helper。
- 清理 `backend/tests/conftest.py` 中 `Item` import 或清理逻辑。
- 清理 `backend/app/models.py`、`backend/app/models_core.py`、`backend/app/crud.py` 中已过时的 Item/project_management 说明。
- 新增测试确认 `/api/v1/items/` 返回 404 或不在 OpenAPI 中。
- 新增测试确认模块注册表不包含 `project_management`。

## 测试责任

你必须创建或更新：

- `backend/tests/platform/remove_workbench/index_test.py`

你必须执行：

- `docker compose exec backend alembic upgrade head`
- `docker compose exec backend alembic current`
- `docker compose exec backend pytest tests/platform/remove_workbench/index_test.py -q`
- `docker compose exec backend pytest tests/finance/purchase_records/index_test.py -q`
- `docker compose exec backend pytest tests/finance/invoice_files/index_test.py -q`

如果 Round 005 后端已合并，还必须执行：

- `docker compose exec backend pytest tests/finance/invoice_matching/index_test.py -q`

## 交付报告

输出到：

- `docs/rounds/round-006/backend-report.md`

报告必须包含：

- 输入物路径
- 删除文件
- 修改文件
- 新增 migration
- 删除的 API
- 删除的数据表
- 破坏性迁移说明
- 新增测试
- 迁移验证结果
- 后端测试结果
- OpenAPI 验证结果
- 模块注册验证结果
- 越界自检
- 未完成项

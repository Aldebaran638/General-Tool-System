# Round 006 Requirements - remove_workbench_project_management

## 背景

`workbench / project_management` 是早期示例工具，当前发票系统已经转向 `finance` 工具组。继续保留项目管理会带来：

- 前端导航存在无关工具组。
- 后端仍暴露 `/api/v1/items` 示例 API。
- 代码中保留 `Item` 示例模型和测试辅助函数，影响后续架构清晰度。
- 用户管理删除提示仍提到 items，容易误导。

本轮目标是彻底删除 `workbench` 工具组及其唯一工具 `project_management`。

## 目标

1. 删除前端 `workbench / 项目管理` 工具入口。
2. 删除前端 `/items` 页面与项目管理工具代码。
3. 删除后端 `workbench/project_management` 模块。
4. 删除或废弃 `/api/v1/items` 兼容路由。
5. 删除 `item` 数据表及相关迁移后的模型引用。
6. 删除项目管理相关测试和测试辅助函数。
7. 构建、迁移和现有财务工具测试继续通过。

## 非目标

- 不改财务工具业务逻辑。
- 不改 Round 005 发票匹配设计。
- 不改用户角色/权限体系。
- 不处理 Round 003 i18n 的临时前端工作区问题。
- 不保留 workbench 作为空工具组。

## 删除范围

### 后端

- `backend/app/modules/workbench/project_management/`
- `backend/app/modules/workbench/`，如果删除 project_management 后为空。
- `backend/app/api/routes/items.py`
- `backend/tests/workbench/project_management/`
- `backend/tests/items/`
- `backend/tests/utils/item.py`
- `backend/app/crud.py` 中只服务于 `create_item` 兼容的残留说明。
- `backend/app/models.py` 中关于 Item legacy compatibility 的残留说明。
- `backend/app/models_core.py` 中关于 Item relationship 的残留注释。
- `backend/app/api/main.py` 中 items 兼容 import。
- 测试配置中对 `Item` 的清理依赖。

### 前端

- `frontend/src/tools/workbench/project_management/`
- `frontend/src/tools/workbench/`，如果删除 project_management 后为空。
- `frontend/src/routes/_layout/items.tsx`
- `frontend/src/components/Items/`
- `frontend/tests/workbench/project_management/`
- `frontend/tests/items/`
- `frontend/src/config/tool-navigation.tsx` 中 project_management 注册 import。
- `frontend/src/routeTree.gen.ts` 重新生成后不得包含 `/items`。
- i18n 字典中与项目管理/items 相关的用户可见文案应清理或改为中性文案。

## 数据库要求

- 新增 Alembic migration 删除 `item` 表。
- migration 必须在报告中明确这是破坏性删除。
- 如果表不存在，迁移应尽量幂等或使用 Alembic 常规安全写法，避免空库迁移失败。
- 不得删除用户表或财务业务表。

## 路由要求

- `/api/v1/items` 不再作为业务 API 暴露。
- 前端 `/items` 路由不再存在。
- 删除后访问 `/items` 应进入现有 NotFound 或路由未匹配状态，不需要新增重定向。

## 验收标准

- 后端自动发现模块中不再注册 `project_management`。
- OpenAPI 中不再包含 `/api/v1/items`。
- 前端导航中不再出现 `workbench`、`项目管理`、`Project Management`。
- 前端构建通过。
- 后端迁移到 head 成功。
- 财务相关后端测试仍通过。
- 用户管理提示不再提到 items。

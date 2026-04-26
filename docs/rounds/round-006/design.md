# Round 006 Design - remove_workbench_project_management

## 总体策略

本轮不是隐藏入口，而是删除示例工具。删除必须覆盖三层：

1. 工具注册层：不再注册 `workbench/project_management`。
2. 路由/API 层：移除 `/items` 前后端路由。
3. 数据层：删除 `item` 表及相关测试辅助代码。

## 后端设计

### 模块删除

删除目录：

```text
backend/app/modules/workbench/project_management/
backend/app/modules/workbench/
```

如果 `workbench` 下没有其他模块，应删除整个 `workbench` 目录。模块自动发现应自然不再发现该组。

### API 删除

删除：

```text
backend/app/api/routes/items.py
```

并删除：

```python
from app.api.routes import items
```

这类兼容 import。`/api/v1/items` 不再挂载。

### 数据库迁移

新增 migration：

```text
drop item table
```

建议迁移内容：

- `upgrade()` 删除 `item` 表。
- `downgrade()` 可重建旧表结构，便于回滚。

注意：

- 这是破坏性迁移，报告必须明确。
- 不要修改旧初始化 migration。

### 模型兼容说明清理

清理已经不再成立的注释：

- `backend/app/models.py` 中 Item 已迁移到 project_management 的说明。
- `backend/app/models_core.py` 中 Item relationship 注释。
- `backend/app/crud.py` 中 `create_item` 兼容说明。

如果 `backend/app/crud.py` 删除后为空或只剩无意义兼容层，可由后端 AI 判断是否删除；但不得影响用户相关 CRUD。

### 测试清理

删除项目管理测试：

```text
backend/tests/workbench/project_management/
backend/tests/items/
backend/tests/utils/item.py
```

清理 `backend/tests/conftest.py` 中对 `Item` 的 import 或清理逻辑。

新增或更新一个轻量测试确认：

- 模块注册中无 `project_management`。
- `/api/v1/items/` 返回 404。
- OpenAPI 不包含 `/api/v1/items/`。

## 前端设计

### 工具删除

删除：

```text
frontend/src/tools/workbench/project_management/
frontend/src/tools/workbench/
frontend/src/routes/_layout/items.tsx
frontend/src/components/Items/
```

### 导航删除

删除 `frontend/src/config/tool-navigation.tsx` 中：

```ts
import "@/tools/workbench/project_management"
```

`workbench` 工具组不应再出现在侧边栏。

### 路由生成

重新运行前端构建或路由 codegen。最终：

- `frontend/src/routeTree.gen.ts` 不应包含 `/_layout/items`。
- 类型中不应包含 `/items`。

### 文案清理

删除或修正用户可见文案中的 items：

- 用户删除确认文案不应再说 “All items associated with this user...”
- i18n 字典中的同类文案应改为中性表达，例如 “Associated data may be affected...” 或业务实际文案。

## 风险

- 旧测试、旧 SDK 生成文件可能仍引用 `/items`。
- `routeTree.gen.ts` 若未重新生成，会导致构建失败或幽灵路由。
- 后端 `models.py` 兼容说明不清理会误导后续 AI。
- 删除 `item` 表是破坏性操作；需要在报告中明确。

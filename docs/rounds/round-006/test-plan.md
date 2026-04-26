# Round 006 Test Plan - remove_workbench_project_management

## 后端验证

必须执行：

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
docker compose exec backend pytest tests/finance/purchase_records/index_test.py -q
docker compose exec backend pytest tests/finance/invoice_files/index_test.py -q
```

建议新增或更新测试：

```text
backend/tests/platform/remove_workbench/index_test.py
```

覆盖：

- `/api/v1/items/` 返回 404。
- OpenAPI schema 不包含 `/api/v1/items/`。
- 模块注册表不包含 `project_management`。

如 Round 005 已引入 `invoice_matching`，还应追加：

```bash
docker compose exec backend pytest tests/finance/invoice_matching/index_test.py -q
```

## 前端验证

必须执行：

```bash
docker compose exec frontend bun run build
```

建议新增或更新测试：

```text
frontend/tests/platform/remove-workbench/index.spec.ts
```

覆盖：

- 侧边栏不显示 `workbench`。
- 侧边栏不显示 `项目管理` / `Project Management`。
- 访问 `/items` 不显示项目管理页面。
- 用户删除确认文案不再包含 items。

如果 Playwright 因环境限制无法执行，报告必须记录真实命令、真实输出和阻塞原因。

## 回归范围

- 财务工具组仍显示。
- 购买记录页面仍可打开。
- 发票文件页面仍可打开。
- 用户管理页面仍可打开。
- 登录后默认页不跳转到 `/items`。

## 不接受的结果

- 只隐藏前端导航，但后端 `/api/v1/items` 仍可用。
- 只删除后端模块，但前端仍有 `/items` route。
- 删除 workbench 时误删 finance 工具。
- 旧 `Item` 测试辅助函数仍存在。
- `routeTree.gen.ts` 仍包含 `/items`。

# 前端 AI 派单 - Round 006 remove_workbench_project_management

你负责前端删除任务：移除 `workbench / 项目管理` 示例工具。

## 必须先读取

1. `skills/members/前端skill.md`
2. `docs/rounds/round-006/requirements.md`
3. `docs/rounds/round-006/design.md`
4. `docs/rounds/round-006/test-plan.md`
5. `docs/rounds/round-006/tasks.md`
6. `frontend/src/config/tool-navigation.tsx`
7. `frontend/src/tools/registry.ts`
8. `frontend/src/tools/workbench/project_management/`
9. `frontend/src/routes/_layout/items.tsx`
10. `frontend/src/components/Items/`
11. `frontend/tests/items/index.spec.ts`
12. `frontend/tests/workbench/project_management/index.spec.ts`
13. `frontend/src/routeTree.gen.ts`

## 任务范围

彻底删除前端 `workbench / 项目管理`：

- 删除工具目录。
- 删除 `/items` 路由。
- 删除侧边栏注册入口。
- 删除项目管理测试。
- 清理用户可见文案中关于 items 的残留。

## 允许修改

- `frontend/src/tools/workbench/**`
- `frontend/src/routes/_layout/items.tsx`
- `frontend/src/routeTree.gen.ts`
- `frontend/src/config/tool-navigation.tsx`
- `frontend/src/components/Items/**`
- `frontend/src/components/Admin/**`
- `frontend/src/i18n/**`
- `frontend/tests/items/**`
- `frontend/tests/workbench/**`
- `frontend/tests/platform/remove-workbench/**`
- `docs/rounds/round-006/frontend-report.md`

## 禁止修改

- `backend/**`
- `skills/**`
- 财务工具业务逻辑
- Round 005 发票匹配文档和代码
- 与删除 workbench 无关的全局视觉重构

## 必须实现

- 删除 `frontend/src/tools/workbench/project_management/`。
- 如果 `frontend/src/tools/workbench/` 为空，删除该目录。
- 删除 `frontend/src/routes/_layout/items.tsx`。
- 删除 `frontend/src/components/Items/`。
- 删除 `frontend/tests/items/`。
- 删除 `frontend/tests/workbench/project_management/`。
- 删除 `frontend/src/config/tool-navigation.tsx` 中 `@/tools/workbench/project_management` import。
- 重新生成或更新 `frontend/src/routeTree.gen.ts`，确保无 `/items`。
- 侧边栏不再出现 `workbench`、`项目管理`、`Project Management`。
- 用户管理删除确认文案不再提到 items。
- 如果 Round 003 i18n 已合并，清理三语言字典中的 items/project management 残留。

## 测试责任

你必须创建或更新：

- `frontend/tests/platform/remove-workbench/index.spec.ts`

你必须执行：

- `docker compose exec frontend bun run build`
- `docker compose exec frontend bun run test -- tests/platform/remove-workbench/index.spec.ts --reporter=line`

如果 Playwright 因环境限制无法执行，必须在 frontend report 中记录真实命令、真实输出和阻塞原因，不得写成通过。

## 交付报告

输出到：

- `docs/rounds/round-006/frontend-report.md`

报告必须包含：

- 输入物路径
- 删除文件
- 修改文件
- 删除的路由
- 删除的导航入口
- routeTree 验证结果
- 构建结果
- Playwright 结果
- 越界自检
- 未完成项

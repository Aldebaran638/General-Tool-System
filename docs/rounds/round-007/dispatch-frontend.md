# 前端 AI 派单 - Round 007 finance_dashboard

你负责单工具前端任务：`finance / dashboard`。

## 必须先读取

1. `skills/members/前端skill.md`
2. `docs/rounds/round-007/requirements.md`
3. `docs/rounds/round-007/design.md`
4. `docs/rounds/round-007/test-plan.md`
5. `docs/rounds/round-007/tasks.md`
6. `frontend/src/config/tool-navigation.tsx`
7. `frontend/src/tools/registry.ts`
8. `frontend/src/tools/finance/purchase_records/`
9. `frontend/src/tools/finance/invoice_files/`
10. `frontend/src/i18n/`，如果 Round 003 已合并

## 任务范围

实现财务统计前端工具：

- 工具目录：`frontend/src/tools/finance/dashboard/`
- 路由：`frontend/src/routes/_layout/finance.dashboard.tsx`
- 测试目录：`frontend/tests/finance/dashboard/`

## 允许修改

- `frontend/src/tools/finance/dashboard/**`
- `frontend/src/routes/_layout/finance.dashboard.tsx`
- `frontend/src/config/tool-navigation.tsx`
- `frontend/src/routeTree.gen.ts`
- `frontend/src/i18n/**`，仅限新增 dashboard 文案
- `frontend/tests/finance/dashboard/**`
- `docs/rounds/round-007/frontend-report.md`

## 禁止修改

- `backend/**`
- `skills/**`
- 购买记录和发票文件现有业务逻辑
- 用户角色体系
- 签字相关功能
- Round 003 i18n 未完成部分，除非只是新增 dashboard 字典

## 必须实现

- 注册 `finance / dashboard` 工具。
- 新增 `/finance/dashboard` 路由。
- 调用后端 summary / pending / by-user API。
- 展示购买记录、发票、匹配三组统计卡片。
- 展示待处理事项列表。
- 管理员展示按用户分组待处理表格。
- 普通用户不显示 by-user 表格。
- 页面 loading / error / empty 状态完整。
- 如果 i18n 已合并，新增三语言 dashboard 文案并全部走翻译。

## 测试责任

你必须创建或更新：

- `frontend/tests/finance/dashboard/index.spec.ts`

你必须执行：

- `docker compose exec frontend bun run build`
- `docker compose exec frontend bun run test -- tests/finance/dashboard/index.spec.ts --reporter=line`

如果 Playwright 因环境限制无法执行，必须在 frontend report 中记录真实命令、真实输出和阻塞原因，不得写成通过。

## 交付报告

输出到：

- `docs/rounds/round-007/frontend-report.md`

报告必须包含：

- 输入物路径
- 修改文件
- 新增文件
- 新增路由
- 新增导航入口
- 已接入 API
- 已覆盖页面状态
- i18n 接入情况
- 构建结果
- Playwright 结果
- 越界自检
- 未完成项

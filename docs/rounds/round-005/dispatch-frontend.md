# 前端 AI 派单 - Round 005 invoice_matching

你负责单工具前端任务：`finance / invoice_matching`。

## 必须先读取

1. `skills/members/前端skill.md`
2. `skills/tool-module-builder/SKILL.md`
3. `docs/rounds/round-005/requirements.md`
4. `docs/rounds/round-005/design.md`
5. `docs/rounds/round-005/test-plan.md`
6. `docs/rounds/round-005/tasks.md`
7. `frontend/src/tools/README.md`
8. `frontend/src/config/tool-navigation.tsx`
9. `frontend/src/tools/registry.ts`
10. `frontend/src/tools/finance/purchase_records/`
11. `frontend/src/tools/finance/invoice_files/`
12. `frontend/src/i18n/`

## 任务范围

实现发票匹配前端工具：

- 工具目录：`frontend/src/tools/finance/invoice_matching/`
- 路由：`frontend/src/routes/_layout/finance.invoice-matching.tsx`
- 页面路径：`/finance/invoice-matching`
- 测试目录：`frontend/tests/finance/invoice_matching/`

## 允许修改

- `frontend/src/tools/finance/invoice_matching/**`
- `frontend/src/routes/_layout/finance.invoice-matching.tsx`
- `frontend/src/config/tool-navigation.tsx`
- `frontend/src/routeTree.gen.ts`
- `frontend/src/i18n/**`
- `frontend/tests/finance/invoice_matching/**`
- `docs/rounds/round-005/frontend-report.md`

如现有 i18n 结构未合并或路径不同，必须先说明并按当前结构最小兼容。

## 禁止修改

- `backend/**`
- `skills/**`
- 无关前端工具目录
- 与发票匹配无关的业务逻辑

## 必须实现

- 财务工具组下 `发票匹配` 导航入口。
- 待匹配视图。
- 已匹配视图。
- 需复核视图。
- 异常视图。
- 候选评分展示。
- 评分解释展示。
- 发票已分摊金额/剩余金额展示。
- 逐条确认匹配。
- 取消匹配。
- 重新确认 `needs_review`。
- 管理员可查看所有匹配，但不显示代确认/取消/重新确认按钮。
- 使用 i18n 翻译文案，不新增独立 i18n 系统。

## 测试责任

你必须创建或更新：

- `frontend/tests/finance/invoice_matching/index.spec.ts`

你必须执行：

- `docker compose exec frontend bun run build`
- `docker compose exec frontend bun run test -- tests/finance/invoice_matching/index.spec.ts --reporter=line`

如果 Playwright 因环境问题无法执行，必须在 frontend report 中记录真实命令、真实输出和阻塞原因，不得写成通过。

## 交付报告

输出到：

- `docs/rounds/round-005/frontend-report.md`

报告必须包含：

- 输入物路径
- 修改文件
- 新增文件
- 新增页面/路由
- 新增 API 调用
- i18n 接入说明
- 新增测试
- 构建结果
- Playwright 结果
- 前端越界自检结果
- 未完成项


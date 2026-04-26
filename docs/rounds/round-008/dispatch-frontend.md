# 前端 AI 派单 - Round 008 reimbursement_excel

你负责单工具前端任务：`finance / reimbursement_exports`。

## 必须先读取

1. `skills/members/前端skill.md`
2. `docs/rounds/round-008/requirements.md`
3. `docs/rounds/round-008/design.md`
4. `docs/rounds/round-008/test-plan.md`
5. `docs/rounds/round-008/tasks.md`
6. `frontend/src/config/tool-navigation.tsx`
7. `frontend/src/tools/registry.ts`
8. `frontend/src/tools/finance/purchase_records/`
9. `frontend/src/tools/finance/invoice_files/`
10. `frontend/src/i18n/`，如果 Round 003 已合并

## 任务范围

实现报销 Excel 导出前端工具：

- 工具目录：`frontend/src/tools/finance/reimbursement_exports/`
- 路由：`frontend/src/routes/_layout/finance.reimbursement-exports.tsx`
- 测试目录：`frontend/tests/finance/reimbursement_exports/`

## 允许修改

- `frontend/src/tools/finance/reimbursement_exports/**`
- `frontend/src/routes/_layout/finance.reimbursement-exports.tsx`
- `frontend/src/config/tool-navigation.tsx`
- `frontend/src/routeTree.gen.ts`
- `frontend/src/i18n/**`，仅限新增 reimbursement_exports 文案
- `frontend/tests/finance/reimbursement_exports/**`
- `docs/rounds/round-008/frontend-report.md`

## 禁止修改

- `backend/**`
- `skills/**`
- 购买记录、发票文件、发票匹配现有业务逻辑
- 签字功能
- PDF 生成功能
- Round 003 i18n 未完成部分，除非只是新增本工具字典

## 必须实现

- 注册 `finance / reimbursement_exports` 工具。
- 新增 `/finance/reimbursement-exports` 路由。
- 购买记录筛选。
- 手动勾选表格。
- 已导出记录警告。
- 多币种选中提示。
- 生成配置弹窗：
  - 报销部门
  - 事业部
  - 报销人
  - 日期
- 生成成功后下载入口。
- 导出历史表。
- 过期文件状态显示。
- 设置弹窗：
  - 导出文件保留天数
  - 1 到 365 校验
- 普通用户无生成入口或显示无权限状态。
- 如果 i18n 已合并，新增三语言字典并全部走翻译。

## 测试责任

你必须创建或更新：

- `frontend/tests/finance/reimbursement_exports/index.spec.ts`

你必须执行：

- `docker compose exec frontend bun run build`
- `docker compose exec frontend bun run test -- tests/finance/reimbursement_exports/index.spec.ts --reporter=line`

如果 Playwright 因环境限制无法执行，必须在 frontend report 中记录真实命令、真实输出和阻塞原因，不得写成通过。

## 交付报告

输出到：

- `docs/rounds/round-008/frontend-report.md`

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

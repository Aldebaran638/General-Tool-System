# 前端 AI 派单 - Round 002 invoice_files

你负责单工具前端任务：`finance / invoice_files`。

## 必须先读取

1. `skills/members/前端skill.md`
2. `skills/tool-module-builder/SKILL.md`
3. `docs/rounds/round-002/requirements.md`
4. `docs/rounds/round-002/design.md`
5. `docs/rounds/round-002/test-plan.md`
6. `docs/rounds/round-002/tasks.md`
7. `frontend/src/tools/README.md`
8. `frontend/src/tools/finance/purchase_records/`
9. `frontend/src/routes/_layout/finance.purchase-records.tsx`
10. `frontend/tests/finance/purchase_records/index.spec.ts`

## 任务范围

实现发票文件前端工具：

- 工具目录：`frontend/src/tools/finance/invoice_files/`
- 路由：`frontend/src/routes/_layout/finance.invoice-files.tsx`
- 页面路径：`/finance/invoice-files`
- 测试目录：`frontend/tests/finance/invoice_files/`

## 允许修改

- `frontend/src/tools/finance/invoice_files/**`
- `frontend/src/routes/_layout/finance.invoice-files.tsx`
- `frontend/src/config/tool-navigation.tsx`
- `frontend/tests/finance/invoice_files/**`
- `docs/rounds/round-002/frontend-report.md`

如果现有导航注册文件路径不同，可修改实际导航注册文件，但必须在报告中说明。

## 禁止修改

- `backend/**`
- `skills/**`
- 无关前端工具目录
- 无关全局布局和认证逻辑

## 必须实现

- 财务工具组下 `发票文件` 导航入口。
- 发票文件列表。
- 已删除发票列表。
- 新建/编辑发票表单。
- PDF 上传。
- PDF parse preview，并把结果预填到表单；失败时允许手填。
- 发票类型选择，使用稳定 code：
  - `general_invoice`
  - `vat_special_invoice`
  - `toll_invoice`
  - `other`
- 常见 ISO 4217 币种选择。
- Decimal 金额输入。
- 保存草稿。
- 确认。
- 撤回确认。
- 作废。
- 恢复草稿。
- 逻辑删除。
- 恢复删除。
- 管理员重复提示。
- 普通用户不显示跨用户重复信息。
- PDF 预览/下载必须通过带 Authorization header 的 fetch 获取 blob，不能把 token 拼 URL。

## 测试责任

你必须创建或更新：

- `frontend/tests/finance/invoice_files/index.spec.ts`

你必须执行：

- `docker compose exec frontend bun run build`
- `docker compose exec frontend bun run test -- tests/finance/invoice_files/index.spec.ts --reporter=line`

如果 Playwright 因环境问题无法执行，必须在 frontend report 中记录真实命令、真实输出和阻塞原因，不得写成通过。

## 交付报告

输出到：

- `docs/rounds/round-002/frontend-report.md`

报告必须包含：

- 输入物路径
- 目标工具路径
- 修改文件
- 新增文件
- 新增页面/路由
- 新增 API 调用
- 新增测试
- 构建结果
- Playwright 结果
- 前端越界自检结果
- 联调已验证项
- 联调未验证项及原因
- 未完成项


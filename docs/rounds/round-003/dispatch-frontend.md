# 前端 AI 派单 - Round 003 frontend_i18n

你负责全局前端任务：语言切换基础设施。

## 必须先读取

1. `skills/members/前端skill.md`
2. `docs/rounds/round-003/requirements.md`
3. `docs/rounds/round-003/design.md`
4. `docs/rounds/round-003/test-plan.md`
5. `docs/rounds/round-003/tasks.md`
6. `docs/invoice-system-todo.md`
7. `frontend/src/config/tool-navigation.tsx`
8. `frontend/src/tools/registry.ts`
9. `frontend/src/routes/_layout/settings.tsx`
10. `frontend/src/routes/_layout/admin.tsx`
11. `frontend/src/components/Sidebar/`
12. `frontend/src/components/Admin/`
13. `frontend/src/tools/finance/purchase_records/`
14. `frontend/src/tools/finance/invoice_files/`

## 任务范围

实现前端三语言切换：

- `zh-CN`：简体中文
- `en-US`：英文
- `zh-TW`：繁体中文

第一版只做前端 UI 多语言，语言偏好保存在 localStorage。

## 允许修改

- `frontend/src/i18n/**`
- `frontend/src/main.tsx`
- `frontend/src/routes/**`
- `frontend/src/components/Sidebar/**`
- `frontend/src/components/Admin/**`
- `frontend/src/components/Common/**`
- `frontend/src/config/tool-navigation.tsx`
- `frontend/src/tools/registry.ts`
- `frontend/src/tools/finance/purchase_records/**`
- `frontend/src/tools/finance/invoice_files/**`
- `frontend/tests/i18n/**`
- 现有相关前端测试中因文案变化需要同步的文件
- `docs/rounds/round-003/frontend-report.md`

## 禁止修改

- `backend/**`
- `skills/**`
- 数据库 migration
- API payload 的业务 code
- 与语言切换无关的业务逻辑

## 必须实现

- i18n provider。
- `useI18n()` hook 或等价 API。
- 三语言字典。
- localStorage key：`app_locale`。
- 语言切换入口，优先放在个人设置页。
- 切换语言后立即刷新当前 UI 文案。
- 刷新页面后保持语言。
- 导航、工具组、用户管理、购买记录、发票文件核心文案改为走翻译。
- 购买记录大类/小类显示走翻译。
- 发票类型显示走翻译。
- 状态、按钮、空状态、常见错误提示走翻译。

## 测试责任

你必须创建或更新：

- `frontend/tests/i18n/index.spec.ts`

你必须执行：

- `docker compose exec frontend bun run build`
- `docker compose exec frontend bun run test -- tests/i18n/index.spec.ts --reporter=line`

如果 Playwright 因环境限制无法执行，必须在 frontend report 中记录真实命令、真实输出和阻塞原因，不得写成通过。

## 交付报告

输出到：

- `docs/rounds/round-003/frontend-report.md`

报告必须包含：

- 输入物路径
- 修改文件
- 新增文件
- 新增 i18n 结构
- 已覆盖语言
- 已改造页面/组件
- 未改造页面/组件及原因
- 构建结果
- Playwright 结果
- 越界自检结果
- 未完成项


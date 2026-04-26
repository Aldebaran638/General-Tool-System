# Round 007 Tasks - finance_dashboard

## BE

- 创建 `backend/app/modules/finance/dashboard/`。
- 实现模块自注册。
- 实现 summary / pending / by-user API。
- 复用 Round 005 匹配金额计算逻辑。
- 实现 owner-only / admin-all 权限规则。
- 新增 `backend/tests/finance/dashboard/index_test.py`。
- 执行后端测试与迁移状态检查。
- 输出 `docs/rounds/round-007/backend-report.md`。

## FE

- 创建 `frontend/src/tools/finance/dashboard/`。
- 注册财务工具组导航入口。
- 新增 `/finance/dashboard` 路由。
- 实现统计卡片、待处理列表、管理员按用户分组表。
- 接入 i18n，或在 Round 003 未合并时记录阻塞。
- 新增 `frontend/tests/finance/dashboard/index.spec.ts`。
- 执行前端构建和 Playwright 测试。
- 输出 `docs/rounds/round-007/frontend-report.md`。

## INT

- 确认普通用户只能看到自己的统计。
- 确认管理员看到全局统计。
- 确认财务工具组下显示统计入口。
- 确认统计页不依赖签字功能。
- 确认 Round 005 未合并时不会虚构匹配数据。

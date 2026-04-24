# 前端 AI 派单 - Round 001 purchase_records

你负责单工具前端任务：`finance / purchase_records`。

## 必须先读取

1. `skills/members/前端skill.md`
2. `skills/tool-frontend-builder/SKILL.md`
3. `docs/rounds/round-001/requirements.md`
4. `docs/rounds/round-001/design.md`
5. `docs/rounds/round-001/test-plan.md`
6. `docs/rounds/round-001/tasks.md`
7. `frontend/src/tools/README.md`
8. `frontend/src/config/tool-navigation.tsx`
9. `frontend/src/components/Sidebar/Main.tsx`
10. `frontend/tests/workbench/project_management/index.spec.ts`

## 任务范围

实现购买记录前端工具：

- 路由：`/finance/purchase-records`
- 工具目录：`frontend/src/tools/finance/purchase_records/`
- 测试目录：`frontend/tests/finance/purchase_records/`
- 导航：财务 -> 购买记录

## 允许修改

- `frontend/src/tools/finance/purchase_records/**`
- `frontend/src/routes/_layout/finance.purchase-records.tsx`
- `frontend/src/config/tool-navigation.tsx`
- `frontend/tests/finance/purchase_records/**`
- `docs/rounds/round-001/frontend-report.md`

## 禁止修改

- `backend/**`
- `skills/**`
- 无关工具目录
- 无关全局布局和全局样式
- 手工修改 `frontend/src/routeTree.gen.ts`

## 必须实现

- 财务工具组下购买记录入口。
- 购买记录列表。
- 正常记录 / 已删除记录筛选。
- 购买记录表单。
- 截图上传。
- OCR preview 调用与表单预填。
- OCR 失败后允许手填。
- 大类/小类联动校验。
- 币种选择。
- 保存草稿。
- 提交。
- 撤回提交。
- 编辑草稿和驳回记录。
- 删除。
- 恢复。
- 管理员批准、驳回、撤回批准。
- 截图预览或下载入口。

## 测试责任

你必须创建或更新：

- `frontend/tests/finance/purchase_records/index.spec.ts`

你必须执行：

- `docker compose exec frontend bun run build`
- `docker compose exec frontend bun run test -- tests/finance/purchase_records/index.spec.ts --reporter=line`

如果测试因后端未完成而无法通过，必须在 frontend report 中写明阻塞点和已完成的前端验证。

## 交付报告

输出到：

- `docs/rounds/round-001/frontend-report.md`

报告必须包含：

- 输入物路径
- 修改文件
- 新增文件
- 新增路由
- 导航注册
- 调用 API 列表
- 新增测试
- 构建结果
- Playwright 结果
- 前端越界自检结果
- 联调已验证项
- 联调未验证项及原因
- 未完成项

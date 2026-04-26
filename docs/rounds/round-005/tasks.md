# Round 005 Tasks - invoice_matching

## 后端任务

- 创建 `backend/app/modules/finance/invoice_matching/`。
- 创建 `invoice_match` SQLModel 模型。
- 新增 Alembic migration。
- 模块自注册。
- 实现候选评分服务。
- 实现发票分摊金额计算。
- 实现匹配确认、取消、重新确认。
- 实现 `needs_review` 标记服务。
- 接入购买记录、发票关键字段变化后的复核标记。
- 实现权限规则。
- 创建后端测试。
- 更新后端报告。

## 前端任务

- 创建 `frontend/src/tools/finance/invoice_matching/`。
- 创建路由 `frontend/src/routes/_layout/finance.invoice-matching.tsx`。
- 注册财务工具组导航。
- 实现待匹配、已匹配、需复核、异常视图。
- 实现候选列表和评分解释。
- 实现发票已分摊金额/剩余金额展示。
- 实现逐条确认、取消、重新确认。
- 管理员视图只读，不显示代确认操作。
- 接入 i18n。
- 创建前端测试。
- 更新前端报告。

## 架构师验收

- 审查后端报告与代码。
- 审查前端报告与代码。
- 复跑核心测试。
- 执行联调。
- 生成 integration report。


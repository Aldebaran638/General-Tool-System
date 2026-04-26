# 后端 AI 派单 - Round 005 invoice_matching

你负责单工具后端任务：`finance / invoice_matching`。

## 必须先读取

1. `skills/members/后端skill.md`
2. `skills/tool-module-builder/SKILL.md`
3. `docs/rounds/round-005/requirements.md`
4. `docs/rounds/round-005/design.md`
5. `docs/rounds/round-005/test-plan.md`
6. `docs/rounds/round-005/tasks.md`
7. `backend/app/MODULE_ARCHITECTURE.md`
8. `backend/app/modules/README.md`
9. `backend/app/modules/finance/purchase_records/`
10. `backend/app/modules/finance/invoice_files/`
11. `backend/tests/finance/purchase_records/index_test.py`
12. `backend/tests/finance/invoice_files/index_test.py`

## 任务范围

实现发票匹配后端模块：

- 模块目录：`backend/app/modules/finance/invoice_matching/`
- 测试目录：`backend/tests/finance/invoice_matching/`
- API 前缀：`/api/v1/finance/invoice-matching`

## 允许修改

- `backend/app/modules/finance/invoice_matching/**`
- `backend/app/modules/finance/purchase_records/**`
- `backend/app/modules/finance/invoice_files/**`
- `backend/app/alembic/versions/**`
- `backend/tests/finance/invoice_matching/**`
- `backend/tests/finance/purchase_records/**`
- `backend/tests/finance/invoice_files/**`
- `docs/rounds/round-005/backend-report.md`

仅当测试隔离需要且 Round 004 尚未合并时，可协调修改测试配置；否则不要改测试基础设施。

## 禁止修改

- `frontend/**`
- `skills/**`
- `.env`
- 无关后端模块
- `backend/app/api/routes/**` 中新增业务路由
- 业务无关全局逻辑

## 必须实现

- `invoice_match` SQLModel 模型。
- Alembic migration。
- 模块自注册。
- 候选实时计算接口，不落库候选。
- confirmed/cancelled/needs_review 匹配关系持久化。
- 一条购买记录最多一个 active 匹配。
- 一张发票允许多个 active 匹配。
- 发票 allocated_amount / remaining_amount 计算。
- 超额确认拦截。
- 金额误差 `<= 0.01` 规则。
- 日期 7 天候选规则。
- 普通用户 owner-only 确认、取消、重新确认。
- 管理员只读所有匹配，不能代确认/取消/重新确认。
- 关键字段变化标记 `needs_review`。
- 发票作废后匹配进入 `needs_review`。
- 逻辑删除后普通列表隐藏相关匹配。

## 测试责任

你必须创建或更新：

- `backend/tests/finance/invoice_matching/index_test.py`

你必须执行：

- `docker compose exec backend pytest tests/finance/invoice_matching/index_test.py -q`
- `docker compose exec backend alembic upgrade head`
- `docker compose exec backend alembic current`

如果 Round 004 测试隔离未完成，不得用会污染开发库的方式运行大量测试；必须在报告中说明阻塞。

## 交付报告

输出到：

- `docs/rounds/round-005/backend-report.md`

报告必须包含：

- 输入物路径
- 目标模块路径
- 修改文件
- 新增文件
- 新增 API
- 新增模型
- 新增 migration
- 新增测试
- 后端测试结果
- 迁移校验结果
- 权限自检
- 越界自检
- 未完成项


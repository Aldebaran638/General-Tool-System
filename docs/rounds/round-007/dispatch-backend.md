# 后端 AI 派单 - Round 007 finance_dashboard

你负责单工具后端任务：`finance / dashboard`。

## 必须先读取

1. `skills/members/后端skill.md`
2. `skills/tool-module-builder/SKILL.md`
3. `docs/rounds/round-007/requirements.md`
4. `docs/rounds/round-007/design.md`
5. `docs/rounds/round-007/test-plan.md`
6. `docs/rounds/round-007/tasks.md`
7. `backend/app/MODULE_ARCHITECTURE.md`
8. `backend/app/modules/README.md`
9. `backend/app/modules/finance/purchase_records/`
10. `backend/app/modules/finance/invoice_files/`
11. `backend/app/modules/finance/invoice_matching/`
12. `backend/tests/finance/purchase_records/index_test.py`
13. `backend/tests/finance/invoice_files/index_test.py`
14. `backend/tests/finance/invoice_matching/index_test.py`

## 任务范围

实现财务统计后端模块：

- 模块目录：`backend/app/modules/finance/dashboard/`
- 测试目录：`backend/tests/finance/dashboard/`
- API 前缀：`/api/v1/finance/dashboard`

## 允许修改

- `backend/app/modules/finance/dashboard/**`
- `backend/app/modules/finance/invoice_matching/**`，仅限提取可复用统计/金额 helper
- `backend/tests/finance/dashboard/**`
- `backend/tests/finance/invoice_matching/**`，仅限 helper 调整带来的测试修正
- `docs/rounds/round-007/backend-report.md`

## 禁止修改

- `frontend/**`
- `skills/**`
- `.env`
- `backend/app/api/routes/**` 中新增业务路由
- 购买记录和发票文件核心业务逻辑
- 用户角色体系
- 签字相关功能
- 数据库 migration，除非确有必要；本轮默认不新增表

## 必须实现

- 模块自注册。
- `GET /summary`。
- `GET /pending`。
- `GET /by-user`，管理员专用。
- 普通用户 owner-only 统计。
- 管理员全局统计。
- 购买记录 total / unmatched / matched / deleted。
- 发票 total / unallocated / partially_allocated / fully_allocated / voided。
- 匹配 confirmed / needs_review / cancelled。
- pending 列表最多 20 条默认，支持 limit 最大 100。
- by-user 按用户聚合 pending 数量。
- 不在 dashboard 中复制 Round 005 的金额分配规则，应复用 helper。

## 测试责任

你必须创建或更新：

- `backend/tests/finance/dashboard/index_test.py`

你必须执行：

- `docker compose exec backend pytest tests/finance/dashboard/index_test.py -q`
- `docker compose exec backend pytest tests/finance/invoice_matching/index_test.py -q`
- `docker compose exec backend alembic current`

如果 Round 005 后端尚未合并，不得硬编码假匹配数据；必须在报告中说明阻塞。

## 交付报告

输出到：

- `docs/rounds/round-007/backend-report.md`

报告必须包含：

- 输入物路径
- 目标模块路径
- 修改文件
- 新增文件
- 新增 API
- 统计口径说明
- 权限规则说明
- 新增测试
- 后端测试结果
- 迁移状态检查结果
- 越界自检
- 未完成项

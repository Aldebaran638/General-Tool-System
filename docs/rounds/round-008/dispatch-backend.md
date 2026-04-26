# 后端 AI 派单 - Round 008 reimbursement_excel

你负责单工具后端任务：`finance / reimbursement_exports`。

## 必须先读取

1. `skills/members/后端skill.md`
2. `skills/tool-module-builder/SKILL.md`
3. `docs/rounds/round-008/requirements.md`
4. `docs/rounds/round-008/design.md`
5. `docs/rounds/round-008/test-plan.md`
6. `docs/rounds/round-008/tasks.md`
7. `docs/報銷表模板最新.xlsx`
8. `docs/202512_signed.pdf`
9. `backend/app/MODULE_ARCHITECTURE.md`
10. `backend/app/modules/README.md`
11. `backend/app/modules/finance/purchase_records/`
12. `backend/app/modules/finance/invoice_files/`
13. `backend/app/modules/finance/invoice_matching/`
14. `backend/tests/finance/invoice_matching/index_test.py`

## 任务范围

实现报销 Excel 导出后端模块：

- 模块目录：`backend/app/modules/finance/reimbursement_exports/`
- 测试目录：`backend/tests/finance/reimbursement_exports/`
- API 前缀：`/api/v1/finance/reimbursement-exports`
- 模板：`docs/報銷表模板最新.xlsx`
- 文件目录：`runtime_data/exports/finance/reimbursement/`

## 允许修改

- `backend/app/modules/finance/reimbursement_exports/**`
- `backend/app/alembic/versions/**`
- `backend/tests/finance/reimbursement_exports/**`
- `backend/app/models_core.py` 或合适的平台模型文件，仅限新增 `AppSetting`
- `backend/app/models.py`，仅限 re-export 新增平台模型
- `backend/tests/conftest.py`，仅限新增测试表清理依赖
- `backend/pyproject.toml`
- `uv.lock`
- `docs/rounds/round-008/backend-report.md`

## 禁止修改

- `frontend/**`
- `skills/**`
- `.env`
- Round 003/005/006/007 文档
- 购买记录、发票文件、发票匹配核心业务逻辑，除非只为读取必要数据或修复 import
- 签字功能
- PDF 生成功能

## 必须实现

- `app_setting` SQLModel 模型。
- `reimbursement_export` SQLModel 模型。
- `reimbursement_export_item` SQLModel 模型。
- Alembic migration。
- 模块自注册。
- `GET /records`。
- `POST /generate`。
- `GET /history`。
- `GET /{id}`。
- `GET /{id}/download`。
- `GET /settings`。
- `PUT /settings`。
- `POST /purge-expired-files`。
- 管理员专用权限。
- 普通用户 403。
- 购买记录筛选。
- 手选记录生成。
- 多用户允许。
- 多币种禁止。
- 已导出允许重复导出。
- 导出历史永久保留。
- 物理 Excel 文件保存到本地文件系统。
- 过期文件清理只删除物理文件。
- 过期文件下载返回 410。
- 单据编号按类别顺序和组内升序生成。
- 明细页每条购买记录一行。
- 分类页其他项目费用按小类汇总。
- 数据库不保存 Excel 二进制。

## 测试责任

你必须创建或更新：

- `backend/tests/finance/reimbursement_exports/index_test.py`

你必须执行：

- `docker compose exec backend pytest tests/finance/reimbursement_exports/index_test.py -q`
- `docker compose exec backend pytest tests/finance/invoice_matching/index_test.py -q`
- `docker compose exec backend alembic upgrade head`
- `docker compose exec backend alembic current`

如果 Round 005 后端尚未合并，不得硬编码假匹配数据；必须在报告中说明阻塞。

## 交付报告

输出到：

- `docs/rounds/round-008/backend-report.md`

报告必须包含：

- 输入物路径
- 模板分析结果
- 目标模块路径
- 修改文件
- 新增文件
- 新增 API
- 新增模型
- 新增 migration
- Excel 生成规则
- 单据编号规则
- 文件存储规则
- 设置项规则
- 新增测试
- 后端测试结果
- 迁移校验结果
- 权限自检
- 越界自检
- 未完成项

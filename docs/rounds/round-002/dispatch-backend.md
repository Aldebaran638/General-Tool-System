# 后端 AI 派单 - Round 002 invoice_files

你负责单工具后端任务：`finance / invoice_files`。

## 必须先读取

1. `skills/members/后端skill.md`
2. `skills/tool-module-builder/SKILL.md`
3. `docs/rounds/round-002/requirements.md`
4. `docs/rounds/round-002/design.md`
5. `docs/rounds/round-002/test-plan.md`
6. `docs/rounds/round-002/tasks.md`
7. `backend/app/MODULE_ARCHITECTURE.md`
8. `backend/app/modules/README.md`
9. `backend/app/modules/finance/purchase_records/`
10. `backend/tests/finance/purchase_records/index_test.py`

## 任务范围

实现发票文件后端模块：

- 模块目录：`backend/app/modules/finance/invoice_files/`
- 测试目录：`backend/tests/finance/invoice_files/`
- API 前缀：`/api/v1/finance/invoice-files`
- 文件目录：`runtime_data/uploads/finance/invoice_files/`

## 允许修改

- `backend/app/modules/finance/invoice_files/**`
- `backend/app/alembic/versions/**`
- `backend/tests/finance/invoice_files/**`
- `backend/pyproject.toml`
- `uv.lock`
- `docs/rounds/round-002/backend-report.md`

如 PDF/OCR 依赖或配置确实必须调整，允许修改：

- `.env-example`
- `backend/app/core/config.py`

但必须在报告中单独说明原因。

## 禁止修改

- `frontend/**`
- `skills/**`
- 无关后端模块
- 无关全局业务逻辑
- `backend/app/api/routes/**` 中新增业务路由
- `.env`

## 必须实现

- `invoice_file` SQLModel 模型。
- Alembic migration。
- 模块自注册。
- PDF 本地存储 `storage.py`。
- PDF parse preview，优先本地文本提取，必要时本地 OCR，失败降级为空 preview。
- parse preview 不落库，不持久化 PDF。
- CRUD API。
- 状态流转 API：
  - `draft -> confirmed`
  - `confirmed -> draft`
  - `confirmed -> voided`
  - `voided -> draft`
- 逻辑删除与恢复。
- 30 天前删除记录清理接口。
- PDF 鉴权下载接口。
- 权限规则。
- 发票类型校验。
- 币种校验。
- Decimal 金额校验。
- 日期校验，非法日期返回 422。
- 同一用户未删除发票号码唯一。
- 跨用户重复发票提示，普通用户不得泄露跨用户信息。
- OCR/parse preview 必须受全局 AI/OCR 配置控制。
- 数据库不保存 PDF 二进制。

## 测试责任

你必须创建或更新：

- `backend/tests/finance/invoice_files/index_test.py`

你必须执行：

- `docker compose exec backend pytest tests/finance/invoice_files/index_test.py`
- `docker compose exec backend alembic upgrade head`
- `docker compose exec backend alembic current`

如果 PDF/OCR 依赖安装或运行受限，不能阻塞正式发票创建流程；必须在 backend report 中写明降级行为和后续处理建议。

## 交付报告

输出到：

- `docs/rounds/round-002/backend-report.md`

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
- API 契约测试结果
- 迁移校验结果
- 后端越界自检结果
- 联调已验证项
- 联调未验证项及原因
- 未完成项


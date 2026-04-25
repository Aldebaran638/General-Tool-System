# 后端 AI 派单 - Round 001 purchase_records

你负责单工具后端任务：`finance / purchase_records`。

## 必须先读取

1. `skills/members/后端skill.md`
2. `skills/tool-module-builder/SKILL.md`
3. `docs/rounds/round-001/requirements.md`
4. `docs/rounds/round-001/design.md`
5. `docs/rounds/round-001/test-plan.md`
6. `docs/rounds/round-001/tasks.md`
7. `backend/app/MODULE_ARCHITECTURE.md`
8. `backend/app/modules/README.md`
9. `backend/app/modules/workbench/project_management/`
10. `backend/tests/workbench/project_management/index_test.py`

## 任务范围

实现购买记录后端模块：

- 模块目录：`backend/app/modules/finance/purchase_records/`
- 测试目录：`backend/tests/finance/purchase_records/`
- API 前缀：`/api/v1/finance/purchase-records`
- 文件目录：`runtime_data/uploads/finance/purchase_records/`

## 允许修改

- `backend/app/modules/finance/purchase_records/**`
- `backend/app/alembic/versions/**`
- `backend/tests/finance/purchase_records/**`
- `.env`
- `.env-example`
- `backend/app/core/config.py`
- `backend/pyproject.toml`
- `uv.lock`
- `docs/rounds/round-001/backend-report.md`

## 禁止修改

- `frontend/**`
- `skills/**`
- 无关后端模块
- 无关全局业务逻辑
- `backend/app/api/routes/**` 中新增业务路由

## 必须实现

- `purchase_record` SQLModel 模型。
- Alembic migration。
- 模块自注册。
- 文件存储 `storage.py`。
- OCR preview `ocr.py`，使用 PaddleOCR 本地预训练模型或清晰降级实现。
- 全局 AI/OCR 配置：`ENABLE_LLM`、`ENABLE_LOCAL_OCR`、`OCR_PROVIDER`、`OCR_MODEL_DIR`、`OCR_ALLOW_MODEL_DOWNLOAD`。
- CRUD API。
- 状态流转 API。
- 逻辑删除与恢复。
- 30 天前删除记录清理接口。
- 截图鉴权下载接口。
- 权限规则。
- 大类/小类校验。
- OCR preview 不落库。
- OCR preview 必须受全局 AI/OCR 配置控制。
- 数据库不保存截图二进制。

## 测试责任

你必须创建或更新：

- `backend/tests/finance/purchase_records/index_test.py`

你必须执行：

- `docker compose exec backend pytest tests/finance/purchase_records/index_test.py`
- `docker compose exec backend alembic upgrade head`
- `docker compose exec backend alembic current`

如果 PaddleOCR 依赖安装或运行受限，不能阻塞正式购买记录创建流程；必须在 backend report 中写明降级行为和后续处理建议。

## 交付报告

输出到：

- `docs/rounds/round-001/backend-report.md`

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

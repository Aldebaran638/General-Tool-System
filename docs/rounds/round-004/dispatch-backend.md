# 后端 AI 派单 - Round 004 backend_test_isolation

你负责后端基础设施任务：pytest 测试环境隔离。

## 必须先读取

1. `skills/members/后端skill.md`
2. `docs/rounds/round-004/requirements.md`
3. `docs/rounds/round-004/design.md`
4. `docs/rounds/round-004/test-plan.md`
5. `docs/rounds/round-004/tasks.md`
6. `backend/tests/conftest.py`
7. `backend/tests/utils/user.py`
8. `backend/tests/utils/utils.py`
9. `backend/app/core/config.py`
10. `.env-example`
11. `compose.yml`

## 任务范围

实现后端 pytest 与开发数据库隔离。

## 允许修改

- `backend/tests/**`
- `backend/app/core/config.py`
- `.env-example`
- `backend/pyproject.toml`
- `uv.lock`
- `docs/rounds/round-004/backend-report.md`

如果必须修改 `compose.yml` 或 `compose.override.yml` 才能实现测试库隔离，允许修改，但必须在报告中说明原因和影响。

## 禁止修改

- `.env`
- `frontend/**`
- `skills/**`
- 业务模块代码，除非只是为了测试隔离必须调整 import 或配置读取
- 数据库 migration
- 当前开发库里的真实数据

## 必须实现

- pytest 使用独立测试数据库。
- 默认测试数据库名建议为 `app_test`。
- 增加 `POSTGRES_TEST_DB` 示例配置。
- 增加 `TESTING` 或等价测试模式标记。
- pytest 启动时必须确认当前数据库是测试库。
- 如果测试数据库名不包含 `test`，必须快速失败。
- 测试 fixture 不得清理开发库。
- 测试运行后不得新增开发库用户。
- backend report 必须说明当前历史垃圾用户不会在本轮自动删除。

## 必须验证

执行：

- `docker compose exec backend pytest tests/finance/invoice_files/index_test.py -q`
- `docker compose exec backend pytest tests/finance/purchase_records/index_test.py -q`
- `docker compose exec backend pytest tests/api/routes/test_users.py -q`

并记录：

- 测试使用的数据库名
- 测试前开发库用户数量
- 测试后开发库用户数量
- 失败或未执行项原因

## 交付报告

输出到：

- `docs/rounds/round-004/backend-report.md`

报告必须包含：

- 输入物路径
- 修改文件
- 新增配置
- 测试数据库隔离方案
- 安全护栏
- 执行命令与结果
- 开发库用户数量前后对比
- 越界自检
- 未完成项


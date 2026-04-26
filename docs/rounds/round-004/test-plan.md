# Round 004 Test Plan - backend_test_isolation

## 必须执行

- `docker compose exec backend pytest tests/finance/invoice_files/index_test.py -q`
- `docker compose exec backend pytest tests/finance/purchase_records/index_test.py -q`
- `docker compose exec backend pytest tests/api/routes/test_users.py -q`

如耗时允许，再执行：

- `docker compose exec backend pytest -q`

## 必须验证

- pytest 输出或报告中能看到当前测试数据库名。
- 测试数据库名不是开发库名。
- 测试数据库名包含 `test`。
- 测试运行后，开发库中的用户数量不增加。
- 测试运行后，开发库中 `1941704428@qq.com`、`admin@example.com`、`test@example.com` 不受影响。
- 如果将测试数据库配置成开发库名，测试会快速失败。

## 建议新增测试

新增后端测试或 fixture 自检：

- `test_tests_use_isolated_database`
- `test_testing_database_name_guard`

如果这类测试难以在普通 pytest 内模拟，可以在 backend report 中说明替代验证方式。

## 报告要求

`docs/rounds/round-004/backend-report.md` 必须包含：

- 测试库配置方式
- 修改文件
- 新增配置项
- 安全护栏说明
- 实际执行命令
- 测试前后开发库用户数量对比
- 未清理历史垃圾用户的说明
- 后续建议


# Round 004 Design - backend_test_isolation

## 推荐方案

在 `backend/tests/conftest.py` 最早阶段设置测试数据库环境，然后再导入 app 配置和 engine。

推荐流程：

1. 读取 `.env` 中的数据库连接基础配置。
2. pytest 启动时设置：
   - `TESTING=true`
   - `POSTGRES_DB=POSTGRES_TEST_DB`，默认 `app_test`
3. 确保测试数据库存在。
4. 对测试数据库执行迁移或 `init_db`。
5. 所有测试使用测试数据库 engine。
6. 测试结束后清理测试数据库数据，或直接 drop/recreate 测试数据库。

## 安全护栏

必须实现一个明确检查：

```text
如果 TESTING=true 且 settings.POSTGRES_DB 不包含 "test"，pytest 立即失败。
```

也可以更严格：

```text
如果 settings.POSTGRES_DB == 开发库 POSTGRES_DB，pytest 立即失败。
```

## 允许实现选择

后端 AI 可以选择以下任一方式：

- 每次 pytest session 创建/重建 `app_test` 数据库。
- 使用稳定 `app_test` 数据库，每次测试前清空所有表。
- 使用独立 schema，但必须证明不会影响开发 schema。

优先推荐独立 database，不推荐独立 schema。

## 注意事项

- `app.core.config.settings` 是模块级单例，必须避免在设置测试环境变量之前被导入。
- 如果需要修改 import 顺序，优先修改 `backend/tests/conftest.py`。
- 不要修改 `.env`。
- 可以修改 `.env-example` 增加 `POSTGRES_TEST_DB` 示例。
- 可以修改 `backend/app/core/config.py` 增加 `POSTGRES_TEST_DB`、`TESTING` 配置。

## 历史垃圾用户

本轮不删除历史垃圾用户。可以在报告中给出建议清理命令或脚本草案，但不得自动执行。


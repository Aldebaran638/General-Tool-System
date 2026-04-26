# Round 004 Tasks - backend_test_isolation

## 后端任务

- 增加测试数据库配置。
- 调整 pytest fixture，确保测试连接测试库。
- 增加测试库安全护栏。
- 避免测试 fixture 清理开发库数据。
- 验证 invoice_files、purchase_records、users 测试在测试库运行。
- 更新 `.env-example`，说明 `POSTGRES_TEST_DB`。
- 更新后端报告。

## 禁止事项

- 不得修改 `.env`。
- 不得删除当前开发库里的历史用户。
- 不得修改前端代码。
- 不得改业务功能来绕过测试。

## 架构师验收

- 复查测试库隔离逻辑。
- 复跑核心 pytest。
- 查询开发库用户数量，确认测试后不增加。
- 确认历史垃圾用户没有被本轮误删。


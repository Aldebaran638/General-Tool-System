# Round 004 Backend Report

## 1. 变更摘要

本次变更实现了 pytest 测试环境与开发数据库的完全隔离，并解决了并行 pytest 会话竞争问题：

- 新增独立的测试数据库配置 `POSTGRES_TEST_DB`（默认 `app_test`）。
- 引入 `TESTING` 布尔标志，运行时自动切换数据库 URI。
- 添加安全护栏：若 `TESTING=true`，数据库名称必须包含 `test` 字样。
- `conftest.py` 在测试会话开始前自动创建测试数据库、运行 Alembic 迁移并注入种子数据；会话结束时自动清理测试数据库。
- 采用 **per-PID 独立测试数据库**（`app_test_<pid>`），彻底消除并行 pytest 会话之间的资源竞争。

## 2. 文件变更

### 2.1 修改文件

- `backend/app/core/config.py`
  - 新增 `POSTGRES_TEST_DB: str = "app_test"`。
  - 新增 `TESTING: bool = False`。
  - `SQLALCHEMY_DATABASE_URI` 在 `TESTING=true` 时自动使用 `POSTGRES_TEST_DB`。
  - 新增 `_ensure_test_db_has_test_suffix` 校验器。

- `.env-example`
  - 新增 `POSTGRES_TEST_DB=app_test`。

- `backend/tests/conftest.py`（完全重写）
  - 在 `import` 之前设置 `os.environ["TESTING"] = "true"`。
  - 使用 `os.getpid()` 构造唯一的测试数据库名 `app_test_<pid>`。
  - 新增 `_create_test_db()`：通过 `postgres` 管理库创建测试库。
  - 新增 `_drop_test_db()`：会话结束前终止该库的所有连接并 `DROP DATABASE`。
  - 新增 `_run_migrations()`：通过 Alembic 以 `upgrade head` 初始化 schema。
  - `db` fixture（`session` 级别，`autouse=True`）负责全生命周期。
  - 保留 `client`、`superuser_token_headers`、`normal_user_token_headers` fixtures。

### 2.2 删除文件

- `scripts/write_conftest.py`（临时脚本，已移除，不允许留在仓库中）

## 3. 并行安全策略

### 3.1 问题

当多个 pytest 进程同时运行时，若共享同一个 `app_test` 数据库，会出现以下竞争：

- 一个进程在运行测试时，另一个进程执行 `DROP DATABASE` 导致连接中断。
- 两个进程同时操作同一张表，数据互相污染。

### 3.2 方案

采用 **per-PID 独立测试数据库**：

```python
_test_db_name = f"app_test_{os.getpid()}"
os.environ["POSTGRES_TEST_DB"] = _test_db_name
```

每个 pytest 进程拥有自己独立的数据库实例：

- 创建：`CREATE DATABASE "app_test_12345"`
- 迁移：`alembic upgrade head`
- 种子：`init_db(session)`
- 销毁：`DROP DATABASE "app_test_12345"`

进程之间互不干扰，无需额外的跨进程锁。

### 3.3 连接清理

`_drop_test_db()` 在删除数据库之前，先通过 `pg_terminate_backend(pid)` 强制终止所有指向该测试库的连接（排除当前后端连接），确保 `DROP DATABASE` 不会因为仍有连接而失败。

## 4. 安全护栏

- `TESTING=true` 时，若数据库名称不包含 `test`，`Settings` 初始化会直接抛出 `ValueError`，防止误操作生产/开发数据库。
- `conftest.py` 在模块导入阶段即强制设置 `os.environ["TESTING"] = "true"`，任何测试都无法绕过此开关。
- 所有测试通过 `TestClient` 与 `dependency_overrides` 访问数据库，完全走测试引擎。

## 5. 验证结果

### 5.1 必测套件（单进程）

```bash
docker compose exec backend bash -c "cd /app && pytest tests/finance/invoice_files/index_test.py -q"
```

结果：`54 passed, 2 warnings`

```bash
docker compose exec backend bash -c "cd /app && pytest tests/finance/purchase_records/index_test.py -q"
```

结果：`42 passed, 2 warnings`

```bash
docker compose exec backend bash -c "cd /app && pytest tests/api/routes/test_users.py -q"
```

结果：`27 passed, 1 warning`

### 5.2 并行会话验证

同时启动两个独立的 pytest 进程，分别运行不同的测试套件：

```bash
# 终端 A
docker compose exec backend bash -c "cd /app && pytest tests/finance/invoice_files/index_test.py -q"

# 终端 B
docker compose exec backend bash -c "cd /app && pytest tests/finance/purchase_records/index_test.py -q"
```

结果：两个会话均通过，且互不影响。

### 5.3 开发数据库保护

- 测试前开发库 `app` 用户表记录数：`304`
- 测试后开发库 `app` 用户表记录数：`304`

确认测试全程未对开发数据库执行任何写入。

## 6. 结论

- 测试与开发数据库已完全隔离。
- 并行 pytest 会话安全，无需额外同步机制。
- 三个必测套件全部通过。
- 开发数据库数据零污染。

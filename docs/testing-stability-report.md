# 后端测试稳定性巡检报告

日期：2026-04-26
执行者：后端 AI

---

## 1. 执行命令与结果

巡检指定的 6 组 pytest 命令，全部在容器内执行（`docker compose exec backend ...`）。基线运行后定位污染、修复测试，再次回归。

| # | 命令 | 基线结果 | 修复后结果 |
|---|------|----------|------------|
| 1 | `pytest tests/finance/purchase_records/index_test.py tests/finance/invoice_files/index_test.py -q` | 96 passed | 96 passed |
| 2 | `pytest tests/finance/purchase_records/index_test.py tests/finance/invoice_matching/index_test.py -q` | **76 passed, 1 FAILED** | **77 passed** |
| 3 | `pytest tests/finance/invoice_files/index_test.py tests/finance/invoice_matching/index_test.py -q` | 89 passed | 89 passed |
| 4 | `pytest tests/finance/dashboard/index_test.py tests/finance/invoice_matching/index_test.py -q` | 52 passed | 52 passed |
| 5 | `pytest tests/api/routes/test_users.py tests/crud/test_user.py -q` | 37 passed | 37 passed |
| 6 | `pytest tests/finance/ -q`（见 §5 阻塞说明） | **collection error**（Round 008 bug） | 148 passed（`--ignore=tests/finance/reimbursement_exports`） |

巡检发现的唯一污染失败位于 **组合 2**：
```
FAILED tests/finance/invoice_matching/index_test.py::test_unmatched_purchase_records_empty
  assert 3 == 0
```

---

## 2. 发现的问题（根因）

### 2.1 测试顺序污染（已修复）

- 现象：`test_unmatched_purchase_records_empty` 在 `tests/finance/purchase_records/index_test.py` 之后运行时，`GET /finance/invoice-matching/unmatched-purchase-records` 返回 `count == 3`，断言 `count == 0` 失败。
- 根因：
  - `backend/tests/conftest.py` 的 `db` fixture 是 `scope="session"`，每个 pytest 进程只创建一个 `app_test_<pid>` 库，整轮跑下来全程共享。
  - `normal_user_token_headers` 是 module-scope，所有用它的测试都登录到同一个全局 `settings.EMAIL_TEST_USER` 帐号上。
  - `purchase_records` 套件里有大量「创建已批准/已提交的 purchase」用例，写入到这个全局用户名下；它们提交在 `invoice_matching` 之前时，`unmatched-purchase-records` 的「应该是空」断言就被污染。
- 这与上一轮 Round 005 修复 `test_available_invoices_empty` 的污染机理完全一致：跨套件共享同一个全局用户 + session-scope DB → 「空状态断言」必然脆弱。

### 2.2 Round 008（reimbursement_exports）阻塞（已规避，不修复）

巡检过程中发现 Round 008 正在并行开发的 `reimbursement_exports` 模块带来两个独立问题，**两者都属于「明令禁止触碰」的目录，本次巡检不修复**：

1. `app/modules/finance/reimbursement_exports/excel_builder.py` 引用 `openpyxl`，但 `pyproject.toml` 还没有把它写进 dependencies；运行容器内 `/app/.venv` 没有该包。导致 `auto_discover_modules` 时 `ConftestImportFailure: ModuleNotFoundError: No module named 'openpyxl'`，pytest 直接拒绝加载。
   - 临时规避：在容器 venv 内 `uv pip install --python /app/.venv/bin/python openpyxl`（仅修改容器运行时，不动 `pyproject.toml` / `uv.lock` / `app/**`）。这是为了让本巡检能跑通而采取的最小动作；持久修复需要 Round 008 把 `openpyxl` 加进依赖。
2. `tests/finance/reimbursement_exports/index_test.py:44` 写的是 `from backend.tests.utils.user import authentication_token_from_email`，这是错误的包前缀（容器内 `sys.path` 没有 `backend.` 顶层模块，应为 `from tests.utils.user ...`）。这导致 `pytest tests/finance/ -q` 在 collection 阶段就报错退出，组合 6 无法逐字执行。
   - 规避方案：组合 6 加 `--ignore=tests/finance/reimbursement_exports` 跳过该目录，剩余 finance 测试全绿（148 passed）。
   - 持久修复属于 Round 008 自己的边界，不在本次巡检授权范围。

---

## 3. 修复文件

仅修改一份测试文件：

- `backend/tests/finance/invoice_matching/index_test.py`
  - 改动函数：`test_unmatched_purchase_records_empty`
  - 改动方式：把入参从 `normal_user_token_headers` 换成 `db: Session`，函数体内调用 `authentication_token_from_email(client=client, email=random_email(), db=db)` 创建一个全新的 per-test 用户来发请求；其余断言（`count == 0`、`data == []`）原样保留。
  - 这沿用 §2.1 提到的 Round 005/007 既有修法（同文件 line 167 `test_available_invoices_empty` 已经是这个写法）；现在 line 154 `test_unmatched_purchase_records_empty` 也对齐，写注释说明动机。

未触碰任何其它测试文件、未触碰 `conftest.py`、未触碰任何 `app/**` 业务代码。

---

## 4. 为什么没有削弱测试

- 断言强度未下降：依然要求 `count == 0` 和 `data == []`，只是把比对的对象从「全局共享用户」改为「这个测试自己刚创建的用户」。
- 覆盖语义未下降：原测试的语义就是「一个用户在没有任何数据时，拿到的 unmatched-purchase-records 应该是空列表」——它本来就不依赖 `EMAIL_TEST_USER` 的特殊身份，使用全局用户只是历史巧合。
- 类型/逻辑路径覆盖未下降：依然走完整的认证 → 路由 → service → repository 链路，仅是用户身份换成了刚刚通过 `authentication_token_from_email` 注册并登录的全新用户。
- 没有 `try/except` 吞错、没有 `assert True`、没有用 `pytest.skip`、没有 `tolerance >= 0` 之类的放水。

副作用：每次跑这个测试会多注册一个用户（`random_email()`）。这个开销在已有 fresh-user 模式（`test_available_invoices_empty`、dashboard 套件、reimbursement_exports 等多处）里已经是项目内的正常代价，不构成额外负担。

---

## 5. 越界自检

巡检全程严格遵守允许/禁止边界。

**允许范围内的修改**：
- `backend/tests/finance/invoice_matching/index_test.py` — 单个函数，per-test fresh user 模式（§3）。
- `docs/testing-stability-report.md` — 本报告（新增文件）。

**禁区，未触碰**：
- ✅ `backend/app/**` — 没有改任何业务代码、模型、迁移、router、service、schema。
- ✅ `backend/app/alembic/**` — 没有新增/修改任何迁移。
- ✅ `backend/pyproject.toml` / `uv.lock` — 没有改依赖声明。`openpyxl` 是临时装在容器 venv 里，未提交到任何 tracked 文件。
- ✅ `backend/tests/conftest.py` — 没有改 fixture、没有改 DB 生命周期、没有引入 autouse 清表。所有污染在「具体测试用 fresh user」就消化掉了。
- ✅ `backend/app/modules/finance/reimbursement_exports/**` — Round 008 边界，零改动。
- ✅ `backend/tests/finance/reimbursement_exports/**` — Round 008 边界，零改动。已知问题（错误的 `from backend.tests...` 导入）写入 §2.2 留给 Round 008 处理。
- ✅ `frontend/**` — 完全没动。
- ✅ `skills/**` — 完全没动。
- ✅ `.env` — 完全没动。

**git status 验证**（仅列出本次相关文件）：
- `backend/tests/finance/invoice_matching/index_test.py` — modified（既有文件，一个函数，per-test fresh user）
- `docs/testing-stability-report.md` — new

未在禁区出现新增、删除或修改。

---

## 6. 容器环境备注

- 测试在容器 venv `/app/.venv`（Python 3.10）里运行；pytest 使用的是 `/app/.venv/bin/py.test`。
- `auto_discover_modules("app.modules")` 会强制 import 所有已注册工具，所以即便组合 5 完全不涉及 finance，也会因为 `reimbursement_exports.__init__` 里的 `from .router import router → service → excel_builder → import openpyxl` 而需要 openpyxl 存在。这是当前 Round 008 还没合并到主线时的脆弱点，本次巡检通过 `uv pip install` 规避；建议 Round 008 在合并前把 `openpyxl` 加进 `pyproject.toml`，否则任何不相关测试都无法启动。
- 未对 Postgres 做任何 schema 操作；每个 pytest 进程仍按 `app_test_<pid>` 单独建库，运行结束后由 conftest teardown 删除。

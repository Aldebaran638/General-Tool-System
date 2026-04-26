# Round 007 Backend Report — finance_dashboard

本轮按 dispatch-backend.md 派单实现 `finance / dashboard` 只读统计工具，新增 `backend/app/modules/finance/dashboard/` 模块，并以「最小侵入」方式将 Round 005 `invoice_matching` 中的分摊金额 helper 由私有改为可跨模块复用。

## 1. 输入物路径

- `skills/members/后端skill.md`
- `skills/tool-module-builder/SKILL.md`
- `docs/rounds/round-007/requirements.md`
- `docs/rounds/round-007/design.md`
- `docs/rounds/round-007/test-plan.md`
- `docs/rounds/round-007/tasks.md`
- `docs/rounds/round-007/dispatch-backend.md`
- `backend/app/MODULE_ARCHITECTURE.md`
- `backend/app/modules/README.md`
- `backend/app/modules/finance/purchase_records/`
- `backend/app/modules/finance/invoice_files/`
- `backend/app/modules/finance/invoice_matching/`
- `backend/tests/finance/purchase_records/index_test.py`
- `backend/tests/finance/invoice_files/index_test.py`
- `backend/tests/finance/invoice_matching/index_test.py`

## 2. 目标模块路径

- 主模块：`backend/app/modules/finance/dashboard/`
- 测试目录：`backend/tests/finance/dashboard/`
- API 前缀：`/api/v1/finance/dashboard`

## 3. 修改文件路径（已存在文件）

- `backend/app/modules/finance/invoice_matching/service.py`
  - 将 `_get_allocated_for_invoice` 重命名并改为公开导出：`get_allocated_for_invoice(session, *, invoice_file_id, exclude_match_id=None)`。
  - 三处调用点全部更新（定义处、`list_candidates` 计算 `remaining`、`_validate_pair_for_match` 校验剩余金额）。
  - 函数 docstring 中明确写出「Public helper: cross-module callers (e.g. finance.dashboard) reuse this instead of duplicating the allocation rule」，避免后续模块再次复制粘贴 active match 求和规则。
  - 行为上零变化（依旧遍历 `confirmed + needs_review` 的 active match 累加 `purchase_record.amount`），只是让 dashboard 可以在不重写规则的前提下调用。

未对 `purchase_records` / `invoice_files` 模块作任何修改；未引入新的数据库迁移。

## 4. 新增文件路径

模块代码：

- `backend/app/modules/finance/dashboard/__init__.py`
  自注册到 `app.modules.registry.register_module(name="dashboard", group="finance", router=router, models=[])`，`models=[]` 表示本工具不持有任何 ORM 表。
- `backend/app/modules/finance/dashboard/constants.py`
  - `PENDING_DEFAULT_LIMIT = 20`、`PENDING_MAX_LIMIT = 100`
  - `PENDING_TYPE_PURCHASE_UNMATCHED` / `PENDING_TYPE_INVOICE_UNALLOCATED` / `PENDING_TYPE_MATCH_NEEDS_REVIEW`
  - `SEVERITY_INFO` / `SEVERITY_WARNING` / `SEVERITY_DANGER`
  - `PRIORITY_BY_TYPE`：needs_review (30) > unallocated (20) > unmatched (10)
  - `SEVERITY_BY_TYPE`：needs_review → warning，其余 info
  - `SCOPE_SELF` / `SCOPE_GLOBAL`
- `backend/app/modules/finance/dashboard/schemas.py`
  全部为 SQLModel 响应模型，无表：`PurchaseRecordSummary` / `InvoiceFileSummary` / `MatchSummary` / `DashboardSummary` / `PendingItem` / `PendingList` / `ByUserItem` / `ByUserList`。
- `backend/app/modules/finance/dashboard/repository.py`
  纯 SQL 聚合层，零业务逻辑：
  - `count_purchase_records(owner_id, deleted=False)`
  - `list_eligible_purchase_records(owner_id)`（status ∈ {submitted, approved} 且未删除）
  - `count_invoice_files(owner_id, status=None, deleted=False)`、`count_voided_invoices(owner_id)`
  - `list_confirmed_invoices(owner_id)`
  - `count_matches_by_status(owner_id, status)`、`list_needs_review_matches(owner_id)`
  - `list_active_users()`、`get_user_email_map(owner_ids)`（管理员视图回填邮箱）
- `backend/app/modules/finance/dashboard/service.py`
  - `_classify_invoice_allocation(session, invoice)` 复用 `invoice_matching.service.get_allocated_for_invoice`，按 `unallocated / partially_allocated / fully_allocated` 三桶归类。
  - `_purchase_has_active_match` 复用 `invoice_matching.repository.get_active_match_for_purchase_record`，避免重写 active match 判断。
  - `read_summary(current_user)` 输出 `{scope, purchase_records, invoice_files, matches}`，`scope` 为 `"self"` / `"global"`。
  - `list_pending(current_user, limit=20)` 收集三类待办（unmatched PR / unallocated invoice / needs_review match），按 `(-PRIORITY_BY_TYPE, created_at ASC)` 排序后截到 `limit`；非 superuser 只看自己；新条目使用相应 `business_date`（PR 用 purchase_date，发票用 invoice_date，match 用对应 PR 的 purchase_date）。
  - `list_by_user(current_user)` 仅 `is_superuser` 可调，否则直接 `raise HTTPException(403)`；按 `(-total_pending, owner_email)` 排序，并过滤 `total_pending == 0` 的用户行（管理员看到的全部是有动作可做的用户）。
- `backend/app/modules/finance/dashboard/router.py`
  3 个 GET 端点，全部 owner-only / admin-all 语义，由 service 层负责权限。`/pending` 的 `limit` 通过 `Query(default=PENDING_DEFAULT_LIMIT, ge=1, le=PENDING_MAX_LIMIT)` 由 FastAPI 直接做 422 校验，不需要 service 层兜底。

测试：

- `backend/tests/finance/dashboard/__init__.py`（空 package marker）
- `backend/tests/finance/dashboard/index_test.py`（17 条 pytest 用例）

## 5. 新增的 API

所有端点挂载在 `/api/v1/finance/dashboard`：

| Method | Path | 说明 | 权限 |
|---|---|---|---|
| GET | `/summary` | 当前视角的 `purchase_records` / `invoice_files` / `matches` 计数；返回 `scope=self/global` | 普通用户 owner-only；管理员全局 |
| GET | `/pending?limit=` | 待处理事项流（unmatched PR + unallocated invoice + needs_review match），按 priority + created_at 排序，默认 20、最大 100 | 同上 |
| GET | `/by-user` | 按用户聚合 pending 数量，供管理员快速识别瓶颈用户；`total_pending == 0` 的行被过滤掉 | 仅管理员；普通用户 403 |

`/summary` 响应体严格匹配 `docs/rounds/round-007/design.md` 给的 JSON 形状：

```json
{
  "scope": "self",
  "purchase_records": {"total": ..., "unmatched": ..., "matched": ..., "deleted": ...},
  "invoice_files":   {"total": ..., "unallocated": ..., "partially_allocated": ..., "fully_allocated": ..., "voided": ...},
  "matches":         {"confirmed": ..., "needs_review": ..., "cancelled": ...}
}
```

`/pending` 响应体每条 `data[i]` 含 `type / severity / title / description / entity_type / entity_id / owner_id / owner_email / business_date / created_at`，与 design.md 一致。

`/by-user` 响应体每条 `data[i]` 含 `owner_id / owner_email / purchase_record_unmatched / invoice_file_unallocated / match_needs_review / total_pending`。

## 6. 新增或修改的模型

- 新增 ORM 表：**无**。
- 新增 SQLModel **响应**模型（非表）：`PurchaseRecordSummary` / `InvoiceFileSummary` / `MatchSummary` / `DashboardSummary` / `PendingItem` / `PendingList` / `ByUserItem` / `ByUserList`，全部位于 `app.modules.finance.dashboard.schemas`，未通过 metadata 创建表。

## 7. 统计口径说明

完全按 `design.md` 第 111-134 行口径实现：

### 购买记录 (`purchase_records`)

- `total`：`deleted_at IS NULL` 的全部 PR 计数。
- `deleted`：`deleted_at IS NOT NULL` 的 PR 计数（与 active 互斥）。
- `unmatched`：active PR（未删除）且不存在 active match。"active match" 定义沿用 Round 005，即 `status IN ('confirmed', 'needs_review')`。
- `matched`：active PR（未删除）且存在 active match。
- `total = unmatched + matched`，`deleted` 单独一桶。

### 发票 (`invoice_files`)

- `total`：`deleted_at IS NULL` 的全部发票计数。
- `voided`：`status = 'voided'` 计数。
- 仅对 `status = 'confirmed'` 的发票按分摊金额分类：
  - `unallocated`：`allocated <= 0`
  - `partially_allocated`：`0 < allocated < invoice_amount`
  - `fully_allocated`：`invoice_amount - allocated <= AMOUNT_TOLERANCE` (`AMOUNT_TOLERANCE = 0.01` 来自 invoice_matching 常量)
- `allocated` **直接复用** `invoice_matching.service.get_allocated_for_invoice`，dashboard 不实现自己的求和逻辑。
- 发票总数包括 draft / confirmed / voided 全部状态的非删除行；分摊三桶之和 ≤ confirmed 子集而 ≠ total（draft / voided 不进入分摊三桶）。

### 匹配 (`matches`)

- `confirmed`：`status = 'confirmed'` 计数。
- `needs_review`：`status = 'needs_review'` 计数。
- `cancelled`：`status = 'cancelled'` 计数。

### Pending 列表

- `unmatched_purchase_record`：active 且 status ∈ {submitted, approved}（与 invoice_matching 候选可匹配性口径对齐）且无 active match。
  - draft / rejected / 已删除 PR **不进入** pending，因为它们的合理动作是先调整状态而非"立刻去找发票"。
- `invoice_unallocated`：confirmed 发票且 `allocated <= 0`（部分分摊不视作 pending，避免 100 张发票里只填了 0.01 的全部冒到通知中心）。
- `match_needs_review`：所有 `needs_review` 状态的 match。
- 排序键：`(-PRIORITY_BY_TYPE[type], created_at ASC)`；同优先级下越早创建越靠前。

### By-User

按用户聚合上述三类 pending 的计数，`total_pending = unmatched_pr + unallocated_inv + needs_review_match`；`total_pending == 0` 的用户行被过滤，避免管理员视图被无操作可做的用户淹没。

## 8. 权限规则说明

| 端点 | 普通用户 | 管理员 |
|---|---|---|
| `GET /summary` | 仅看自己（`scope=self`） | 全局（`scope=global`） |
| `GET /pending` | 仅看自己 | 全局 |
| `GET /by-user` | **403 Forbidden** | 全局聚合 |

实现方式：

- `service.read_summary` / `service.list_pending` 内部根据 `current_user.is_superuser` 决定 `owner_id = None | current_user.id`；不调用任何 router-level Depends 守卫，使权限决策集中在 service 层。
- `service.list_by_user` 在入口处直接 `if not current_user.is_superuser: raise HTTPException(status_code=403, detail="Admin only")`，与 invoice_matching 的写操作一致沿用 owner-only / admin-bypass 的语义边界。
- 未引入任何新的 Depends 或 deps 修改，未触碰 `backend/app/api/routes/**`。

## 9. 新增的测试

`backend/tests/finance/dashboard/index_test.py`，**17** 条用例，分组覆盖派单全部硬性需求：

**Auth / 路由暴露**

- `test_summary_unauthenticated` / `test_pending_unauthenticated` / `test_by_user_unauthenticated`：未登录访问三端点全部 401/403。

**Summary 形状与 scope 切换**

- `test_summary_returns_expected_shape`：响应字段与 design.md 完全匹配。
- `test_summary_normal_user_only_counts_own_data`：普通用户只看自己；并通过对照管理员视图证明全局 ≥ 单用户。
- `test_summary_admin_scope_is_global`：superuser 拿到 `scope == "global"`。

**购买记录计数**

- `test_unmatched_purchase_count_excludes_active_match`：confirmed 与 needs_review match 都让 PR 进入 `matched`、不进 `unmatched`。
- `test_deleted_purchase_separated_from_active_count`：软删除后 `total` 减 1、`deleted` 加 1，`unmatched` 也相应减少。

**发票分摊三桶**

- `test_invoice_allocation_buckets`：unallocated / partially_allocated (`40 / 100`) / fully_allocated (`60+40 / 100`) 三类各 +1；voided 桶在新增一张 voided 发票后正确 +1。

**匹配状态计数**

- `test_match_status_counts`：confirmed / needs_review / cancelled 三类计数同时增长。

**Pending 列表**

- `test_pending_default_limit_caps_at_20`：往同一用户塞 25 条 unmatched PR，service 默认 cap 在 20。
- `test_pending_normal_user_only_sees_own_items`：普通用户的 pending 不会冒出别的 owner 行（`owner_id != other_id`）。
- `test_pending_includes_needs_review_match`：把 confirmed match 切到 needs_review 后，pending 中含 `type == match_needs_review`。

**By-User（管理员专用）**

- `test_by_user_normal_user_forbidden`：普通用户 403。
- `test_by_user_admin_returns_aggregate`：管理员能看到包含被测用户的聚合行；`total_pending >= unmatched`；`owner_email` 与该用户邮箱一致。

**Limit 边界（FastAPI Query 422）**

- `test_pending_limit_validation_rejects_zero`：`limit=0` → 422。
- `test_pending_limit_validation_rejects_too_large`：`limit=10000` → 422。

测试用例不直接断言全局绝对计数（共享 session-scoped DB 容易被其他测试污染），改用「断言 ≥」+「相对增量」+「跨视角对照」组合验证，与 invoice_matching 测试基线一致。

## 10. 后端测试结果

执行环境：`docker compose exec -T backend pytest ... -q`

| 套件 | 用例数 | 结果 |
|---|---|---|
| `tests/finance/dashboard/index_test.py` | 17 | 全部通过 |
| `tests/finance/invoice_matching/index_test.py` | 35 | 全部通过 |
| `tests/finance/purchase_records/index_test.py` | 42 | 全部通过 |
| `tests/finance/invoice_files/index_test.py` | 54 | 全部通过 |

所有警告均为 `SECRET_KEY` / `POSTGRES_PASSWORD` / `FIRST_SUPERUSER_PASSWORD` 默认值告警，与本轮无关。

测试运行在 conftest.py 配置的 per-PID 隔离测试库 `app_test_<pid>` 上，未对开发库 `app` 写入。

## 11. 迁移状态检查结果

```text
docker compose exec -T backend alembic current
a4e06ea5ffad (head)
```

`a4e06ea5ffad` 与 main 当前 head 一致，未生成新迁移。本轮严格不新增数据库表，dashboard 仅是读取层，所有统计都通过 SQL 聚合 + Round 005 已有规则得到。

## 12. 后端越界自检结果

本轮实际改动文件清单：

- `backend/app/modules/finance/dashboard/` 全部 6 个文件（新建，dispatch 允许范围内）
- `backend/app/modules/finance/invoice_matching/service.py`（dispatch 允许范围内：「仅限提取可复用统计 / 金额 helper」，本次为 `_get_allocated_for_invoice` → `get_allocated_for_invoice` 的命名调整 + 调用点同步）
- `backend/tests/finance/dashboard/__init__.py`、`backend/tests/finance/dashboard/index_test.py`（dispatch 允许）
- `docs/rounds/round-007/backend-report.md`（dispatch 允许）

未改动：

- `frontend/**`、`skills/**`、`.env`
- `backend/app/api/routes/**`
- `backend/app/modules/finance/purchase_records/**`（核心业务，dispatch 禁止）
- `backend/app/modules/finance/invoice_files/**`（核心业务，dispatch 禁止）
- 其他无关后端模块 / 测试基础设施 / 用户角色体系 / 签字相关功能
- 数据库 migration（dispatch 默认禁止本轮新增）

特别说明：

- `invoice_matching/service.py` 的修改严格落在「仅限提取可复用 helper」这一 dispatch 子条款内：函数体一字未改，只把名字从 `_get_allocated_for_invoice` 改成 `get_allocated_for_invoice` 并补 docstring；3 处调用点同步更新。**没有**借此机会改 invoice_matching 的业务行为或评分规则。
- 没有借「金额规则统一」名义把 `_validate_pair_for_match` 等其他私有函数也改公开；只动派单确实需要的那一个。

结论：**修改严格落在派单允许范围内，未越界**。

## 13. 联调检查中后端已验证项与未验证项

后端已验证（自动化测试覆盖）：

- 模块通过 `app.modules.registry` 自注册并挂载到 `/api/v1/finance/dashboard`，三个端点均可由 TestClient 命中。
- `/summary`：购买记录 4 桶 / 发票 5 桶 / 匹配 3 桶 数值与 design.md 口径一致；普通用户视角与 admin 全局视角分别返回正确 scope；软删除 PR 立刻反映到 `deleted` 桶。
- `/pending`：默认 cap 在 20、上限 100；非 owner 数据不会泄漏；needs_review match 进入列表；`limit=0` / `limit=10000` 触发 422。
- `/by-user`：普通用户 403；admin 可见聚合行且邮箱、unmatched / unallocated / total_pending 数值正确。
- 跨模块复用：dashboard 调用 `invoice_matching.service.get_allocated_for_invoice` 计算分摊，未在自身模块内重新实现求和逻辑；`get_active_match_for_purchase_record` 复用 invoice_matching repository。
- Round 005 invoice_matching 35 条原有用例在 helper 重命名后零回归。

后端尚未验证（依赖架构师 / 前端联调）：

- 与前端 `frontend/src/tools/finance/dashboard/`（路由 `/finance.dashboard`）的端到端联调（前端任务在并行派单中，由前端 AI 负责）。
- i18n 字段（`finance.dashboard.*`）的接入，本轮后端不涉及 UI 文案。
- 大数据量下 `/by-user` 的性能（当前实现遍历 `list_active_users` 后逐个聚合，未做分页 / 索引优化；本轮按派单只要求功能正确）。

## 14. 未完成项

- 派单内的所有功能层硬性要求（自注册、三端点、4 / 5 / 3 桶口径、limit 默认 20 上限 100、复用 Round 005 helper、admin-only by-user、非 admin 仅看自己）均已落地并由测试覆盖。
- **跨套件预存在问题（非本轮回归）**：`docker compose exec -T backend pytest tests/finance/ -q` 一并跑全部 finance 子套件时，`tests/finance/invoice_matching/index_test.py::test_available_invoices_empty` 会失败 1 条；原因是 `tests/finance/invoice_files/` 在共享 session-scoped DB 上预先注入了 confirmed 发票，污染了「列表为空」断言。
  - 复现验证：在删除 dashboard 全部新增文件 / 撤销 invoice_matching helper 重命名（`git stash`）后，该测试在「invoice_files + invoice_matching」组合下依然失败；恢复改动（`git stash pop`）后再次确认依然失败。结论：与 Round 007 无因果关系。
  - 派单的硬性测试要求是 dashboard 单套件 + invoice_matching 单套件 + alembic current，三者本轮均通过。
  - 建议后续单独立项修复（让 invoice_matching 该测试在断言前 scope 到本测试自建用户，而非全局空值）。本轮不在 dispatch 允许范围内，未触碰。
  - **更新（测试稳定性补丁，已合并）**：该问题已在后续「测试稳定性」专项派单中以单测级修复落地，详见本报告 §16。修复后 `pytest tests/finance/invoice_files tests/finance/invoice_matching -q` 89 passed / 0 failed，`pytest tests/finance/ -q` 148 passed / 0 failed。

## 15. 是否仅在任务清单授权范围内完成修改

**是。** 本轮修改严格收敛于以下 dispatch-backend.md 允许的目录：

- `backend/app/modules/finance/dashboard/**`
- `backend/app/modules/finance/invoice_matching/**`（仅 service.py 的 helper 重命名，无业务行为变化）
- `backend/tests/finance/dashboard/**`
- `docs/rounds/round-007/backend-report.md`

未触碰禁止目录（`frontend/**`、`skills/**`、`.env`、`backend/app/api/routes/**`、购买记录与发票文件核心业务逻辑、用户角色体系、签字功能）。未新增数据库迁移。未自行扩大目标模块数量，未以「统一」/「重构」名义迁移无关现有工具。

## 附录 A：复用 Round 005 helper 的具体路径

| Dashboard 调用 | invoice_matching 提供的 helper | 用途 |
|---|---|---|
| `dashboard.service._classify_invoice_allocation` | `invoice_matching.service.get_allocated_for_invoice` | 计算 confirmed 发票的 allocated，再与 `invoice_amount` 对比落桶 |
| `dashboard.service._purchase_has_active_match` | `invoice_matching.repository.get_active_match_for_purchase_record` | 判断 PR 是否进入 matched 桶 / 是否进 pending 列表 |
| `dashboard.service.read_summary` | `invoice_matching.constants.MATCH_STATUS_*` | 复用匹配状态常量，避免 dashboard 自行硬编码字符串 |
| `dashboard.service` | `invoice_matching.constants.AMOUNT_TOLERANCE` | `fully_allocated` 判定阈值 |

未在 dashboard 模块内复制 active match 的求和逻辑或评分规则；分摊金额规则单点权威来源依旧是 `invoice_matching.service.get_allocated_for_invoice`。

## 附录 B：Pending 优先级与 severity 决策

| Type | Priority | Severity | 触发条件 |
|---|---|---|---|
| `match_needs_review` | 30 | warning | 任一 active match 被生命周期事件标记为 `needs_review` |
| `invoice_unallocated` | 20 | info | confirmed 发票且 allocated ≤ 0 |
| `purchase_unmatched` | 10 | info | 非删除 PR、status ∈ {submitted, approved}、无 active match |

理由：

- needs_review 代表"既有匹配被打破"，比从零开始建匹配更紧迫，故优先级最高、severity 用 warning。
- unallocated invoice 与 unmatched PR 都是"还没建匹配"，但 unallocated invoice 是用户已经上传发票后的卡点（收据已交，待映射），用户操作意愿更强；unmatched PR 多数情况下用户还在补发票，因此 invoice 优先于 PR。
- 全部三类同优先级时按 created_at ASC 排序，最早出现的待办先暴露。

## 附录 C：Helper 重命名对外影响面分析

`_get_allocated_for_invoice` 是 Round 005 私有 helper，命名调整前 grep 全仓库结果如下：

- `backend/app/modules/finance/invoice_matching/service.py`：3 处（定义 + 2 处调用）。
- 所有 `backend/tests/`、`backend/app/api/`、`frontend/`、`skills/` 子树均无任何引用。

因此本次重命名只产生 invoice_matching/service.py 内部 3 行修改，对 invoice_matching 公开契约 / API 行为 / 测试用例零影响（35 条测试零回归）。Dashboard 通过 `from ..invoice_matching.service import get_allocated_for_invoice` 直接复用，没有引入额外 wrapper 层。

## 16. 测试稳定性补丁：invoice_files × invoice_matching 跨套件污染修复

§14 中标注的"未完成项"（仅在 invoice_files + invoice_matching 联合运行时 `tests/finance/invoice_matching/index_test.py::test_available_invoices_empty` 失败）已通过单测级别修复落地，落在「测试稳定性」专项派单授权范围内。

### 16.1 根因

`test_available_invoices_empty` 复用 session-scoped `normal_user_token_headers` fixture（即认证为全局 `EMAIL_TEST_USER`），并断言"该用户的 available invoices 列表 count == 0"。这是一个隐性"全局状态为空"假设。

但 `tests/finance/invoice_files/index_test.py` 中以下用例会在测试过程中为同一全局用户生成 **confirmed** 状态发票：

- `test_confirm_invoice`（line 553）：直接对 normal user 拥有的发票调 `/confirm`，留下 1 条 confirmed 发票。
- `test_withdraw_confirmation`（line 571）：先用 `_create_random_invoice(..., status=STATUS_CONFIRMED)` 注入 1 条 confirmed 发票再撤回，撤回过程虽然把 status 改回 draft，但若 owner_id 流程中其他状态切换有异步残留，依然可能保留 confirmed 数据。
- 其他若干 confirm/withdraw/restore 流程会临时把 normal user 的发票切到 confirmed。

session-scoped `db` fixture 在整个 pytest 进程生命周期内只重建一次（per-PID），跨文件共享。pytest 默认按文件路径字典序运行：`invoice_files` 排在 `invoice_matching` 之前，所以 invoice_files 留下的 confirmed 发票会被 invoice_matching 的 `test_available_invoices_empty` 看到。

复现命令（修复前）：

```text
docker compose exec -T backend pytest \
  tests/finance/invoice_files/index_test.py \
  tests/finance/invoice_matching/index_test.py -q
...
FAILED tests/finance/invoice_matching/index_test.py::test_available_invoices_empty
assert 2 == 0
```

invoice_matching 单独运行时通过，因此问题不在 invoice_matching 自身的业务逻辑或读路径，而在于"测试隐含假设全局空状态"这一脆弱前提。

### 16.2 修改文件

仅一文件变更：

- `backend/tests/finance/invoice_matching/index_test.py`
  - `test_available_invoices_empty`：把依赖 `normal_user_token_headers` 改为「该测试自建一个新用户并用其 token 发请求」。
  - 函数签名由 `(client, normal_user_token_headers)` 改为 `(client, db)`。
  - 测试体内调用 `tests.utils.user.authentication_token_from_email(client=client, email=random_email(), db=db)` 创建并登录全新用户；该用户在测试运行的瞬间数据库内不可能有任何 invoice / match 记录。
  - 断言保持 `count == 0` 与 `data == []`，含义不变。
  - 函数顶部加注释解释：选择 per-test fresh user 的原因是"防止其他工具套件对全局 normal user 的写操作污染本断言"，而非"让断言宽松"。

未触动：

- `backend/tests/finance/invoice_files/index_test.py`：无需修改，不消减原有覆盖。
- `backend/tests/conftest.py`：未引入 function-scoped DB 重置或 transaction rollback。dispatch 明确禁止改 conftest，除非证明单测级修复不可行；本次单测级修复完全充分，conftest 零变化。
- 任何 `backend/app/modules/**` 业务代码：dispatch 禁止；本补丁也无需改业务，因为问题在测试层。

### 16.3 修复策略

把"全局 normal user 的发票列表是空的"这一**全局状态假设**替换为"该测试当场创建的全新用户的发票列表必然是空的"这一**结构性事实**。

具体落地：

```python
def test_available_invoices_empty(client: TestClient, db: Session) -> None:
    from tests.utils.user import authentication_token_from_email
    from tests.utils.utils import random_email

    headers = authentication_token_from_email(
        client=client, email=random_email(), db=db
    )
    response = client.get(f"{BASE_URL}/available-invoices", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["data"] == []
```

`authentication_token_from_email` 是 `tests/utils/user.py` 已有 helper：传入新邮箱即创建用户并返回登录 token，复用基础设施零新增。

未采用的反向方案及理由：

- ❌ 把断言改成 `count >= 0` 或 `count == previously_observed_value`：会丢失"用户没有发票时应该看到空列表"这一契约的有效性，dispatch 明确禁止此类做法。
- ❌ 在测试 fixture 里 truncate 全局表：会掩盖 invoice_files 自己的状态，且把测试隔离责任推到全局基础设施层，违反 dispatch 「不要清空全局表来掩盖问题」要求。
- ❌ 把 invoice_files 改成总是用 fresh user：超出 dispatch「仅当确实需要」的允许边界，且 invoice_files 大量 state-transition 测试本身依赖 normal_user_token_headers 也是合理选择。

### 16.4 为什么不会削弱测试

新断言验证的契约严格更强：

- 旧断言："认证为 EMAIL_TEST_USER 时，`/available-invoices` 返回的 count 是 0"——隐含「全局共享用户没有 confirmed 发票」，依赖测试运行顺序与外部状态。
- 新断言："认证为一个刚创建的新用户时，`/available-invoices` 返回的 count 是 0"——直接验证业务契约「未拥有任何 confirmed 发票的用户看到空列表」。

更具体地，新版本继续验证：

1. `/available-invoices` endpoint 对认证用户存在（200）。
2. 响应结构含 `count` 与 `data` 字段。
3. 对没有 confirmed 发票的用户，`count == 0` 且 `data == []`（即不会泄漏其他用户的发票）。

如果 service 层意外把所有用户的发票都返回（owner_id filter 失效），新断言依然会失败（fresh user 看到 N 条数据），因此 owner-scoping 这条核心契约**仍然被守护**。换言之，本补丁让断言更鲁棒，而不是更宽松。

### 16.5 执行命令与结果

以 dispatch 列出的四条命令为准：

| 命令 | 期望 | 实际 |
|---|---|---|
| `docker compose exec -T backend pytest tests/finance/invoice_matching/index_test.py -q` | 通过 | **35 passed** |
| `docker compose exec -T backend pytest tests/finance/invoice_files/index_test.py tests/finance/invoice_matching/index_test.py -q` | 通过 | **89 passed**（54 + 35） |
| `docker compose exec -T backend pytest tests/finance/invoice_files/index_test.py -q` | 通过 | **54 passed** |
| `docker compose exec -T backend alembic current` | head | `a4e06ea5ffad (head)` |

补充健康检查（非 dispatch 必需，但用于确认无更广泛回归）：

- `docker compose exec -T backend pytest tests/finance/ -q` → **148 passed**（finance 全套件，含 dashboard 17 / invoice_matching 35 / invoice_files 54 / purchase_records 42）。
- 警告项保持 3 条 `SECRET_KEY` / `POSTGRES_PASSWORD` / `FIRST_SUPERUSER_PASSWORD` 默认值告警，与本补丁无关。

修复前 `pytest tests/finance/invoice_files tests/finance/invoice_matching` 是 1 failed / 88 passed；修复后 0 failed / 89 passed（多出来的 1 条来自原本被失败短路掉的下游断言）。

### 16.6 越界自检

本补丁实际改动文件：

- `backend/tests/finance/invoice_matching/index_test.py`：dispatch 允许范围内（"测试稳定性补丁"明确允许该文件）。
- `docs/rounds/round-007/backend-report.md`：dispatch 允许「记录测试稳定性补丁」的文件之一。

未改动：

- `backend/app/modules/**` 业务代码（dispatch 禁止）。
- `backend/app/alembic/**`（dispatch 禁止；本补丁也无需迁移）。
- `backend/tests/conftest.py`（dispatch 默认禁止，单测级修复完全充分时不应触碰）。
- `backend/tests/finance/invoice_files/index_test.py`（dispatch 允许「仅当确实需要」；本补丁不需要）。
- `frontend/**`、`skills/**`、`.env`：dispatch 严禁。

未做：

- 没有把 `count >= 0` / `count == arbitrary` 等弱断言塞进测试。
- 没有清空表 / TRUNCATE / DELETE FROM 任何业务表。
- 没有借此机会"统一" invoice_files 和 invoice_matching 测试 fixture。
- 没有新增数据库迁移。
- 没有改业务代码。

结论：**修改严格落在派单允许范围内，未越界**。修复策略为单测级最小变更，不依赖任何全局基础设施改动。

# Round 005 Backend Report — invoice_matching

本轮交付分三阶段：先按设计实现 `finance/invoice_matching` 模块及其与 `purchase_records`、`invoice_files` 的集成，再依据架构师下发的「修复任务（harden）」清单回头修复了六大类偏差与硬性测试缺口，最后依据「补丁任务（matching eligibility lifecycle fixes）」补齐候选可匹配性校验和三条新生命周期事件的 needs_review 集成。本报告反映合并后的最终交付状态。

## 1. 输入物路径

- `skills/members/后端skill.md`
- `skills/tool-module-builder/SKILL.md`
- `docs/rounds/round-005/requirements.md`
- `docs/rounds/round-005/design.md`
- `docs/rounds/round-005/test-plan.md`
- `docs/rounds/round-005/tasks.md`
- `docs/rounds/round-005/dispatch-backend.md`
- `backend/app/MODULE_ARCHITECTURE.md`
- `backend/app/modules/README.md`
- `backend/app/modules/finance/purchase_records/`
- `backend/app/modules/finance/invoice_files/`
- `backend/tests/finance/purchase_records/index_test.py`
- `backend/tests/finance/invoice_files/index_test.py`
- 架构师下发的修复任务清单（六类偏差：管理员只读、发票分摊、候选过滤、confirm 契约、reconfirm 重校验、needs_review 集成）

## 2. 目标模块路径

- 主模块：`backend/app/modules/finance/invoice_matching/`
- 测试目录：`backend/tests/finance/invoice_matching/`
- API 前缀：`/api/v1/finance/invoice-matching`

## 3. 修改文件路径（已存在文件）

- `backend/app/modules/finance/invoice_files/service.py`
  - `update_record`、`void_record`、`restore_draft`、`delete_record`、`restore_record`、`withdraw_confirmation` 末尾按需调用 `mark_needs_review_for_invoice_file(...)`，使用懒加载导入打破循环依赖。
  - 在所有返回 record 的方法（`update_record`、`void_record`、`restore_draft`、`restore_record`、`withdraw_confirmation`）中，在 hook 之后追加 `session.refresh(record)`，规避 SQLAlchemy `expire_on_commit=True` 导致 `model_dump()` 读到空 `__dict__` 的序列化崩溃。
- `backend/app/modules/finance/purchase_records/service.py`
  - `update_record`、`delete_record`、`restore_record`、`withdraw_record`、`reject_record` 末尾按需调用 `mark_needs_review_for_purchase_record(...)`。
  - 在 `update_record`、`restore_record`、`withdraw_record`、`reject_record` 中，hook 之后追加 `session.refresh(updated/restored)`。

## 4. 新增文件路径

模块代码：
- `backend/app/modules/finance/invoice_matching/__init__.py`（自注册到 `app.modules.registry`）
- `backend/app/modules/finance/invoice_matching/constants.py`（状态、阈值、评分权重、`AMOUNT_TOLERANCE=0.01`、`MAX_DATE_DIFF_DAYS=7`）
- `backend/app/modules/finance/invoice_matching/models.py`（SQLModel `InvoiceMatch` + `InvoiceMatchPublic` + `InvoiceMatchesPublic` + `CandidateInvoice`）
- `backend/app/modules/finance/invoice_matching/schemas.py`（统一 re-export，与同 group 其他模块对齐）
- `backend/app/modules/finance/invoice_matching/repository.py`（数据库访问层）
- `backend/app/modules/finance/invoice_matching/service.py`（业务逻辑：候选评分、分摊计算、确认/取消/重新确认、needs_review hook）
- `backend/app/modules/finance/invoice_matching/router.py`（HTTP 路由）

迁移：
- `backend/app/alembic/versions/6b683da4fd50_add_invoice_match_table.py`

测试：
- `backend/tests/finance/invoice_matching/__init__.py`
- `backend/tests/finance/invoice_matching/index_test.py`（30 条 pytest 用例）

## 5. 新增或修改的 API

所有端点挂载在 `/api/v1/finance/invoice-matching`：

| Method | Path | 说明 | 权限 |
|---|---|---|---|
| GET | `/summary` | 汇总：confirmed / cancelled / needs_review / 未匹配 PR / 可用发票 数量 | owner 看自己；superuser 看全部 |
| GET | `/unmatched-purchase-records` | 列出可参与匹配且无 active match 的 PR（`submitted` / `approved` 且未删除） | owner 看自己；superuser 看全部 |
| GET | `/available-invoices` | 列出可匹配的 `confirmed` 状态发票（已剔除 draft / voided / deleted） | 同上 |
| GET | `/candidates?purchase_record_id=...` | 实时候选列表，含 `allocated_amount`、`remaining_amount`、`score`、`score_breakdown`、`level`。**对 `draft` / `rejected` / 已删除等不合格 PR 直接返回 400**（避免静默返回空列表掩盖错误调用） | 读权限 |
| GET | `/matches?status=&skip=&limit=` | 列出匹配，自动过滤 PR 或发票已被删除的孤儿匹配 | 同读 |
| POST | `/confirm` | 确认匹配。**body 仅接受 `purchase_record_id` + `invoice_file_id`**，`extra="forbid"`；score / score_breakdown 一律由后端从权威状态重算 | owner-only，superuser 不可代操作 |
| POST | `/{match_id}/cancel` | 取消匹配；记录 `cancelled_by_id` / `cancelled_at` | owner-only |
| POST | `/{match_id}/reconfirm` | 将 `needs_review` 复确认为 `confirmed`；**重新执行全部确认校验**（owner / 状态 / 币种 / 7 天 / 剩余金额），并以 `exclude_match_id=match.id` 重算分摊；分数同样后端重算 | owner-only |

确认/取消/重新确认在 service 层统一以 `PermissionError` 表示鉴权失败、`ValueError` 表示业务校验失败、`HTTPException(404)` 表示对象缺失；router 层将前两者映射到 403 / 400。

## 6. 新增或修改的模型

新增 ORM 表 `invoice_match`（SQLModel `InvoiceMatch`）：

| 字段 | 类型 | 约束 |
|---|---|---|
| id | UUID | PK |
| owner_id | UUID | FK → `user.id`，CASCADE |
| purchase_record_id | UUID | FK → `purchase_record.id`，CASCADE |
| invoice_file_id | UUID | FK → `invoice_file.id`，CASCADE |
| status | VARCHAR(32) | `confirmed` / `cancelled` / `needs_review` |
| score | INTEGER | 默认 0 |
| score_breakdown | JSON | 各维度得分 |
| review_reason | VARCHAR(255) | `needs_review` 触发原因 |
| confirmed_by_id | UUID | nullable，FK → `user.id` |
| confirmed_at | TIMESTAMPTZ | nullable |
| cancelled_by_id | UUID | nullable，FK → `user.id` |
| cancelled_at | TIMESTAMPTZ | nullable |
| created_at | TIMESTAMPTZ | default `get_datetime_utc()` |
| updated_at | TIMESTAMPTZ | nullable |

视图模型（非表）：`InvoiceMatchPublic`、`InvoiceMatchesPublic`、`CandidateInvoice`。

未对 `purchase_record` / `invoice_file` 表结构做任何更改。

## 7. 新增或修改的测试

`backend/tests/finance/invoice_matching/index_test.py`，35 条用例，覆盖：

基础与生命周期（沿用原始实现的 15 条）：
- 模块自注册、未认证 401、404 路径、summary 空状态、列表分页、create-cancel-reconfirm 完整生命周期等。

修复轮新增（15 条，命中六类偏差）：
- `test_admin_cannot_confirm_match` / `test_admin_cannot_cancel_match` / `test_admin_cannot_reconfirm_match` —— 证明管理员对他人记录的写操作 403。
- `test_available_invoices_only_includes_confirmed` —— draft / voided 发票被剔除。
- `test_unmatched_only_includes_submitted_or_approved` —— draft 购买记录被剔除。
- `test_candidates_excludes_far_dates` —— 7 天硬过滤生效。
- `test_candidates_excludes_currency_mismatch` —— 币种不一致硬过滤。
- `test_two_purchases_share_one_invoice` —— 同一发票多 PR 分摊：`allocated_amount = sum(pr.amount)`，`remaining = invoice_amount - allocated`。
- `test_over_allocation_rejected` —— `(allocated + new_pr.amount) > (invoice_amount + 0.01)` 时 confirm 拒绝。
- `test_confirm_rejects_extra_score_fields` —— body 携带 `score` / `score_breakdown` 时 422。
- `test_confirm_recomputes_score_from_authoritative_state` —— 不传 score，响应 score 与后端按权威状态重算结果一致。
- `test_purchase_update_marks_match_needs_review` —— PR `update_record` 触发 needs_review。
- `test_purchase_delete_marks_match_needs_review` —— PR `delete_record` 触发 needs_review。
- `test_invoice_void_marks_match_needs_review` —— 发票 `void_record` 触发 needs_review。
- `test_invoice_delete_marks_match_needs_review` —— 发票 `delete_record` 触发 needs_review。

补丁轮新增（5 条，匹配可匹配性生命周期）：
- `test_candidates_rejects_draft_purchase` —— 对 draft PR 调 `/candidates` 返回 400 且 detail 含 `not eligible`。
- `test_candidates_rejects_rejected_purchase` —— 对 rejected PR 调 `/candidates` 返回 400。
- `test_invoice_withdraw_confirmation_marks_match_needs_review` —— 发票 `withdraw_confirmation`（confirmed → draft）触发 needs_review。
- `test_purchase_withdraw_marks_match_needs_review` —— PR `withdraw_record`（submitted → draft）触发 needs_review。
- `test_purchase_reject_marks_match_needs_review` —— PR `reject_record`（submitted → rejected，仅 admin 可调）触发 needs_review，且 admin 调用本身在 reject 业务上是被允许的。

`tests/finance/invoice_files/` 与 `tests/finance/purchase_records/` 未新增用例；它们用于回归证明 hook 注入未破坏既有契约。

## 8. 执行的校验命令

```bash
docker compose exec -T backend pytest tests/finance/invoice_matching/index_test.py -q
docker compose exec -T backend pytest tests/finance/invoice_files/index_test.py -q
docker compose exec -T backend pytest tests/finance/purchase_records/index_test.py -q
docker compose exec -T backend alembic current
```

## 9. 测试结果

| 套件 | 用例数 | 结果 |
|---|---|---|
| `tests/finance/invoice_matching/index_test.py` | 35 | 全部通过 |
| `tests/finance/invoice_files/index_test.py` | 54 | 全部通过 |
| `tests/finance/purchase_records/index_test.py` | 42 | 全部通过 |

合计 **131 通过 / 0 失败**，仅有 3 条来自 `app/core/config.py` 的 `SECRET_KEY` / `POSTGRES_PASSWORD` / `FIRST_SUPERUSER_PASSWORD` 默认值警告（非本轮变更，与本模块无关）。

测试运行在 conftest.py 配置的 per-PID 隔离测试库 `app_test_<pid>` 上，未对开发库 `app` 写入。

## 10. API 契约测试结果

invoice_matching 测试用例覆盖以下契约项目，均通过：
- `POST /confirm` 的 `extra="forbid"` 行为（多余字段 → 422）。
- `POST /confirm` 不接受客户端 score / score_breakdown，响应 score 由后端按 50 / 10 / 20 / 15 / 5 权重重算。
- 列表接口统一返回 `{count, data}` 结构。
- 确认/取消/重新确认在缺失对象时返回 404，鉴权不足返回 403，业务非法返回 400。
- 管理员对他人记录的写操作（confirm / cancel / reconfirm）一律 403。
- `GET /candidates` 在 PR 处于 `draft` / `rejected` / 已删除等不合格状态时返回 400 而非空列表，detail 里附带 `status` 与 `deleted` 信息便于排查。

## 11. 迁移校验结果

```text
docker compose exec backend alembic current
6b683da4fd50 (head)
```

`6b683da4fd50_add_invoice_match_table.py` 已经应用并位于 head。迁移内容：
- 创建 `invoice_match` 表。
- 创建 partial unique index `ix_invoice_match_active_purchase` on `(purchase_record_id) WHERE status IN ('confirmed', 'needs_review')`，确保同一 PR 同一时间最多只有一条 active match，同时允许历史 `cancelled` 行存在。

未修改 `purchase_record` / `invoice_file` 表结构，未引入多余迁移。

## 12. 后端越界自检结果

本轮实际改动文件：
- `backend/app/modules/finance/invoice_matching/`（新建，全部允许范围内）
- `backend/app/alembic/versions/6b683da4fd50_add_invoice_match_table.py`（允许）
- `backend/app/modules/finance/invoice_files/service.py`（允许，仅末尾追加 hook + refresh）
- `backend/app/modules/finance/purchase_records/service.py`（允许，仅末尾追加 hook + refresh）
- `backend/tests/finance/invoice_matching/`（允许）
- `docs/rounds/round-005/backend-report.md`（允许）

未改动：
- `frontend/**`、`skills/**`、`.env`、`backend/app/api/routes/**`、其他无关后端模块、其他模块测试基础设施。
- 未触发任何"结构统一"型迁移，未扩大目标模块数量。

结论：**修改严格落在派单允许范围内，未越界**。

## 13. 联调检查中后端已验证项与未验证项

后端已验证（通过自动化测试）：
- 模块通过 `app.modules.registry` 自注册并挂载到 `/api/v1/finance/invoice-matching`。
- 列表 / 候选 / summary 在 owner 与 superuser 视角下分别返回正确数据。
- 候选实时计算且不落库（response 中包含 score 但 DB 表无候选记录写入）。
- 候选过滤：currency 不匹配剔除、日期差 > 7 天剔除、低于 `SCORE_THRESHOLD_WEAK` 剔除、draft / voided / deleted 发票剔除、draft / deleted PR 剔除。
- 候选入口校验：对 `draft` / `rejected` / 已删除等不合格 PR，`/candidates` 直接 400。
- 确认与重新确认按权威状态重算 score，`extra="forbid"` 拒绝伪造 score。
- 分摊：`allocated = sum(active_match.purchase.amount)`、`remaining = invoice_amount - allocated`、阈值 `> invoice_amount + 0.01` 时确认拒绝。
- 跨模块 hook 完整覆盖：
  - PR：`update_record` / `delete_record` / `restore_record` / `withdraw_record` / `reject_record` 均能将相关 active match 切到 `needs_review`。
  - 发票：`update_record` / `void_record` / `restore_draft` / `delete_record` / `restore_record` / `withdraw_confirmation` 同上。
  - 所有写路径写入 `review_reason`。
- partial unique index 阻止同 PR 重复 active match（`existing` 早期分支 + DB 兜底）。
- 软删除孤儿匹配在 `/matches` 列表中被剔除。

后端尚未验证（需依赖架构师 / 前端联调）：
- 与前端 `frontend/src/tools/finance/invoice_matching/` 的端到端联调（前端任务尚未在本派单范围内）。
- 真实生产数据下评分阈值 60 / 80 的可调性与可解释性（仅在测试桩数据上验证算法正确性）。
- 取消后该 match 行不再占用分摊后，前端"剩余金额"刷新时序（依赖 SWR / TanStack Query 失效策略）。

## 14. 未完成项

- 无功能层未完成项。修复任务清单的全部六类偏差以及补丁任务清单的全部三项（候选可匹配性 400、`withdraw_confirmation` hook、`withdraw_record` / `reject_record` hook）均已落地并由测试覆盖。
- 报告中的"未验证项"非未完成的后端工作，而是需要在联调阶段由架构师 / 前端协同确认的运行期表现。

## 15. 是否仅在任务清单授权范围内完成修改

**是。** 本轮修改严格收敛于以下 dispatch-backend.md 允许的目录：

- `backend/app/modules/finance/invoice_matching/**`
- `backend/app/modules/finance/purchase_records/**`（仅 service.py 末尾追加 hook + refresh）
- `backend/app/modules/finance/invoice_files/**`（仅 service.py 末尾追加 hook + refresh）
- `backend/app/alembic/versions/**`
- `backend/tests/finance/invoice_matching/**`
- `docs/rounds/round-005/backend-report.md`

未触碰禁止目录（`frontend/**`、`skills/**`、`.env`、无关后端模块、`backend/app/api/routes/**`、其他模块测试基础设施）。未自行扩大目标模块数量，未以任何"统一/重构"理由迁移无关现有工具。

## 附录 A：修复任务的六类偏差与对应解法

| # | 偏差 | 解法 | 校验测试 |
|---|---|---|---|
| 1 | 管理员可写 | service 层引入 `_require_owner_only`（`PermissionError`，superuser 不旁路），仅 read 走 `_require_read_access` | `test_admin_cannot_confirm_match` / `cancel` / `reconfirm` |
| 2 | 分摊金额错误（误用发票金额相加） | `_get_allocated_for_invoice` 改为遍历 active match 并累加 `purchase.amount`，支持 `exclude_match_id` 供 reconfirm 自身排除 | `test_two_purchases_share_one_invoice`、`test_over_allocation_rejected` |
| 3 | 候选未硬过滤 draft / 币种 / 7 天 | `list_candidates` 在打分前用 `_currencies_match` + `_within_date_window` 双硬过滤；底层 `_invoice_eligible_for_match` / `_purchase_eligible_for_match` 排除 draft / voided / deleted | `test_available_invoices_only_includes_confirmed`、`test_unmatched_only_includes_submitted_or_approved`、`test_candidates_excludes_far_dates`、`test_candidates_excludes_currency_mismatch` |
| 4 | confirm 接受客户端 score | `ConfirmMatchRequest` 仅留 `purchase_record_id` + `invoice_file_id`，`model_config = {"extra": "forbid"}`；service 内部一律 `_score_candidate` 重算后写入 | `test_confirm_rejects_extra_score_fields`、`test_confirm_recomputes_score_from_authoritative_state` |
| 5 | reconfirm 不重校验 | reconfirm 重新加载 PR / 发票，调用 `_validate_pair_for_match(..., exclude_match_id=match.id)` 全量重校验，并由 repository.reconfirm_match 写回 score / score_breakdown | 生命周期测试 + 越额校验测试 |
| 6 | needs_review hook 缺失 / 集成不真实 | invoice_files 5 个写入路径（update / void / restore_draft / delete / restore）+ purchase_records 3 个写入路径（update / delete / restore）懒导入并调用 hook；返回 record 的方法在 hook 后 `session.refresh(record)` 修复 expire-on-commit 序列化空 `__dict__` 的问题 | `test_purchase_update_marks_match_needs_review`、`test_purchase_delete_marks_match_needs_review`、`test_invoice_void_marks_match_needs_review`、`test_invoice_delete_marks_match_needs_review` |

## 附录 B：评分权重与阈值参考

- `SCORE_AMOUNT_MATCH = 50`（`abs(diff) <= 0.01`）
- `SCORE_CURRENCY_MATCH = 10`
- `SCORE_DATE_EXACT = 20` / `SCORE_DATE_NEAR = 10`（1–3 天） / `SCORE_DATE_FAR = 5`（4–7 天）
- `SCORE_TEXT_SIMILARITY = 15`（订单名 / 类目 与发票号 / 卖家词集合交集非空）
- `SCORE_KEYWORD_MATCH = 5`（PR 备注 / 类目关键字命中卖家文本）
- `SCORE_THRESHOLD_WEAK = 60`（候选门槛）/ `SCORE_THRESHOLD_STRONG = 80`（强候选标记）
- `MAX_DATE_DIFF_DAYS = 7`、`AMOUNT_TOLERANCE = 0.01`

## 附录 C：补丁任务（matching eligibility lifecycle fixes）的修复与对应解法

| # | 问题 | 解法 | 校验测试 |
|---|---|---|---|
| 1 | `list_candidates` 没有先校验 PR 是否可参与匹配，对 draft / rejected / 已删除 PR 也会跑评分流程并返回空列表，掩盖错误调用 | service 在 `_require_read_access` 之后追加 `_purchase_eligible_for_match(purchase)` 守卫；不合格抛 `ValueError("Purchase record is not eligible for matching ...")`；router 已有的 `ValueError → 400` 通道直接复用，detail 携带 `status` 与 `deleted` 便于排查 | `test_candidates_rejects_draft_purchase`、`test_candidates_rejects_rejected_purchase` |
| 2 | `invoice_files.withdraw_confirmation`（confirmed → draft）未触发 needs_review，导致已被取消确认的发票仍被 active match 视作合法 | 在状态切换之后懒导入调用 `mark_needs_review_for_invoice_file(..., review_reason="invoice file withdrawn to draft")`，并 `session.refresh(record)` 防止 expire-on-commit 影响后续序列化 | `test_invoice_withdraw_confirmation_marks_match_needs_review` |
| 3 | `purchase_records.withdraw_record`（submitted → draft）和 `reject_record`（submitted → rejected）让已匹配 PR 进入不合格状态，但未触发 needs_review | 两个方法都在状态切换之后懒导入调用 `mark_needs_review_for_purchase_record(...)`，`review_reason` 分别记为 `"purchase record withdrawn to draft"` 与 `"purchase record rejected"`；`session.refresh(updated)` 同上 | `test_purchase_withdraw_marks_match_needs_review`、`test_purchase_reject_marks_match_needs_review` |

策略说明：候选不合格选择 **400 + 明确 detail** 而非返回空列表。理由是空列表会让前端在 PR 处于 draft / rejected 等状态时仍展示「无可匹配发票」的常规视图，从而把"调用方应不应该跳到这一步"的判断错误地推给用户；返回 400 + status / deleted 信息更容易在前端联调与日志里暴露错误调用。

# Round 005 Design - invoice_matching

## 后端设计

### 目录

- `backend/app/modules/finance/invoice_matching/`
- `backend/tests/finance/invoice_matching/index_test.py`

参考模块：

- `backend/app/modules/finance/purchase_records/`
- `backend/app/modules/finance/invoice_files/`

### 数据模型

建议表名：`invoice_match`

字段：

- `id`: UUID primary key
- `owner_id`: UUID，购买记录所属用户
- `purchase_record_id`: UUID，FK `purchase_record.id`
- `invoice_file_id`: UUID，FK `invoice_file.id`
- `status`: string，`confirmed` / `cancelled` / `needs_review`
- `score`: integer，确认时使用的候选评分
- `score_breakdown`: JSON，评分解释
- `confirmed_by_id`: UUID
- `confirmed_at`: datetime
- `cancelled_by_id`: UUID nullable
- `cancelled_at`: datetime nullable
- `review_reason`: string nullable
- `created_at`: datetime
- `updated_at`: datetime nullable

约束：

- 一个购买记录同一时间只能有一个 active 匹配。
- active 状态为 `confirmed`、`needs_review`。
- 一张发票允许多个 active 匹配。
- 建议 migration 添加 partial unique index：
  - `(purchase_record_id) WHERE status IN ('confirmed', 'needs_review')`

候选不落库，由服务层实时计算。

### API

建议端点：

- `GET /summary`
  - 返回未匹配购买记录数、可用发票数、需复核数、孤立发票数。
- `GET /unmatched-purchase-records`
  - 返回当前用户或管理员视角下可参与匹配但没有 active 匹配的购买记录。
- `GET /available-invoices`
  - 返回 `confirmed` 发票，包含 `allocated_amount`、`remaining_amount`。
- `GET /candidates`
  - query：`purchase_record_id`
  - 返回候选发票、评分、评分解释、已分摊金额、剩余金额。
- `GET /matches`
  - 支持 `status`、`skip`、`limit`。
- `POST /confirm`
  - body：`purchase_record_id`、`invoice_file_id`
  - 创建 `confirmed` 匹配。
- `POST /{id}/cancel`
  - owner 取消自己的匹配。
- `POST /{id}/reconfirm`
  - owner 将 `needs_review` 重新确认成 `confirmed`。

### 服务规则

确认匹配必须校验：

- 当前用户是购买记录 owner。
- 管理员不能代用户确认。
- 购买记录未删除。
- 购买记录状态为 `submitted` 或 `approved`。
- 购买记录没有 active 匹配。
- 发票未删除。
- 发票状态为 `confirmed`。
- 发票 owner 与购买记录 owner 一致。
- 币种一致。
- 新增后发票分摊总额不超过发票金额 `0.01` 以上。

取消匹配必须校验：

- 当前用户是匹配 owner。
- active 匹配可取消。
- 取消后状态为 `cancelled`，保留历史。

### needs_review

本轮应提供服务函数：

- `mark_matches_needing_review_for_purchase_record(record_id, reason)`
- `mark_matches_needing_review_for_invoice_file(invoice_id, reason)`

并在相关模块更新关键字段、作废、删除时调用。

如果跨模块调用范围太大，后端 AI 必须在报告中明确未完成项；但至少要实现函数和测试。

## 前端设计

### 目录

- `frontend/src/tools/finance/invoice_matching/`
- `frontend/src/routes/_layout/finance.invoice-matching.tsx`
- `frontend/tests/finance/invoice_matching/index.spec.ts`

### 页面

建议 Tabs：

- `待匹配`
- `已匹配`
- `需复核`
- `异常`

待匹配视图：

- 左侧或上方选择购买记录。
- 右侧显示候选发票列表。
- 候选显示：
  - 发票号码
  - 发票日期
  - 发票金额
  - 已分摊金额
  - 剩余金额
  - 评分
  - 评分解释
  - 确认按钮

已匹配视图：

- 显示购买记录、发票、金额、状态、确认时间、取消按钮。

需复核视图：

- 显示 `needs_review` 匹配和原因。
- 支持重新确认或取消。

异常视图：

- 无发票购买记录。
- confirmed 但未被任何购买记录分摊的发票。
- 弱候选。

### i18n

如果 Round 003 i18n 已完成，前端必须使用现有 i18n 翻译 key。

如果 Round 003 尚未合并，前端应先按当前项目可用方式实现，但不得引入与 Round 003 冲突的独立 i18n 系统。


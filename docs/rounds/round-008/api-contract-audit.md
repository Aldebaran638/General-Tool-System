# Round 008 reimbursement_exports — API 契约审计

日期：2026-04-26
执行者：后端 AI 1（审计角色）→ 后端 AI（FIX-002 修复者，2026-04-26 同日）
是否修改代码：**审计阶段：否；FIX-002 阶段：是（修代码 + 测试，不动 schema/迁移）。详见 §10。**

---

## 0. 后续状态总览（FIX-002 后，2026-04-26）

| 审计发现 | 严重 | 状态 |
|----------|------|------|
| URL 前缀缺 `/finance/` 段（§2.1 / §4.1） | 🔴 阻塞前端 | ✅ 已修复（详见 §10.1 / `backend-report.md` §10.1） |
| `retention_days` 忽略全局设置（§4.3） | 🔴 阻塞需求 | ✅ 已修复（详见 §10.2 / `backend-report.md` §10.2） |
| `/records` count 与 data 在 `exported` 过滤下不一致（§4.4） | 🟠 影响分页 | ✅ 已修复（详见 §10.3 / `backend-report.md` §10.3） |
| `/history` 缺设计要求的过滤参数（§4.5） | 🟠 影响功能 | ✅ 已修复（详见 §10.4 / `backend-report.md` §10.4） |
| 日期参数命名 `start_date/end_date` vs 设计 `purchase_date_from/_to`（§4.2） | 🟡 文档 | 暂保留实现命名，详见 §11 备注 |
| `purge_ids` 多字段（§4.6）/ `download_url` 缺字段（§4.7） | 🟢 可忽略 | 维持现状 |

下文 §3（API 契约表）、§5（前端对接示例）、§6（验证结果）已按 FIX-002 后的状态更新。§2 / §4 保留原审计描述并加上「（已修复 — 见 §10）」标注，方便回溯。

---

## 1. 审计输入物路径

| 类别 | 路径 |
|------|------|
| 需求 | `docs/rounds/round-008/requirements.md` |
| 设计 | `docs/rounds/round-008/design.md` |
| 测试计划 | `docs/rounds/round-008/test-plan.md` |
| 任务拆解 | `docs/rounds/round-008/tasks.md` |
| 后端报告 | `docs/rounds/round-008/backend-report.md` |
| Router | `backend/app/modules/finance/reimbursement_exports/router.py` |
| Schemas | `backend/app/modules/finance/reimbursement_exports/schemas.py` |
| Service | `backend/app/modules/finance/reimbursement_exports/service.py` |
| Models | `backend/app/modules/finance/reimbursement_exports/models.py` |
| Backend 测试 | `backend/tests/finance/reimbursement_exports/index_test.py` |

辅助：通过 `app.main.app.routes` 列出真实 mount 路径（仅审计读取，未改动代码）。

---

## 2. ⚠️ 关键路径偏差（前端必须先于其余对齐） — ✅ FIX-002 已修复

> 本节描述的是审计当时（2026-04-26 上午）观察到的状态；FIX-002（同日下午）后路径已对齐设计文档，详见 §10.1。

### 2.1 实际 prefix 与设计 / 任务派发不一致（已修复）

- 设计与本次任务派发约定的 prefix：`/api/v1/finance/reimbursement-exports`
- **审计当时实际 mount prefix：** `/api/v1/reimbursement-exports`（**没有 `/finance/` 段**）
- **FIX-002 后实际 mount prefix：** `/api/v1/finance/reimbursement-exports` ✅

实测路由列表（审计当时，运行时来自 `app.main.app.routes`，过滤 `reimbursement`）：

```
GET   /api/v1/reimbursement-exports/records
POST  /api/v1/reimbursement-exports/generate
GET   /api/v1/reimbursement-exports/history
GET   /api/v1/reimbursement-exports/settings
PUT   /api/v1/reimbursement-exports/settings
GET   /api/v1/reimbursement-exports/{export_id}
GET   /api/v1/reimbursement-exports/{export_id}/download
POST  /api/v1/reimbursement-exports/purge-expired-files
```

**FIX-002 后实测路由列表**（修复后通过 pytest 65 处 URL 全部命中验证）：

```
GET   /api/v1/finance/reimbursement-exports/records
POST  /api/v1/finance/reimbursement-exports/generate
GET   /api/v1/finance/reimbursement-exports/history
GET   /api/v1/finance/reimbursement-exports/settings
PUT   /api/v1/finance/reimbursement-exports/settings
GET   /api/v1/finance/reimbursement-exports/{export_id}
GET   /api/v1/finance/reimbursement-exports/{export_id}/download
POST  /api/v1/finance/reimbursement-exports/purge-expired-files
```

兄弟工具的对照（FIX-002 后，全部统一在 `/api/v1/finance/` 下）：

```
/api/v1/finance/dashboard
/api/v1/finance/invoice-files
/api/v1/finance/invoice-matching
/api/v1/finance/purchase-records
/api/v1/finance/reimbursement-exports/...   ← 已对齐
```

`router.py` 原使用 `APIRouter(prefix="/reimbursement-exports", ...)`，与兄弟工具 `invoice_files` 等所用的 `prefix="/finance/<tool>"` 风格不一致。**审计当时结论：前端如果按 `design.md` 直接拼 `/api/v1/finance/reimbursement-exports/...`，会全部 404。**

**FIX-002 后（已修复）**：`router.py` 改为 `APIRouter(prefix="/finance/reimbursement-exports", ...)`；旧路径 `/api/v1/reimbursement-exports` 已停止挂载（不双挂载）。下文「3. API 契约表」全部以新路径为准。

> 处置建议（FIX-002 已落地）：后端 `router.py` 已补 `/finance` 段；`design.md` 中的 URL 与实现一致，无需文档变更。

下文「3. API 契约表」全部以 **FIX-002 后** 的实际路径为准；同时在「4. 与设计偏差」第 4.1 节再次重点标注此事。

---

## 3. API 契约表（按实际行为输出）

通用约定：
- 所有端点权限：登录 + `current_user.is_superuser=True`。任一不满足→ 401（未登录）或 403（已登录非管理员），由 router 层统一抛 `HTTPException(403, "Admin access required.")`。
- 401 来源：FastAPI 依赖 `CurrentUser` 解析失败时抛出。
- 时间字段全部 UTC，序列化为 ISO 8601 带时区。

---

### 3.1 `GET /api/v1/finance/reimbursement-exports/records`

**用途**：列出可导出的购买记录（已批准 + 已确认匹配 + 关联发票未删除/未作废），并附带是否已被某次导出选中过的元数据。

**Query 参数**：

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `skip` | `int >= 0` | 否，默认 0 | 分页偏移。 |
| `limit` | `int 1..1000` | 否，默认 100 | 分页上限；超出 422。 |
| `start_date` | `string YYYY-MM-DD` | 否 | `purchase_date >= start_date`；非法格式 422。 |
| `end_date` | `string YYYY-MM-DD` | 否 | `purchase_date <= end_date`；非法格式 422。 |
| `category` | string | 否 | 大类常量（`transportation` / `meals_entertainment` / `vehicle` / `other_project`），后端不强校验枚举。 |
| `subcategory` | string | 否 | 小类。 |
| `currency` | string | 否 | 三字母币种。 |
| `owner_id` | UUID | 否 | 限定到指定用户。 |
| `exported` | `all` / `exported` / `not_exported` | 否 | 不传等价于 `all`。FastAPI 通过 `pattern` 校验，非法值 422。 |
| `q` | string | 否 | 关键字（具体匹配范围由 repository 决定，建议前端覆盖 `order_name` 与 `note`）。 |

**Request body**：无。

**Response body** — `RecordsPublic`：

```ts
{
  count: number,            // 注意：见 §4.4 关于 exported 过滤下 count 与 data.length 的口径偏差
  data: PurchaseRecordWithExportInfo[]
}

// PurchaseRecordWithExportInfo
{
  id: UUID,
  owner_id: UUID,
  purchase_date: "YYYY-MM-DD",
  amount: string,                 // Decimal serialized as string
  currency: string,
  order_name: string,
  category: string,
  subcategory: string | null,
  note: string | null,
  status: string,
  created_at: ISO8601 | null,
  invoice_file: {                  // 来自 invoice_match 关联的 invoice_file 摘要；不可能为 null（已 JOIN 过滤）
    id: UUID,
    invoice_number: string,
    invoice_date: "YYYY-MM-DD",
    invoice_amount: string,
    currency: string,
    seller: string
  } | null,
  exported: boolean,
  latest_exported_at: ISO8601 | null,
  latest_exported_by: UUID | null
}
```

**主要错误码**：

- 401：未登录。
- 403：非管理员。
- 422：`limit` 超界、`start_date` / `end_date` 非 ISO、`exported` 不在 `all|exported|not_exported`。

**前端使用建议**：
- 表格列至少应展示 `purchase_date / owner_id / category / subcategory / amount / currency / order_name / invoice_file.invoice_number / exported / latest_exported_at`。
- 「已导出」过滤是前端的「是否已导出」开关；`exported=exported` / `not_exported` 二选一，`all` 等价于不传。
- ✅ FIX-002 后：`count` 与 `data` 在 `exported` 过滤下保持一致（同一 SQL 过滤树 + `OFFSET/LIMIT`），前端可直接以 `count` 计算总页数。详见 §4.4。

---

### 3.2 `POST /api/v1/finance/reimbursement-exports/generate`

**用途**：基于一组 purchase_record_ids，生成 Excel 并落盘 + 写入历史 + 写入 items 快照。

**Request body** — `GenerateRequest`：

```ts
{
  purchase_record_ids: UUID[],     // 必填，至少 1 条；空列表 422
  department?:        string | null,    // <= 255 chars
  business_unit?:     string | null,    // <= 255 chars
  reimburser?:        string | null,    // <= 255 chars
  reimbursement_date?: "YYYY-MM-DD" | null,
  retention_days?:    int (1..365) | null  // 可选；不传 → 走 /settings 全局值；显式传值仅覆盖本次（FIX-002 后语义）
}
```

> ✅ FIX-002 后：`retention_days` 改为 `int | None`，**不传时走全局设置 → 默认 1 天**；显式传值仅覆盖本次导出。详见 §4.3。

**Response body** — `ReimbursementExportPublic`：

```ts
{
  id: UUID,
  created_by_id: UUID,
  created_at: ISO8601,
  department: string | null,
  business_unit: string | null,
  reimburser: string | null,
  reimbursement_date: "YYYY-MM-DD" | null,
  currency: string | null,
  total_amount: string,             // Decimal serialized as string
  item_count: number,
  original_filename: string | null,
  stored_filename: string | null,
  file_path: string | null,
  mime_type: string | null,         // application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
  file_size: number | null,
  file_expires_at: ISO8601 | null,
  file_deleted_at: ISO8601 | null   // 刚生成时为 null
}
```

> ⚠️ 实际响应**没有** `download_url` 字段（design.md 给的样例里有）。前端要自己拼：`/api/v1/finance/reimbursement-exports/{id}/download`。

**主要错误码**：

- 401 / 403：见通用约定。
- 422：
  - `purchase_record_ids` 为空。
  - 任一 ID 不存在 / 不满足 eligibility（status=approved + 已确认匹配 + 发票未删/未作废）。整批拒绝，detail 中列出未通过的 IDs。
  - 命中多币种。detail 形如 `Multiple currencies selected: {'CNY', 'USD'}. Only one currency per export is allowed.`。
  - `retention_days` 越界（`< 1` 或 `> 365`）。
- 500：`Failed to build Excel file: ...`（openpyxl 阶段异常）。

**前端使用建议**：
- 提交前如果勾选里有 `exported = true` 的记录，**前端必须弹警告**（需求要求的「允许重复导出但前端必须警告」）。
- 提交前对比 `currency`，如果发现选中行混合多币种，前端可以不发请求直接拦截；即便直发，后端也会 422，detail 中含 `Multiple currencies` 关键字。
- `retention_days` 在生成时不必让用户填，前端建议**不传**（让后端用默认值），由「设置」入口统一调；若产品要求每次生成可单独覆盖，则保留为高级选项，并把范围限定到 1..365。

---

### 3.3 `GET /api/v1/finance/reimbursement-exports/history`

**用途**：按时间倒序的导出历史。

**Query 参数**（FIX-002 后已补齐设计要求的过滤参数）：

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `skip` | `int >= 0` | 否，默认 0 | 分页偏移。 |
| `limit` | `int 1..1000` | 否，默认 100 | 分页上限；超出 422。 |
| `created_at_from` | ISO 8601 datetime | 否 | `created_at >= from`；FastAPI 自动 ISO-8601 解析。 |
| `created_at_to` | ISO 8601 datetime | 否 | `created_at <= to`。 |
| `created_by_id` | UUID | 否 | 按生成者过滤。 |
| `currency` | string | 否 | 按币种过滤（与 export.currency 精确匹配）。 |

> ✅ FIX-002 后：上述 4 个过滤参数已实装；`count` 与 `data` 共享同一过滤树，分页一致。详见 §4.5。

**Request body**：无。

**Response body** — `ReimbursementExportsPublic`：

```ts
{
  count: number,
  data: ReimbursementExportPublic[]   // 见 §3.2 同名类型
}
```

**主要错误码**：401 / 403 / 422（limit 越界）。

**前端使用建议**：
- 表格列至少展示 `created_at / created_by_id / department / reimburser / reimbursement_date / item_count / currency / total_amount / file_expires_at / file_deleted_at`。
- `file_deleted_at != null` 表示物理文件已被清理，下载按钮应该置灰，提示「文件已过期，可重新生成」；`file_expires_at < now` 同样需要置灰（或直接隐藏下载）。

---

### 3.4 `GET /api/v1/finance/reimbursement-exports/settings`

**用途**：读取报销导出全局设置。

**Query / Body**：无。

**Response**：

```ts
{ retention_days: number }
```

**错误码**：401 / 403。

---

### 3.5 `PUT /api/v1/finance/reimbursement-exports/settings`

**用途**：更新保留天数。

**Request body** — `SettingsUpdate`：

```ts
{ retention_days?: int (1..365) | null }
```

`retention_days` 为 `null` 或缺省时，后端不更新（但仍返回 200 + 当前值）。

**Response**：与 §3.4 一致。

**错误码**：401 / 403 / 422（越界）。

---

### 3.6 `GET /api/v1/finance/reimbursement-exports/{export_id}`

**用途**：查看导出详情，含 items 快照。**即使 `file_deleted_at` 已置位（物理文件已清理），仍可读**——历史不删。

**Query / Body**：无。`export_id` 必须是 UUID。

**Response** — `ReimbursementExportDetailPublic` = `ReimbursementExportPublic` + `items: ReimbursementExportItemPublic[]`：

```ts
// ReimbursementExportItemPublic
{
  id: UUID,
  export_id: UUID,
  purchase_record_id: UUID,
  invoice_file_id: UUID | null,
  invoice_match_id: UUID | null,
  document_number: number,
  purchase_date: "YYYY-MM-DD",
  amount: string,                 // Decimal as string
  currency: string,
  category: string,
  subcategory: string | null,
  order_name: string,
  remark: string | null,
  description_snapshot: string | null,
  department_snapshot: string | null,
  created_at: ISO8601
}
```

**错误码**：401 / 403 / 404（detail：`Export not found.`） / 422（path UUID 非法）。

**前端使用建议**：详情页可用 `items[].document_number` 作为单据编号显示；若需要展示「单据编号范围」（设计文档里的 `1-22`、`1-2,5,7-9`），前端要自己压缩，**后端不预压缩**返回。

---

### 3.7 `GET /api/v1/finance/reimbursement-exports/{export_id}/download`

**用途**：下载未过期且物理文件存在的 Excel。

**Query / Body**：无。

**Response（成功）**：

- HTTP 200。
- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`。
- `Content-Disposition: attachment; filename="<original_filename or stored_filename or export.xlsx>"` —— 由 FastAPI `FileResponse` 自动设置。
- Body：xlsx 二进制流。

**Response（失败）**：

| 条件 | Status | Detail |
|------|--------|--------|
| `export` 不存在 | 404 | `Export not found.` |
| `file_deleted_at IS NOT NULL` | 410 | `File expired. Please regenerate.` |
| `file_expires_at < now(utc)` | 410 | `File expired. Please regenerate.` |
| `file_path` 为空 | 410 | `File expired. Please regenerate.` |
| 物理文件不存在 | 410 | `File expired. Please regenerate.` |

**前端使用建议**：详见 §5.2（download 一定要走 `fetch` + `Authorization` header，不能用 `<a href>` + token query）。

---

### 3.8 `POST /api/v1/finance/reimbursement-exports/purge-expired-files`

**用途**：清理所有 `file_expires_at < now()` 的导出物理文件，**不删历史和 items**。

**Query / Body**：无。

**Response**：

```ts
{
  purged_count: number,
  purged_ids:   UUID[]      // 每个被清理的 export id
}
```

> 设计文档里只写了 `purged_count`，实际多了一个 `purged_ids`（非破坏性扩展，前端可直接用，也可忽略）。详见 §4.6。

**错误码**：401 / 403。

**前端使用建议**：见 §5.6。

---

## 4. 与设计偏差项

> ⚠️ 标记 = 前端会撞 / 后端建议正式修；ℹ️ 标记 = 偏差但不影响功能。

### 4.1 ✅ URL prefix 缺 `/finance/` 段（FIX-002 已修复）

详见 §2.1 与 §10.1。`router.py` 的 `prefix` 已改为 `/finance/reimbursement-exports`，前端按 design.md 直接拼接的 URL 现可正常命中。**未双挂载**，旧路径 `/api/v1/reimbursement-exports` 已停止挂载。

### 4.2 ⚠️ records 的日期参数名

- 设计：`purchase_date_from` / `purchase_date_to`。
- 实际：`start_date` / `end_date`。
- 影响：前端类型签名要按实际写。设计文档与实现不一致；建议二选一统一。

### 4.3 ✅ generate `retention_days` 已回落到全局设置（FIX-002 已修复）

- 设计原意：保留天数由全局 `app_setting.reimbursement_export_retention_days` 决定；管理员通过 PUT /settings 调整。
- **审计当时实际**：`GenerateRequest.retention_days` 默认值是常量 `DEFAULT_RETENTION_DAYS`（不是来自 settings），且 `service.generate_export` 计算 `file_expires_at` 时**用的是请求体的值**（`service.py`：`retention_days = data_in.retention_days or DEFAULT_RETENTION_DAYS`）。**全局设置的值在生成阶段被忽略**。
- ✅ **FIX-002 后**：
  - `GenerateRequest.retention_days: int | None = None`，可省略。
  - `service.generate_export` 改为：
    ```python
    retention_days = (
        data_in.retention_days
        if data_in.retention_days is not None
        else get_setting_int(session, SETTING_RETENTION_DAYS, DEFAULT_RETENTION_DAYS)
    )
    ```
    不传 → 走 `app_setting.reimbursement_export_retention_days`；该 key 也不存在则退到 `DEFAULT_RETENTION_DAYS=1`。
  - 显式传值仍可覆盖（保留作为「单次导出高级选项」的能力），范围 1..365 仍由 Pydantic 校验，越界 422。
- 新增测试：`test_generate_uses_settings_retention_when_omitted`、`test_generate_explicit_retention_days_overrides_settings`。详见 `backend-report.md` §10.2。

### 4.4 ✅ `GET /records` 的 `count` 与 `data` 已对齐（FIX-002 已修复）

- **审计当时实际行为**（`service.py:65-127`）：
  1. `count = count_eligible_records(session, filters)` —— 这是 **未应用 exported 过滤** 的总数。
  2. `get_eligible_records_by_ids_with_filter` 内部最多取 10000 行，再在 Python 端按 `exported=exported|not_exported` 过滤、再切片返回 `paged`。
- 后果：当 `exported=exported` 或 `not_exported` 时返回的 `count` 是过滤前总数，`data` 是过滤后当前页 → 翻页不一致；且 >10000 行被切尾。
- ✅ **FIX-002 后**：
  - `_build_eligible_base` 在 `filters.exported in ("exported", "not_exported")` 时挂上 `EXISTS` / `NOT EXISTS` 子查询，把过滤下推到 SQL：
    ```python
    exported_subq = (
        select(ReimbursementExportItem.id)
        .where(ReimbursementExportItem.purchase_record_id == PurchaseRecord.id)
    )
    stmt = stmt.where(exported_subq.exists())   # 或 ~exported_subq.exists()
    ```
  - `service.read_records` 直接调 `count_eligible_records(filters)` + `list_eligible_records(filters, skip, limit)` —— 两边走的是同一棵基础查询树，自然一致。
  - 删除了 `get_eligible_records_by_ids_with_filter` 与 10000 行硬上限；分页完全交给 SQL `OFFSET / LIMIT`。
- 新增测试：`test_records_exported_count_matches_data`、`test_records_exported_pagination_consistent_with_count`。详见 `backend-report.md` §10.3。

### 4.5 ✅ history 已补齐设计要求的过滤参数（FIX-002 已修复）

- 设计：`created_at_from` / `created_at_to` / `created_by_id` / `currency`。
- **审计当时实际**：仅 `skip` / `limit`。
- ✅ **FIX-002 后**：
  - `router.py` `read_history` 增加 4 个 query 参数；`datetime` 由 FastAPI 自动 ISO 8601 解析。
  - `repository.py` 抽取 `_apply_history_filters`，`count_exports` / `list_exports` 共用，count/data 语义一致。
- 新增测试：`test_history_filter_by_currency`、`test_history_filter_by_created_by_id`、`test_history_filter_by_created_at_range`。详见 `backend-report.md` §10.4。

### 4.6 ℹ️ purge 响应多了 `purged_ids`

非破坏性扩展。前端可以选择展示「本次清理了哪些导出」；不需要也可以忽略。

### 4.7 ℹ️ generate 响应没有 `download_url` / `filename` 字段

- 设计示例：

  ```json
  { "id": "uuid", "filename": "...", "download_url": "..." }
  ```

- 实际：返回 `ReimbursementExportPublic`，包含 `id` / `stored_filename` / `original_filename` 等，但没有独立的 `download_url`。
- 影响：前端要自己拼 `${API_V1}/reimbursement-exports/${id}/download`，不依赖后端返回的字符串。可接受。

### 4.8 ℹ️ GenerateRequest 字段名命名

- 设计：`purchase_record_ids`。
- 实际：`purchase_record_ids`。
- ✅ 一致。

### 4.9 ℹ️ 表头字段可空性

- 设计：`department` / `business_unit` / `reimburser` / `reimbursement_date` 全部非必填。
- 实际：`Optional` + `default=None`，`max_length=255`。
- ✅ 一致。

### 4.10 ℹ️ records 返回字段（重点核对项）

- 设计要求返回：`invoice_file` / `exported` / `latest_exported_at` / `latest_exported_by`。
- 实际：`PurchaseRecordWithExportInfo` 全部包含。
- ✅ 一致。`invoice_file` 是 `InvoiceFileBriefPublic`（见 §3.1）。

### 4.11 ℹ️ settings 表面

- 设计：仅暴露 `retention_days`。
- 实际：`SettingsResponse` 仅 `retention_days`；`SettingsUpdate` 仅 `retention_days`。
- ✅ 一致。

### 4.12 ℹ️ download 410 行为

- 设计：过期 / 已清理返回 410。
- 实际：见 §3.7 详细分支表，全部命中 410，且 detail 文案统一为 `File expired. Please regenerate.`。
- ✅ 一致；甚至比设计更扎实（覆盖了 `file_path` 缺失、物理文件不存在两种）。

### 4.13 ℹ️ 普通用户 forbidden

- 设计：普通用户对生成 / 设置 / 历史 / 清理无权。
- 实际：8 个端点全部命中 `is_superuser` 检查；测试覆盖了普通用户访问每个端点 → 403。
- ✅ 一致。

---

## 5. 前端对接注意事项

### 5.1 TypeScript 类型建议（直接复制即可对齐当前实现）

```ts
// 与实际 schema 1:1 对齐
export type UUID = string;
export type ISODateTime = string; // ISO8601, UTC
export type ISODate = string;     // YYYY-MM-DD
export type DecimalStr = string;  // backend serializes Decimal as string

export interface InvoiceFileBrief {
  id: UUID;
  invoice_number: string;
  invoice_date: ISODate;
  invoice_amount: DecimalStr;
  currency: string;
  seller: string;
}

export interface PurchaseRecordWithExportInfo {
  id: UUID;
  owner_id: UUID;
  purchase_date: ISODate;
  amount: DecimalStr;
  currency: string;
  order_name: string;
  category: string;
  subcategory: string | null;
  note: string | null;
  status: string;
  created_at: ISODateTime | null;
  invoice_file: InvoiceFileBrief | null;
  exported: boolean;
  latest_exported_at: ISODateTime | null;
  latest_exported_by: UUID | null;
}

export interface RecordsPublic {
  count: number;
  data: PurchaseRecordWithExportInfo[];
}

export type ExportedFilter = "all" | "exported" | "not_exported";

export interface RecordsQuery {
  skip?: number;
  limit?: number;          // 1..1000
  start_date?: ISODate;    // ⚠️ 不是 purchase_date_from
  end_date?: ISODate;      // ⚠️ 不是 purchase_date_to
  category?: string;
  subcategory?: string;
  currency?: string;
  owner_id?: UUID;
  exported?: ExportedFilter;
  q?: string;
}

export interface GenerateRequest {
  purchase_record_ids: UUID[];
  department?: string | null;
  business_unit?: string | null;
  reimburser?: string | null;
  reimbursement_date?: ISODate | null;
  retention_days?: number | null;  // 1..365；不传 → 走全局 /settings 的值（FIX-002 后语义）
}

export interface HistoryQuery {
  skip?: number;
  limit?: number;             // 1..1000
  created_at_from?: ISODateTime;  // ISO 8601
  created_at_to?: ISODateTime;
  created_by_id?: UUID;
  currency?: string;
}

export interface ReimbursementExportPublic {
  id: UUID;
  created_by_id: UUID;
  created_at: ISODateTime;
  department: string | null;
  business_unit: string | null;
  reimburser: string | null;
  reimbursement_date: ISODate | null;
  currency: string | null;
  total_amount: DecimalStr;
  item_count: number;
  original_filename: string | null;
  stored_filename: string | null;
  file_path: string | null;       // 注意：这是后端内部相对路径，不要拼到前端 URL
  mime_type: string | null;
  file_size: number | null;
  file_expires_at: ISODateTime | null;
  file_deleted_at: ISODateTime | null;
}

export interface ReimbursementExportItemPublic {
  id: UUID;
  export_id: UUID;
  purchase_record_id: UUID;
  invoice_file_id: UUID | null;
  invoice_match_id: UUID | null;
  document_number: number;
  purchase_date: ISODate;
  amount: DecimalStr;
  currency: string;
  category: string;
  subcategory: string | null;
  order_name: string;
  remark: string | null;
  description_snapshot: string | null;
  department_snapshot: string | null;
  created_at: ISODateTime;
}

export interface ReimbursementExportDetailPublic
  extends ReimbursementExportPublic {
  items: ReimbursementExportItemPublic[];
}

export interface ReimbursementExportsPublic {
  count: number;
  data: ReimbursementExportPublic[];
}

export interface SettingsResponse  { retention_days: number; }
export interface SettingsUpdate    { retention_days?: number | null; }

export interface PurgeResponse {
  purged_count: number;
  purged_ids: UUID[];   // 设计未列，实测存在
}
```

### 5.2 ⚠️ download 必须用 `fetch` + `Authorization` header

直接 `<a href="/api/v1/finance/reimbursement-exports/{id}/download">` 走不了——FastAPI 的鉴权依赖 `Authorization: Bearer ...` header，浏览器原生跳转不会带。**绝对不要把 token 放在 URL 里。**

推荐写法（与项目其他工具一致）：

```ts
async function downloadExport(id: UUID) {
  const resp = await fetch(`/api/v1/finance/reimbursement-exports/${id}/download`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (resp.status === 410) {
    showToast("文件已过期，可重新生成");
    return;
  }
  if (!resp.ok) throw new Error(`Download failed: ${resp.status}`);
  const blob = await resp.blob();
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href = url;
  // Content-Disposition 里的 filename 也可以解析；为简化前端直接用本地文件名即可。
  a.download = `reimbursement_${id}.xlsx`;
  a.click();
  URL.revokeObjectURL(url);
}
```

### 5.3 `exported` 过滤 → UI 对应关系

| 前端控件 | `exported` 值 | 行为 |
|----------|--------------|------|
| 默认 / 「全部」 | 不传（或 `all`） | 全部 eligible 记录。 |
| 「未导出」单选 | `not_exported` | 只看尚未被任何导出选中的记录。 |
| 「已导出」单选 | `exported` | 只看曾被某次导出选中过的记录（`latest_exported_at` 必非空）。 |

> ✅ FIX-002 后：当过滤为 `exported`/`not_exported` 时 `count` 已与 `data` 对齐（同一 SQL 过滤树）。前端可直接以 `count` 计算总页数与「共 N 条」展示，无需「下一页存在性探测」的兜底逻辑。

### 5.4 多币种错误展示

前端两层防护：

1. **本地拦截**（首选）：勾选时维护 `selectedCurrencies = new Set(records.map(r => r.currency))`，`size > 1` 时禁用「生成」按钮 + 提示「不允许跨币种导出，请分别导出」。
2. **后端兜底**：直接发请求时，后端会 422，`detail` 形如 `Multiple currencies selected: {'CNY', 'USD'}. Only one currency per export is allowed.`。前端解析时只需匹配关键字 `Multiple currencies` 就能展示成自己的本地化文案。

### 5.5 已导出记录再次勾选 → 警告但允许

需求要求：「允许重复导出已导出过的购买记录，但前端必须弹出警告」。建议交互：

1. 用户点「生成」按钮。
2. 在调用 `/generate` 之前，前端遍历当前选中：若任意 `r.exported === true` → 弹确认框，列出这些记录的 `order_name` + `latest_exported_at`，让用户「确认重新导出」或「取消」。
3. 用户确认后再发请求。
4. 后端不会拒绝（设计与实现一致），所以这个警告完全是前端职责。

### 5.6 `purge-expired-files` 按钮放哪？

**建议放设置弹窗里**，作为 retention_days 表单旁边的「立即清理过期文件」按钮：
- 业务上和 retention_days 同源（什么算「过期」由它定）；
- 是低频破坏性操作，不适合放在常规工具栏；
- 设置弹窗本身已是「管理员才看见」入口；
- 调用后用 `purged_count` 反馈：>0 时提示「已清理 N 个过期文件」，=0 时提示「当前没有可清理文件」；如果产品需要展开列表，可用 `purged_ids` 配合历史表的 `file_deleted_at` 去染色。

不建议放在历史页表格上方，避免与单条「下载」按钮的视觉权重错位。

---

## 6. 验证命令与结果

### 6.1 必须执行的命令

```bash
docker compose exec backend pytest tests/finance/reimbursement_exports/index_test.py -q
docker compose exec backend pytest tests/finance/ -q
docker compose exec backend alembic current
```

### 6.2 实际输出（FIX-002 后）

**pytest（reimbursement_exports）**：

```
59 passed, 3 warnings in 5.46s
```

**pytest（finance 全套回归）**：

```
207 passed, 3 warnings in 10.67s
```

**alembic**：

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
85dea52b034c (head)
```

迁移头是 `85dea52b034c_add_app_setting_and_reimbursement_*.py`，**FIX-002 阶段未触动 schema/迁移**，与审计当时一致；`app_setting` / `reimbursement_export` / `reimbursement_export_item` 三张表均已建。

### 6.3 审计当时（FIX-002 前）的输出留档

仅供回溯。FIX-002 只动 application 层与测试层，故 alembic head 一致。

```
# pytest 当时
45 passed, 3 warnings in 3.78s

# alembic 当时
85dea52b034c (head)
```

### 6.4 辅助审计动作（只读，非必须命令）

为确认 §2.1 的 prefix 偏差，运行了一条只读检查（**未改任何文件**）：

```bash
docker compose exec backend python -c "
from app.main import app
for route in app.routes:
    p = getattr(route, 'path', None)
    if p and 'reimbursement' in p:
        print(getattr(route, 'methods', None), p)
"
```

输出列在 §2.1。

---

## 7. 是否修改代码

**审计阶段：否；FIX-002 阶段：是（不动 schema / 不动 migration / 不动 frontend / 不动 skills）。**

### 7.1 审计阶段（2026-04-26 上午）

未修改任何 `backend/app/**`、`backend/tests/**`、`frontend/**`、`skills/**`、`alembic/**`、`pyproject.toml`、`uv.lock`、`.env`。
唯一新增文件：本报告 `docs/rounds/round-008/api-contract-audit.md`。

### 7.2 FIX-002 阶段（2026-04-26 下午）

修改范围严格限定在派发允许的路径内：

- `backend/app/modules/finance/reimbursement_exports/router.py`：prefix 改为 `/finance/reimbursement-exports`；`/history` 增加 4 个 datetime/UUID/string 过滤 query。
- `backend/app/modules/finance/reimbursement_exports/schemas.py`：`GenerateRequest.retention_days` 改为可选（`int | None`）。
- `backend/app/modules/finance/reimbursement_exports/service.py`：`generate_export` 实现 retention 二级回落；`read_records` 直接调 list/count；`read_history` 转发过滤参数；删除 `get_eligible_records_by_ids_with_filter` 的引用。
- `backend/app/modules/finance/reimbursement_exports/repository.py`：`_build_eligible_base` 加 EXISTS / NOT EXISTS 子查询；抽取 `_apply_history_filters` 共享给 `count_exports` / `list_exports`；删除 `get_eligible_records_by_ids_with_filter`。
- `backend/tests/finance/reimbursement_exports/index_test.py`：65 处 URL 替换 + 7 个新测试（retention fallback × 2、count/data 一致 × 2、history filters × 3）。
- `docs/rounds/round-008/backend-report.md`：新增 §10「BE-R008-FIX-002（前端阻塞修复）」。
- `docs/rounds/round-008/api-contract-audit.md`（本文件）：补 §0 总览、各偏差节标记 ✅ 已修复、§3 路径更新、§5 示例更新、§6 输出更新、§10 / §11 新章节。

**未触动**：alembic versions/、frontend/、skills/、其他后端模块、`pyproject.toml`、`uv.lock`、`.env`。`alembic current` head 仍为 `85dea52b034c`。

git 视角自检（FIX-002 后）：本轮新增 / 修改文件全部在上述清单内，未越界。

---

## 8. 风险清单（给前端 / 后端 R008 作者）

按严重程度从高到低（FIX-002 后状态）：

| # | 严重 | 说明 | 处置建议 / 当前状态 |
|---|------|------|---------------------|
| 1 | 🔴 阻塞前端 | URL prefix 缺 `/finance/`（§2.1 / §4.1） | ✅ FIX-002 已修复：`router.py` 改为 `prefix="/finance/reimbursement-exports"`，未双挂载，全部 65 处测试 URL 同步替换。 |
| 2 | 🔴 阻塞需求 | 全局 `retention_days` 设置在 generate 阶段被忽略（§4.3） | ✅ FIX-002 已修复：`GenerateRequest.retention_days` 改为可选，省略时走 `app_setting` → `DEFAULT_RETENTION_DAYS=1` 二级回落；显式值仅覆盖本次。 |
| 3 | 🟠 影响分页 | `exported` 过滤下 `count` 与 `data` 不一致（§4.4） | ✅ FIX-002 已修复：过滤下推为 SQL `EXISTS` / `NOT EXISTS` 子查询；`count_eligible_records` 与 `list_eligible_records` 共享 `_build_eligible_base`；同时移除 10000 行硬上限。 |
| 4 | 🟠 影响功能 | history 缺过滤参数（§4.5） | ✅ FIX-002 已修复：补齐 `created_at_from` / `created_at_to` / `created_by_id` / `currency`；`count_exports` / `list_exports` 共享 `_apply_history_filters`，分页一致。 |
| 5 | 🟡 文档 | records 日期参数命名（§4.2） | 维持实现 `start_date` / `end_date`，design.md 与之不一致；详见 §11。 |
| 6 | 🟢 可忽略 | purge 响应多 `purged_ids`、generate 没 `download_url`（§4.6 / §4.7） | 维持现状；前端按实际行为对接，TS 类型已在 §5.1 给出。 |

---

## 10. FIX-002 修复后状态总结（2026-04-26）

| 修复项 | 文件入口 | 关键变更 | 验证 |
|--------|----------|----------|------|
| **10.1 API 前缀** | `router.py` | `APIRouter(prefix="/finance/reimbursement-exports", ...)`；旧路径 `/api/v1/reimbursement-exports` 不再挂载（无双挂载） | 65 处测试 URL 命中 200/403/422/410；`app.routes` 已实测 |
| **10.2 retention 二级回落** | `schemas.py` / `service.py` | `retention_days: int \| None`；省略时 `get_setting_int(...)` → `DEFAULT_RETENTION_DAYS=1`；显式值覆盖本次 | `test_generate_uses_settings_retention_when_omitted` / `test_generate_explicit_retention_days_overrides_settings` |
| **10.3 records SQL 下推** | `repository.py` / `service.py` | `_build_eligible_base` 加 `EXISTS` / `NOT EXISTS`；删除 `get_eligible_records_by_ids_with_filter` 与 10000 行上限；`read_records` 直接用 `count + list` | `test_records_exported_count_matches_data` / `test_records_exported_pagination_consistent_with_count` |
| **10.4 history 过滤** | `router.py` / `repository.py` / `service.py` | 增加 `created_at_from / created_at_to / created_by_id / currency`；`_apply_history_filters` 共享给 count/list | `test_history_filter_by_currency` / `test_history_filter_by_created_by_id` / `test_history_filter_by_created_at_range` |

**累计测试（FIX-002 后）**：模块 59 通过 / 财务回归 207 通过 / `alembic current` = `85dea52b034c (head)`，迁移头与审计当时一致（未动 schema）。

**前端对齐建议（FIX-002 后已可直接采用）**：

1. URL 全部按 §3 表里的 `/api/v1/finance/reimbursement-exports/...` 拼。
2. `GET /records?exported=exported|not_exported` 时直接信任 `count`，正常分页。
3. 「设置 → 保留天数」更新后，下一次 `POST /generate`（不传 `retention_days`）将立即生效，无需前端额外补 retention 字段。
4. 「历史」表的过滤控件可直接对接 `created_at_from / _to / created_by_id / currency` 4 个 query。

---

## 11. 备注：日期参数命名（§4.2 妥协说明）

- 设计文档：`/records?purchase_date_from=&purchase_date_to=`
- 实现 + 测试 + 前端预期：`/records?start_date=&end_date=`

FIX-002 期间未改这一项，理由：
- 修改为设计命名会破坏 `backend/tests/finance/reimbursement_exports/index_test.py` 当前所有 records 过滤用例与已经写好的前端 TS 类型 (§5.1)，引发二次返工。
- 当前命名已被 `backend-report.md` §4 与本文件 §3.1 / §5.1 显式记录，对前端是有据可循的契约。
- 建议「以实现为准」更新 `design.md`，或留待后续轮次统一规范化。

后端没有再向前端暴露任何旧名称别名（无 `purchase_date_from/_to`），所以前端不需要兼容两套命名。

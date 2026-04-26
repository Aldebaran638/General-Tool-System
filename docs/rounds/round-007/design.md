# Round 007 Design - finance_dashboard

## 后端模块

建议路径：

```text
backend/app/modules/finance/dashboard/
```

文件结构：

```text
constants.py
schemas.py
repository.py
service.py
router.py
__init__.py
```

本轮不需要新增数据库表。

## API

### GET `/api/v1/finance/dashboard/summary`

返回当前用户视角的统计摘要。

普通用户：只统计自己的数据。  
管理员：统计全局数据。

响应结构建议：

```json
{
  "scope": "self",
  "purchase_records": {
    "total": 10,
    "unmatched": 3,
    "matched": 6,
    "deleted": 1
  },
  "invoice_files": {
    "total": 8,
    "unallocated": 2,
    "partially_allocated": 1,
    "fully_allocated": 4,
    "voided": 1
  },
  "matches": {
    "confirmed": 6,
    "needs_review": 1,
    "cancelled": 2
  }
}
```

### GET `/api/v1/finance/dashboard/pending`

返回待处理事项列表。

Query：

- `limit`，默认 20，最大 100。

响应结构建议：

```json
{
  "data": [
    {
      "type": "match_needs_review",
      "severity": "warning",
      "title": "匹配需要复核",
      "description": "购买记录金额或日期发生变化",
      "entity_type": "invoice_match",
      "entity_id": "uuid",
      "owner_id": "uuid",
      "owner_email": "user@example.com",
      "business_date": "2026-04-26",
      "created_at": "2026-04-26T00:00:00Z"
    }
  ],
  "count": 1
}
```

### GET `/api/v1/finance/dashboard/by-user`

管理员专用。普通用户返回 403。

返回按用户聚合的待处理数量：

```json
{
  "data": [
    {
      "owner_id": "uuid",
      "owner_email": "user@example.com",
      "purchase_record_unmatched": 3,
      "invoice_file_unallocated": 2,
      "match_needs_review": 1,
      "total_pending": 6
    }
  ],
  "count": 1
}
```

## 统计口径

### 购买记录

- 默认统计非永久删除记录。
- `deleted` 单独统计 `deleted_at IS NOT NULL`。
- `unmatched`：非 deleted，且不存在 active match。
- `matched`：非 deleted，且存在 active match。
- active match 指 `confirmed` 或 `needs_review`。

### 发票

- 默认统计非 deleted。
- `voided` 根据发票状态统计。
- `unallocated`：confirmed 发票，active match 已分配金额为 0。
- `partially_allocated`：confirmed 发票，0 < allocated_amount < invoice_amount。
- `fully_allocated`：confirmed 发票，allocated_amount 与 invoice_amount 差额 <= 0.01。

### 匹配

- `confirmed`：状态为 confirmed。
- `needs_review`：状态为 needs_review。
- `cancelled`：状态为 cancelled。

## 金额计算

复用 Round 005 发票匹配模块中的 allocated / remaining 计算逻辑，避免 dashboard 重写一套金额规则。

如果 Round 005 未提供可复用函数，后端 AI 应优先提取共享 service/repository helper，而不是复制粘贴。

## 前端工具

建议路径：

```text
frontend/src/tools/finance/dashboard/
```

文件结构：

```text
api.ts
types.ts
index.ts
hooks/useFinanceDashboard.ts
components/FinanceDashboardPage.tsx
components/SummaryCards.tsx
components/PendingList.tsx
components/UserPendingTable.tsx
```

路由：

```text
frontend/src/routes/_layout/finance.dashboard.tsx
```

导航：

```text
财务 -> 统计
```

## 页面布局

第一版保持工具型界面：

- 顶部标题和更新时间。
- 三组统计卡片：购买记录、发票、匹配。
- 待处理事项列表。
- 管理员额外显示按用户分组表格。

不要做营销式大 hero，不需要图表库。

## i18n

如果 Round 003 已合并：

- 新增 `finance.dashboard.*` 字典。
- 页面标题、卡片标题、待处理类型、按钮、空状态全部走翻译。

如果 Round 003 未合并：

- 前端 AI 不应阻塞业务页面实现。
- 报告中写明 i18n 接入阻塞，后续由 Round 003 合并后补齐。

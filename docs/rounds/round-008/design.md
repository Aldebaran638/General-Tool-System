# Round 008 Design - reimbursement_excel

## 后端模块

建议路径：

```text
backend/app/modules/finance/reimbursement_exports/
```

文件结构：

```text
constants.py
models.py
schemas.py
storage.py
excel_builder.py
repository.py
service.py
router.py
__init__.py
```

## 全局配置表

新增平台级表：

```text
app_setting
```

字段建议：

```text
key: str primary key
value: str
value_type: str
description: str | null
updated_by_id: uuid | null
updated_at: datetime
```

第一版只写入：

```text
key = reimbursement_export_retention_days
value = "1"
value_type = "int"
description = "Reimbursement export file retention days"
```

虽然是全局表，本轮 API 只暴露报销导出相关设置，不做通用配置中心 UI。

## 数据模型

### reimbursement_export

字段建议：

```text
id
created_by_id
created_at
department
business_unit
reimburser
reimbursement_date
currency
total_amount
item_count
original_filename
stored_filename
file_path
mime_type
file_size
file_expires_at
file_deleted_at
```

说明：

- `file_expires_at` 根据配置保留天数计算。
- 清理文件后设置 `file_deleted_at`。
- 历史记录不删除。

### reimbursement_export_item

字段建议：

```text
id
export_id
purchase_record_id
invoice_file_id
invoice_match_id
document_number
purchase_date
amount
currency
category
subcategory
order_name
remark
description_snapshot
department_snapshot
created_at
```

说明：

- 这是导出时快照。
- 即使后续购买记录修改，历史导出的编号和内容仍可追溯。

## API

### GET `/records`

管理员查询可导出的购买记录。

Query：

- `purchase_date_from`
- `purchase_date_to`
- `owner_id`
- `category`
- `subcategory`
- `currency`
- `exported`: `all` / `exported` / `not_exported`
- `q`
- `skip`
- `limit`

返回：

- 购买记录基本信息。
- 匹配发票信息。
- 是否已导出。
- 最近导出时间。
- 最近导出人。

### POST `/generate`

管理员生成 Excel。

Request：

```json
{
  "purchase_record_ids": ["uuid"],
  "department": "",
  "business_unit": "",
  "reimburser": "",
  "reimbursement_date": "2026-04-26"
}
```

全部表头字段非必填。

校验：

- 必须至少选择 1 条购买记录。
- 当前用户必须是管理员。
- 所有记录必须满足导出条件。
- 所有记录必须同一币种。
- 允许多用户。
- 允许重复导出。

响应：

```json
{
  "id": "uuid",
  "filename": "reimbursement_20260426.xlsx",
  "download_url": "/api/v1/finance/reimbursement-exports/{id}/download"
}
```

### GET `/history`

管理员查看导出历史。

Query：

- `created_at_from`
- `created_at_to`
- `created_by_id`
- `currency`
- `skip`
- `limit`

### GET `/{id}`

管理员查看导出详情，包含导出项快照。

### GET `/{id}/download`

管理员下载未过期且物理文件存在的 Excel。

如果文件已清理：

- 返回 410 Gone。
- detail：`File expired. Please regenerate.`

### GET `/settings`

管理员读取报销导出设置。

返回：

```json
{
  "retention_days": 1
}
```

### PUT `/settings`

管理员更新设置。

校验：

- `retention_days` 必须在 1 到 365。

### POST `/purge-expired-files`

管理员清理过期物理 Excel 文件。

返回：

```json
{
  "purged_count": 3
}
```

## Excel 生成

使用 `openpyxl`。

流程：

1. 加载模板 `docs/報銷表模板最新.xlsx`。
2. 校验存在 sheet：
   - `報銷單分类`
   - `報銷單`
3. 复制/扩展明细行样式。
4. 按类别顺序和组内排序生成导出项。
5. 从 1 开始生成 `document_number`。
6. 写入 `報銷單` 明细页。
7. 写入 `報銷單分类` 汇总页。
8. 写入表头字段。
9. 保存到 `runtime_data/exports/finance/reimbursement/`。
10. 写入导出历史和导出项快照。

## 类别排序

类别顺序常量：

```text
transportation
meals_entertainment
vehicle
other_project
```

组内排序：

```text
purchase_date ASC
created_at ASC
id ASC
```

## 编号范围格式

分类页显示单据编号时，应压缩连续编号：

```text
1,2,3,4,5 -> 1-5
1,2,5,7,8,9 -> 1-2, 5, 7-9
22,23,24,39,91 -> 22-24, 39, 91
```

如需要附加备注“已提交正本”，第一版不自动生成，由管理员在购买记录备注中体现。

## 前端工具

建议路径：

```text
frontend/src/tools/finance/reimbursement_exports/
```

文件结构：

```text
api.ts
types.ts
index.ts
hooks/useReimbursementExports.ts
components/ReimbursementExportsPage.tsx
components/ExportRecordFilters.tsx
components/ExportRecordTable.tsx
components/GenerateExportDialog.tsx
components/ExportHistoryTable.tsx
components/ExportSettingsDialog.tsx
```

路由：

```text
frontend/src/routes/_layout/finance.reimbursement-exports.tsx
```

导航：

```text
财务 -> 报销导出
```

## 前端交互

页面分为三个区域：

1. 可导出购买记录。
2. 导出历史。
3. 设置入口。

生成流程：

1. 管理员筛选购买记录。
2. 勾选记录。
3. 如果选中记录包含已导出项，弹出警告。
4. 管理员填写可选表头字段。
5. 点击生成。
6. 生成成功后显示下载入口。

## i18n

如果 Round 003 已合并：

- 新增 `finance.reimbursementExports.*` 字典。
- 页面标题、筛选项、按钮、警告、错误、空状态、设置弹窗都走翻译。

如果 Round 003 未合并：

- 不阻塞后端。
- 前端报告中说明 i18n 接入阻塞。

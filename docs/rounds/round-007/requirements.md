# Round 007 Requirements - finance_dashboard

## 背景

发票系统需要一个财务统计页，用来快速看到购买记录、发票、匹配关系中的待处理事项。

签字功能暂时冻结，不进入本轮。

## 目标

新增 `finance / dashboard` 工具：

- 普通用户查看自己的统计。
- 管理员查看全局统计。
- 管理员额外看到按用户分组的待处理数量。
- 统计数据由后端聚合，前端只负责展示。

## 非目标

- 不做签字。
- 不做报销单 Excel 导出。
- 不做复杂图表。
- 不做用户角色体系。
- 不修改购买记录、发票文件、发票匹配的核心状态定义。
- 不在前端直接拉全量数据后自行统计。

## 页面入口

```text
财务 -> 统计
```

建议路径：

```text
/finance/dashboard
```

API 前缀：

```text
/api/v1/finance/dashboard
```

## 权限

### 普通用户

只能看到自己的：

- 购买记录统计。
- 发票统计。
- 匹配统计。
- 待处理列表。

### 管理员

可以看到：

- 全部用户的数据统计。
- 按用户分组的待处理数量。
- 全局待处理列表。

## 第一版统计指标

### 购买记录

- `purchase_record_total`：购买记录总数。
- `purchase_record_unmatched`：未匹配发票的购买记录数。
- `purchase_record_matched`：已匹配发票的购买记录数。
- `purchase_record_deleted`：逻辑删除中的购买记录数。

### 发票

- `invoice_file_total`：发票总数。
- `invoice_file_unallocated`：未分配金额的发票数。
- `invoice_file_partially_allocated`：部分分配金额的发票数。
- `invoice_file_fully_allocated`：已完全分配金额的发票数。
- `invoice_file_voided`：已作废发票数。

### 匹配

- `match_confirmed`：已确认匹配数。
- `match_needs_review`：需要复核匹配数。
- `match_cancelled`：已取消匹配数。

## 待处理列表

后端返回最多 20 条待处理事项，按优先级排序。

第一版待处理类型：

- `purchase_record_unmatched`：购买记录没有匹配发票。
- `invoice_file_unallocated`：发票没有分配到购买记录。
- `match_needs_review`：匹配关系需要复核。

每条待处理事项应包含：

- `type`
- `severity`：`info` / `warning` / `danger`
- `title`
- `description`
- `entity_type`
- `entity_id`
- `owner_id`
- `owner_email`，管理员视角需要
- `created_at` 或相关业务日期

## 管理员按用户分组

管理员接口返回 `by_user`：

- `owner_id`
- `owner_email`
- `purchase_record_unmatched`
- `invoice_file_unallocated`
- `match_needs_review`
- `total_pending`

普通用户接口可返回空数组。

## 依赖

本轮依赖：

- Round 001 `purchase_records`
- Round 002 `invoice_files`
- Round 005 `invoice_matching`

如果 Round 005 尚未合并：

- 后端 AI 不应硬编码假接口。
- 应等待 Round 005 合并，或在报告中明确阻塞。

## 验收标准

- 普通用户只能看到自己的统计。
- 管理员能看到全局统计和按用户分组。
- 统计接口不返回已被其他用户逻辑删除且不可见的数据给普通用户。
- 前端页面没有写死业务统计逻辑。
- 导航中出现在财务工具组下。
- 三语言项目中，新增页面核心文案应接入 i18n。如果 Round 003 尚未合并，则报告中说明阻塞。

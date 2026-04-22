---
name: db-design-intake
description: 将已确认的工具定义转成结构化的数据与持久化决策。当架构师需要判断当前工具是复用已有数据结构、扩展已有结构，还是新增数据结构时使用。
---

## 输入

1. tool-intake 产出的 JSON。
2. 用户对数据归属、唯一性、删除规则、关联关系的补充说明。
3. 当前数据库相关文件：
   backend/app/models.py
   backend/app/modules/*/models.py

## 目标

输出一个足够支撑后续设计文档和后端实现的数据决策 JSON。

## 固定执行顺序

1. 先读取 tool-intake 输出的 object_key、object_name、core_actions、summary。
2. 再检查现有模型中是否已有可复用的表或模型。
3. 再判断 schema_strategy：
   reuse
   extend
   create
   no-persistence-change
4. 再补齐字段、索引、唯一性、外键、删除限制。
5. 最后整理为统一 JSON 草稿给用户确认。

## 必须输出的字段

- object_key
- schema_strategy
- migration_required
- tables
- relations
- notes

## tables 中每一项必须包含

- table_name
- action
- description
- fields

## fields 中每一项必须包含

- field_key
- field_name
- type
- nullable
- primary_key
- unique
- index
- default
- foreign_key
- source

## 规则

1. 必须先检查当前仓库里是否已有可复用的数据结构。
2. 如果现有表足够支撑需求，禁止默认新建平行表。
3. 如果现有表只能部分支撑需求，必须明确是 extend 还是 create。
4. relations 用于表达该工具与已有对象之间的依赖关系。
5. migration_required 只能是 true 或 false。
6. source 只能取以下值之一：
   existing-table
   new-field
   new-table
7. 在用户明确表示“通过”“可以”“没问题”之前，不得输出最终 JSON。
8. 最终输出时，只输出 JSON，不附加解释文字。

## 固定输出格式

```json
{
  "object_key": "supplier_reconciliation",
  "schema_strategy": "extend",
  "migration_required": true,
  "tables": [
    {
      "table_name": "supplier_reconciliation",
      "action": "create",
      "description": "存储供应商对账单头信息。",
      "fields": [
        {
          "field_key": "id",
          "field_name": "主键ID",
          "type": "bigint",
          "nullable": false,
          "primary_key": true,
          "unique": true,
          "index": true,
          "default": null,
          "foreign_key": null,
          "source": "new-table"
        }
      ]
    }
  ],
  "relations": [
    "supplier_reconciliation.supplier_id -> supplier.id"
  ],
  "notes": [
    "提交后禁止直接删除已对账单据。"
  ]
}
```
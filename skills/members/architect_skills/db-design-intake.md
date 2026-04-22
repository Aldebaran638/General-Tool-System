---
name: db-design-intake
description: 将第一阶段产出的业务对象定义，转成结构化数据库设计定义。当用户已经明确一个新业务对象，并需要通过对话逐步确认数据库层该如何落地时使用。输出字段包括 object_key、tables。该 skill 负责与用户确认是否需要新建表、字段如何定义、字段类型、是否可空、是否唯一、是否主键、是否建立索引、默认值是什么，以及外键关联到哪张表的哪个字段。
---

## 输入:
* 第一阶段输出的业务对象定义 JSON
* 用户当前补充的提示词（用于修正、细化、微调数据库方案）
* 当前数据库的数据库文件，固定指以下相对路径中的文件：
  * `backend/app/models.py`
  * `backend/app/modules/*/models.py`

## 逻辑：
* 通过简短追问，澄清该业务对象在数据库层应该如何落地。
* 从第一阶段输出结果收集以下内容：
  * `object_key`
  * `object_name`
  * `fields`
  * `description`
* 结合当前数据库文件，判断现有表是否可以直接复用、扩展，或需要新建。
* 最终生成结构化数据库设计定义。
* 结合规则见 `规则` 板块。

## skill流程:
```mermaid
flowchart TD
    A[输入第一阶段业务对象定义 JSON] --> B[读取用户补充提示词]
    B --> C[读取当前数据库相关内容]
    C --> D[AI提取可复用表与潜在关联]
    D --> E{信息是否足够}
    E -- 否 --> F[AI向用户追问最必要问题]
    F --> G[整理当前数据库设计草稿]
    G --> H[展示给用户审核]
    H --> I{用户是否通过}
    I -- 否 --> J[根据用户意见修改草稿]
    J --> E
    I -- 是 --> K[输出最终 JSON]
    K --> L[结束当前 skill]

    E -- 是 --> G
```

## 规则：

* `object_key` 来自第一阶段输入，不得擅自修改。

* `tables` 是本次需要复用、扩展或新建的表定义集合。

* AI 必须先检查当前数据库内容中是否已有可复用或可扩展的表。

* 用户当前补充的提示词拥有修正权，可用于调整 AI 对复用、新建、关联关系、字段定义的判断。

* 如果现有表无法完全支持当前业务对象，AI 需要向用户确认是扩展旧表，还是新建表。

* 如果当前业务对象与已有业务对象存在关系，AI 需要向用户确认是否要通过外键或关联表将它们联系起来。

* 每一轮对话只专注于一个问题，内容需要简洁，禁止输出过多行数导致刷屏。

* 缺信息时，只能追问当前最必要的问题。

* 审核阶段应先展示草稿，再等待用户确认。

* 在用户明确表示“通过”“可以”“没问题”之前，不得输出最终 JSON。

* 最终输出时，只输出 JSON，不附加任何解释文字。

* `tables` 中每一项表示一张需要处理的表，必须包含以下字段：

  * `table_name`
  * `action`
  * `description`
  * `fields`

* `action` 只能从以下值中选择：

  * `reuse`
  * `extend`
  * `create`

* `fields` 中每一项表示一个字段，必须包含以下字段：

  * `field_key`
  * `field_name`
  * `type`
  * `nullable`
  * `primary_key`
  * `unique`
  * `index`
  * `default`
  * `foreign_key`

* `type` 先只允许使用常见值，例如：

  * `bigint`
  * `int`
  * `varchar`
  * `text`
  * `boolean`
  * `date`
  * `datetime`
  * `decimal`

* `nullable` 只能是 `true` 或 `false`

* `primary_key` 只能是 `true` 或 `false`

* `unique` 只能是 `true` 或 `false`

* `index` 只能是 `true` 或 `false`

* `default` 表示字段默认值；没有默认值时必须为 `null`

* `foreign_key` 没有外键时必须为 `null`

* `foreign_key` 有值时格式必须为：

  * `table`
  * `field`

## 固定输出格式(示例)：

```json
{
  "object_key": "transcript",
  "tables": [
    {
      "table_name": "transcript",
      "action": "create",
      "description": "用于存储学生成绩单信息",
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
          "foreign_key": null
        },
        {
          "field_key": "student_id",
          "field_name": "学生ID",
          "type": "bigint",
          "nullable": false,
          "primary_key": false,
          "unique": false,
          "index": true,
          "default": null,
          "foreign_key": {
            "table": "student",
            "field": "id"
          }
        },
        {
          "field_key": "semester",
          "field_name": "学期",
          "type": "varchar",
          "nullable": false,
          "primary_key": false,
          "unique": false,
          "index": false,
          "default": null,
          "foreign_key": null
        }
      ]
    }
  ]
}
```

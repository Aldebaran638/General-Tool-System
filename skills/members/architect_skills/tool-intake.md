---
name: tool-intake
description: 将用户需求转成结构化的 group -> tool 定义草案。当架构师需要通过对话澄清一个新工具、新工具组、现有工具修改需求，或把混合需求拆成单工具任务时使用。
---

## 输入

1. 用户当前需求。
2. 用户对现有工具、现有页面、现有接口的补充说明。
3. 如已给出，则读取当前任务涉及的已有路径或文档。

## 目标

通过最少问题，产出可继续进入数据库设计与设计文档阶段的结构化定义。

## 固定执行顺序

1. 先判断请求类型：
   new-group
   new-tool
   existing-tool-change
   split-into-multiple-tools
2. 再判断本次是否需要独立前端页面。
3. 再判断本次是否需要独立后端模块。
4. 再判断本次是否涉及数据实体变化。
5. 最后整理为统一 JSON 草稿给用户确认。

## 必须收集的字段

- request_type
- group
- group_name
- tool_key
- tool_name
- route_path
- navigation_label
- object_key
- object_name
- core_actions
- primary_actor
- frontend_required
- backend_required
- summary
- assumptions
- open_questions

## 规则

1. 只基于当前输入判断，不得引入未确认的历史业务假设。
2. 一轮只问一个最关键的问题。
3. 先确认工具边界，再讨论数据库和接口。
4. 如果用户描述实际上包含多个工具，必须先拆分，再分别整理。
5. 如果当前需求只是新增工具组，tool_key、tool_name、route_path、object_key、object_name 允许为 null。
6. group、tool_key 必须使用稳定英文标识。
7. route_path 必须以当前项目可接受的路由形态表达。
8. core_actions 只记录当前工具真实要支持的用户动作。
9. assumptions 只记录已被架构师主动声明、但尚未得到用户明确确认的推断。
10. open_questions 只记录会阻塞后续设计的未决问题。
11. 在用户明确表示“通过”“可以”“没问题”之前，不得输出最终 JSON。
12. 最终输出时，只输出 JSON，不附加解释文字。

## 固定输出格式

```json
{
  "request_type": "new-tool",
  "group": "purchase-records",
  "group_name": "采购记录",
  "tool_key": "supplier-reconciliation",
  "tool_name": "供应商对账",
  "route_path": "/purchase-records/supplier-reconciliation",
  "navigation_label": "供应商对账",
  "object_key": "supplier_reconciliation",
  "object_name": "供应商对账单",
  "core_actions": ["list", "read", "create", "submit"],
  "primary_actor": "finance-manager",
  "frontend_required": true,
  "backend_required": true,
  "summary": "用于按供应商维度查看、创建并提交对账单。",
  "assumptions": [],
  "open_questions": []
}
```
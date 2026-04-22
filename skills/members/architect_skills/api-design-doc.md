---
name: api-design-doc
description: 将工具定义与数据决策组合成一个可交接的设计文档。当架构师需要为前端、后端、测试生成统一设计文档时使用。
---

## 输入

1. tool-intake 输出的 JSON。
2. db-design-intake 输出的 JSON。
3. 用户当前补充的提示词。

## 目标

输出一份 markdown 设计文档，供前端AI、后端AI、测试AI共享使用。

## 固定执行顺序

1. 读取 group、tool_key、tool_name、route_path、navigation_label、core_actions。
2. 读取 schema_strategy、tables、relations、notes。
3. 推导本工具的前端根目录、后端根目录、测试目录。
4. 按工具动作推导 API 契约。
5. 按 API 契约推导页面状态、权限规则、文件边界、验收标准。
6. 先展示草稿给用户审核，再输出最终文档。

## 规则

1. 只基于当前输入生成设计文档，不得擅自补充未被输入支持的功能点。
2. 禁止强行套用统一请求包裹结构，除非用户已明确要求。
3. 一个工具一份设计文档，不得混入其他工具。
4. 必须写出真实目录路径：
   frontend/src/tools/<group>/<tool-key>/
   backend/app/modules/<group>/<tool-key>/
   frontend/tests/<group>/<tool-key>/
   backend/tests/<group>/<tool-key>/
5. 如果本次只是前端工具组调整，必须在文档中明确写出“本次无后端 API 变更”。
6. 审核通过前不得输出最终文档。
7. 最终输出时，只输出设计文档，不附加解释文字。

## 固定输出结构

```md
# <tool_key> 设计文档

## 一、工具身份
- request_type:
- group:
- tool_key:
- tool_name:
- route_path:
- navigation_label:
- frontend_root:
- backend_root:
- frontend_test_root:
- backend_test_root:

## 二、需求摘要
- summary:
- primary_actor:
- core_actions:

## 三、数据与持久化决策
- schema_strategy:
- migration_required:
- tables:
- relations:
- notes:

## 四、API 契约
### 1. <endpoint_id>
- method:
- path:
- purpose:
- auth_requirement:
- request_shape:
- response_shape:
- error_shape:
- business_rules:

## 五、前端页面状态
- loading:
- empty:
- success:
- validation_error:
- permission_denied:
- backend_failure:

## 六、文件边界
- allowed_files:
- forbidden_files:

## 七、验收清单
- frontend_acceptance:
- backend_acceptance:
- integration_acceptance:
```
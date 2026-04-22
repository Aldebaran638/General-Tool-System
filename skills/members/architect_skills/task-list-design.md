---
name: task-list-design
description: 将工具定义、数据决策、设计文档、测试文档组合成结构化任务清单。当架构师需要生成前端、后端、联调、测试可直接执行的任务包时使用。
---

## 输入

1. tool-intake 输出的 JSON。
2. db-design-intake 输出的 JSON。
3. api-design-doc 输出的设计文档。
4. test-doc-design 输出的测试文档。
5. 用户当前补充的提示词。

## 目标

输出一份 markdown 任务清单，供前端AI、后端AI、测试AI直接执行。

## 固定执行顺序

1. 读取工具身份、目录路径、API 契约、页面状态、测试范围。
2. 先拆前端任务，再拆后端任务。
3. 再整理联调任务。
4. 最后整理 QA 任务。
5. 每条任务都必须绑定 allowed_files 与 done_when。
6. 先展示草稿给用户审核，再输出最终文档。

## 规则

1. 任务清单必须围绕单个工具生成，不得混入其他工具的任务。
2. 任务清单必须包含 FE、BE、INT、QA 四段。
3. 每条任务必须包含：
   task_id
   title
   description
   depends_on
   allowed_files
   done_when
4. 已定义的核心动作、接口、测试点必须在任务清单中被映射。
5. 任务边界必须能直接约束子智能体，不得只写抽象描述。
6. 审核通过前不得输出最终文档。
7. 最终输出时，只输出任务清单，不附加解释文字。

## 固定输出结构

```md
# <tool_key> 任务清单

## 一、任务上下文
- group:
- tool_key:
- frontend_root:
- backend_root:
- frontend_test_root:
- backend_test_root:

## 二、前端任务
### FE-001
- title:
- description:
- depends_on:
- allowed_files:
- done_when:

## 三、后端任务
### BE-001
- title:
- description:
- depends_on:
- allowed_files:
- done_when:

## 四、联调任务
### INT-001
- title:
- description:
- depends_on:
- allowed_files:
- done_when:

## 五、测试任务
### QA-001
- title:
- description:
- depends_on:
- allowed_files:
- done_when:
```
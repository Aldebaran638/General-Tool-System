# Skill System 使用说明

## 1. 这套 skill 是怎么分工的

这套体系不是让所有 AI 同时自由发挥，而是固定成一条单向流水线：

1. 用户只直接和架构师沟通。
2. 架构师负责把需求拆成 group -> tool，并产出设计、测试、任务、派单包。
3. 前端 AI 只负责一个工具的前端实现。
4. 后端 AI 只负责一个工具的后端实现。
5. 测试 AI 只负责验收，不负责反向补设计。

对应 skill 文件：

- 架构师：[skills/members/架构师skill.md](skills/members/%E6%9E%B6%E6%9E%84%E5%B8%88skill.md)
- 前端成员：[skills/members/前端skill.md](skills/members/%E5%89%8D%E7%AB%AFskill.md)
- 后端成员：[skills/members/后端skill.md](skills/members/%E5%90%8E%E7%AB%AFskill.md)
- 测试成员：[skills/members/测试skill.md](skills/members/%E6%B5%8B%E8%AF%95skill.md)
- 前端 builder：[skills/tool-frontend-builder/SKILL.md](skills/tool-frontend-builder/SKILL.md)
- 后端 builder：[skills/tool-module-builder/SKILL.md](skills/tool-module-builder/SKILL.md)
- 共享规则入口：[skills/tool-system/README.md](skills/tool-system/README.md)

## 2. 你作为用户应该怎么用

你正常情况下只需要驱动架构师。

推荐用法：

1. 把需求直接告诉架构师。
2. 让架构师先澄清边界，再产出完整任务包。
3. 架构师产出任务包后，再分别把前端任务、后端任务派给空白子 AI。
4. 前后端都交付并产出报告后，再派测试 AI 验收。

不要直接跳过架构师，把一个模糊需求丢给前端或后端。

不要在前端或后端还没出报告时就派测试 AI。

## 3. 标准执行顺序

### 第一步：你向架构师提需求

你给架构师的信息至少应包含：

1. 这是新增工具、修改现有工具，还是新增工具组。
2. 用户从哪里进入这个工具。
3. 这个工具要支持哪些核心动作。
4. 是否涉及后端接口或数据结构。

推荐说法：

```text
请你作为架构师，按当前仓库的 skill 体系处理这个需求：
我要在 <group> 下新增/修改一个 <tool_name> 工具。
用户入口是 <route or navigation>。
核心动作有：<list/read/create/update/delete/...>。
这次需要/不需要后端接口改动。
请先完成澄清，再输出设计文档、测试文档、任务清单和派单包。
```

### 第二步：架构师必须产出四类输入物

架构师完成后，至少应产出：

1. 设计文档：docs/design/<group>/<tool_key>.md
2. 测试文档：docs/test/<group>/<tool_key>.md
3. 任务清单：docs/tasks/<group>/<tool_key>.md
4. 派单包：docs/packets/<group>/<tool_key>/dispatch.md

如果涉及数据库决策，还应有：

1. tool intake：docs/packets/<group>/<tool_key>/01-tool-intake.json
2. db design：docs/packets/<group>/<tool_key>/02-db-design.json

### 第三步：派前端 AI

前端 AI 不是直接自由编码，而是必须先执行成员 skill，再进入 builder。

你给前端 AI 的任务应该明确写成：

```text
你现在只负责一个工具：<group> / <tool_key>。
先读取：
1. docs/design/<group>/<tool_key>.md
2. docs/test/<group>/<tool_key>.md
3. docs/tasks/<group>/<tool_key>.md
4. skills/members/前端skill.md
5. skills/tool-frontend-builder/SKILL.md

然后严格按任务清单实现，并输出 frontend report。
```

前端交付完成后，必须至少产出：

1. 前端工具目录：frontend/src/tools/<group>/<tool_key>/
2. 前端测试目录：frontend/tests/<group>/<tool_key>/
3. 前端报告：docs/packets/<group>/<tool_key>/frontend-report.md

### 第四步：派后端 AI

你给后端 AI 的任务应该明确写成：

```text
你现在只负责一个工具：<group> / <tool_key>。
先读取：
1. docs/design/<group>/<tool_key>.md
2. docs/test/<group>/<tool_key>.md
3. docs/tasks/<group>/<tool_key>.md
4. skills/members/后端skill.md
5. skills/tool-module-builder/SKILL.md

然后严格按任务清单实现，并输出 backend report。
```

后端交付完成后，必须至少产出：

1. 后端模块目录：backend/app/modules/<group>/<tool_key>/
2. 后端测试目录：backend/tests/<group>/<tool_key>/
3. 后端报告：docs/packets/<group>/<tool_key>/backend-report.md

### 第五步：派测试 AI

只有当前端报告、后端报告、前后端主测试文件都存在时，才可以派测试 AI。

你给测试 AI 的任务应该明确写成：

```text
你现在只负责一个工具：<group> / <tool_key>。
先读取：
1. docs/design/<group>/<tool_key>.md
2. docs/test/<group>/<tool_key>.md
3. docs/tasks/<group>/<tool_key>.md
4. docs/packets/<group>/<tool_key>/frontend-report.md
5. docs/packets/<group>/<tool_key>/backend-report.md
6. skills/members/测试skill.md

然后按测试文档执行验收，输出最终结论。
```

## 4. 你需要记住的目录规则

内部标识统一使用 snake_case。

原因：后端目录会进入 Python import 链，不能用带连字符的内部目录名。

固定规则：

1. group 必须是 snake_case。
2. tool_key 必须是 snake_case。
3. 前端目录：frontend/src/tools/<group>/<tool_key>/
4. 前端测试目录：frontend/tests/<group>/<tool_key>/
5. 后端目录：backend/app/modules/<group>/<tool_key>/
6. 后端测试目录：backend/tests/<group>/<tool_key>/

用户可见的 URL 可以保留产品需要的写法，不要求和内部 tool_key 完全一致。

## 5. 哪些 skill 是用户直接关心的

你直接关心这四类：

1. 架构师 skill：用来把需求变成可执行任务包。
2. 前端 skill：约束前端子 AI 的边界和交付物。
3. 后端 skill：约束后端子 AI 的边界和交付物。
4. 测试 skill：约束测试 AI 的准入条件和验收方式。

builder skill 更像执行引擎，不是你平时直接对话的主要入口。

## 6. 什么时候说明流程是闭环的

一条工具流水线只有同时满足下面条件，才算闭环：

1. 架构师已经产出设计文档、测试文档、任务清单、派单包。
2. 前端已经产出工具目录、主测试文件、frontend report。
3. 后端已经产出模块目录、主测试文件、backend report。
4. 自动化测试已经真实执行，不是口头声称通过。
5. 测试 AI 已经根据前后端报告完成验收。

只做到“文档齐全”不算闭环。

只做到“代码改完但没跑测试”也不算闭环。

## 7. 推荐的用户提问模板

### 模板 A：新增工具

```text
请按当前仓库的 skill 体系处理一个新增工具需求。
group 暂定为 <group>。
工具名称是 <tool_name>。
入口想放在 <navigation group> 下。
路由想要 <route_path>。
核心动作：<...>。
请先完成需求澄清，然后输出完整任务包，不要直接写代码。
```

### 模板 B：修改现有工具

```text
请按当前仓库的 skill 体系处理一个现有工具修改需求。
现有工具是 <route or existing tool>。
本轮只改这个工具，不要扩散到其他工具。
核心变更：<...>。
请先输出设计文档、测试文档、任务清单和派单包。
```

### 模板 C：进入实现阶段

```text
现在不要再改任务包。
直接用现有派单包，把 <group>/<tool_key> 派给前端 AI 和后端 AI 执行。
要求真实运行验证，并产出 frontend report 与 backend report。
```

### 模板 D：进入验收阶段

```text
前后端报告已经齐了。
现在直接按测试 skill 验收 <group>/<tool_key>，给出通过/退回修复/无法验收结论。
```

## 8. 常见错误用法

下面这些用法会直接破坏体系：

1. 让前端 AI 在没有设计文档和任务清单时直接开工。
2. 让后端 AI 同时实现多个工具。
3. 让测试 AI 在缺少 frontend report 或 backend report 时硬验收。
4. 允许子 AI 自己改 skill 文件。
5. 内部目录继续使用 kebab-case，导致后端模块 import 路径失效。
6. 自动化测试没跑通，却在报告里写“已通过”。

## 9. 你最少要检查什么

如果你只想做最低限度的人工把关，至少检查这几项：

1. design/test/tasks/dispatch 四类文档是否都存在。
2. frontend report 和 backend report 是否都存在。
3. 前端和后端主测试文件是否都落在标准路径。
4. 报告里的验证命令是否真实执行过。
5. group 与 tool_key 是否都是 snake_case。

## 10. 当前仓库的推荐使用方式

对这个仓库，推荐你始终使用下面的模式：

1. 用户只驱动架构师。
2. 架构师固定先出文档和派单包。
3. 空白前端子 AI 只读前端成员 skill + frontend builder + 本工具文档。
4. 空白后端子 AI 只读后端成员 skill + module builder + 本工具文档。
5. 空白测试子 AI 只在前后端报告齐全后才启动。

这是当前这套 skill 体系最稳的用法。
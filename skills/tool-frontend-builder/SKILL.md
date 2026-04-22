---
name: tool-frontend-builder
description: Build or repair exactly one frontend tool from an architect task packet, design document, test document, and task list. Use when a frontend agent must stay inside one tool boundary, follow the repository's real route and navigation structure, and keep code under the group/tool-key directory shape.
---

# Tool Frontend Builder

本 skill 用于实现或修复一个工具的前端部分。

目标工具的主要前端代码根目录必须为：

frontend/src/tools/<group>/<tool-key>/

目标测试目录必须为：

frontend/tests/<group>/<tool-key>/

## 输入优先级

1. 架构师明确派单内容
2. 任务清单
3. 设计文档
4. 测试文档
5. skills/members/前端skill.md
6. skills/tool-system/*.md
7. 当前仓库现有代码，仅作兼容性上下文

## 开工前必须读取

1. 架构师任务包
2. 任务清单
3. 设计文档
4. 测试文档
5. skills/members/前端skill.md
6. frontend/src/config/tool-navigation.tsx
7. frontend/src/routes/_layout.tsx
8. frontend/src/routes/_layout/ 下与本工具最接近的已有路由

## 核心规则

1. 一次只实现一个工具。
2. route 文件必须保持薄。
3. 主要业务代码必须收敛到 frontend/src/tools/<group>/<tool-key>/。
4. 只允许修改任务包授权范围与最小集成文件。
5. 视觉风格必须复用当前项目。
6. 禁止发明设计文档外的业务规则。

## 固定执行步骤

1. 从任务包中提取 group、tool_key、route、入口名称、API 清单、页面状态、权限要求。
2. 确认工具目录是否已存在；存在则复用，不存在则创建。
3. 检查导航与路由接入点。
4. 实现 api、types、schemas、hooks、components。
5. 在 route 文件中装配页面入口。
6. 注册 navigation。
7. 在 frontend/tests/<group>/<tool-key>/ 下实现或更新测试。
8. 执行针对本工具的验证。
9. 输出前端报告。

## 必须覆盖的验证

1. 当前工具相关构建校验。
2. 当前工具相关 Playwright 测试。
3. 至少一条核心成功流程。
4. 至少一条错误、空状态、权限状态中的已定义分支。

## 禁止事项

1. 禁止把新工具主要代码继续放入 frontend/src/tools/<tool-key>/ 单层目录。
2. 禁止在 route 文件中堆业务逻辑。
3. 禁止跳过导航注册。
4. 禁止跳过测试目录更新。
5. 禁止因为统一风格而重写无关工具。
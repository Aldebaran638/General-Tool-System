---
name: initializer-system
description: Use when an existing repository must be converted into an architect-led multi-agent tool pipeline, or when project-specific architect and worker skills need to be regenerated from repository facts instead of hand-written assumptions.
---

# Initializer System

本 skill 用于把一个已有项目初始化为“架构师负责决策，执行者负责单工具实现，程序负责编排，skill 负责约束”的流水线系统。

它不直接假设前端、后端、数据库、迁移工具、测试框架一定存在。

它的职责是：

1. 识别目标项目事实。
2. 把事实整理成机器可读的项目画像。
3. 依据项目画像生成或解析项目专属的 role skill。
4. 生成说明书与迁移计划。
5. 在交付前执行可靠性校验。

## 固定输出物

初始化完成后，至少必须得到：

1. `ai-system/project-skill-profile.json`
2. `ai-system/generated-skills-manifest.json`
3. `ai-system/skill-manual.md`
4. `ai-system/migration-plan.md`

当目标项目尚无可用 role skill 时，还必须生成：

1. `skills/generated/architect-skill.md`
2. `skills/generated/<role>-skill.md`
3. 必要时生成 `skills/generated/<role>-builder.md`

如果目标仓库已经存在符合要求的 skill，允许复用既有 skill 文件，但必须在 manifest 中明确标记为 `existing_project_skill`。

## 必读资料

始终先读取：

1. `references/core-protocol.md`
2. `references/project-profile-contract.md`
3. `references/generated-skills-manifest-contract.md`
4. `references/reliability-gate.md`

在识别执行角色时，额外读取：

1. `references/role-generation-contract.md`

在生成输出物时，直接复用这些模板：

1. `assets/templates/project-skill-profile.template.json`
2. `assets/templates/generated-skills-manifest.template.json`
3. `assets/templates/skill-manual.template.md`
4. `assets/templates/migration-plan.template.md`
5. `assets/templates/architect-skill.template.md`
6. `assets/templates/executor-skill.template.md`
7. `assets/templates/reviewer-skill.template.md`
8. `assets/templates/builder-skill.template.md`

## 固定工作流

### 第一步：识别项目事实

最少识别以下信息：

- 项目名称与仓库根目录
- 主业务单元是否能映射为 `group -> tool`
- 前端或其他界面层技术栈
- 后端或其他服务层技术栈
- 测试框架
- 数据库访问方式
- schema 演进机制
- 目录结构
- 路由或导航接入点
- 当前已有 skill 或提示规则位置

### 第二步：判断角色清单

架构师角色始终存在。

其他角色必须由仓库事实推导，不得写死成“永远只有前端和后端”。

例子：

- Web + API 项目：`architect`, `frontend_tool_worker`, `backend_tool_worker`, `test_worker`
- Web + API + Mobile 项目：再增加 `mobile_tool_worker`
- 数据平台项目：可能是 `architect`, `data_pipeline_worker`, `qa_worker`

### 第三步：生成项目画像

按 `project-profile-contract` 生成 `ai-system/project-skill-profile.json`。

项目画像必须写出：

- 技术栈事实
- 目录映射
- 角色清单
- 验证命令
- 输出物路径

### 第四步：生成或解析 role skill

对每个角色：

1. 优先检查仓库内是否已经存在合格 skill。
2. 若已存在，则在 manifest 中登记并说明复用原因。
3. 若不存在，则依据模板生成新 skill。

每个执行角色都必须写清：

- 任务边界
- 必读输入物
- 允许修改范围
- 禁止修改范围
- 必须产出的报告
- 必须执行的验证

### 第五步：生成说明书与迁移计划

`ai-system/skill-manual.md` 必须面向人和 AI 都可读。

`ai-system/migration-plan.md` 必须区分：

- 已执行动作
- 建议动作
- 必须人工确认的动作

### 第六步：执行可靠性校验

交付前必须执行：

`python3 skills/initializer-system/scripts/validate_outputs.py ai-system/project-skill-profile.json ai-system/generated-skills-manifest.json`

若脚本失败，必须继续修复输出物，禁止直接结束。

## 关键约束

1. 禁止把当前仓库的具体目录硬编码为所有项目的通用真理。
2. `group -> tool` 是业务抽象，不是语言绑定目录。
3. 角色类型必须来源于仓库事实，而不是初始化者主观想象。
4. 初始化者默认只生成规范、skill、说明书、迁移计划与目录骨架。
5. 未获明确授权前，禁止大规模搬迁现有业务代码。
6. 未获明确授权前，禁止删除现有业务代码。

## 完成标准

只有同时满足以下条件，初始化任务才算完成：

1. 四类固定输出物都存在。
2. 项目画像与 manifest 通过可靠性校验。
3. 角色清单与仓库事实一致。
4. 说明书能指导后续架构师与 worker 真正开工。
5. 迁移计划明确区分已执行、建议、待确认三类动作。

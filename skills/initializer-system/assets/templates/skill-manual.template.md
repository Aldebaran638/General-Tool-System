# <PROJECT_NAME> Skill Manual

## 1. 初始化结果

本项目已经被初始化为“架构师主导的多 Agent 工具流水线”。

当前真相源为：

1. `ai-system/project-skill-profile.json`
2. `ai-system/generated-skills-manifest.json`
3. 本项目实际 role skill 文件

## 2. 当前角色

- `architect`: `<SKILL_PATH>`
- `<ROLE_ID>`: `<SKILL_PATH>`

## 3. 标准运行方式

1. 用户只直接驱动 `architect`。
2. 架构师先产出设计、测试、任务、派单包。
3. 再派发给对应执行角色。
4. 执行角色必须回报并接受 change request。

## 4. 初始化输出物

- `project profile`: `ai-system/project-skill-profile.json`
- `skills manifest`: `ai-system/generated-skills-manifest.json`
- `migration plan`: `ai-system/migration-plan.md`

## 5. 维护规则

1. 修改角色边界前，先更新 `project profile`。
2. 修改 active skill 前，先更新 `generated-skills-manifest.json`。
3. 更新后重新运行校验脚本。

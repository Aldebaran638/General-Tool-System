# Invoice Management System Skill Manual

## 初始化结果

当前仓库已经具备“架构师主导的多 Agent 工具流水线”初始化基线。

本次初始化没有复制一套重复的成员 skill，而是先完成了两件事：

1. 用 `ai-system/project-skill-profile.json` 固化当前仓库的项目画像。
2. 用 `ai-system/generated-skills-manifest.json` 声明当前仓库实际启用的 role skill。

这意味着后续维护时，先看 `project-skill-profile.json` 和 `generated-skills-manifest.json`，再看具体 skill 文件。

## 当前激活角色

- `architect` -> `skills/members/架构师skill.md`
- `frontend_tool_worker` -> `skills/members/前端skill.md`
- `backend_tool_worker` -> `skills/members/后端skill.md`
- `test_worker` -> `skills/members/测试skill.md`

当前仓库额外复用的 builder：

- `frontend_tool_worker` -> `skills/tool-frontend-builder/SKILL.md`
- `backend_tool_worker` -> `skills/tool-module-builder/SKILL.md`

## 当前仓库的目录映射

- 抽象工具根：`src/tools/<group>/<tool_key>/`
- 前端真实工具根：`frontend/src/tools/<group>/<tool_key>/`
- 前端真实测试根：`frontend/tests/<group>/<tool_key>/`
- 后端真实工具根：`backend/app/modules/<group>/<tool_key>/`
- 后端真实测试根：`backend/tests/<group>/<tool_key>/`

当前仓库允许遗留结构继续存在，但新增工具必须收敛到上述路径。

## 标准运行方式

1. 用户只直接驱动 `architect`。
2. `architect` 先完成需求澄清，再输出设计文档、测试文档、任务清单、派单包。
3. `frontend_tool_worker` 与 `backend_tool_worker` 只各自执行一个工具。
4. 两个执行角色都必须回报结构化 report。
5. `test_worker` 只在前后端 report 齐全后启动验收。

## 初始化输出物

- 项目画像：`ai-system/project-skill-profile.json`
- 激活 skill 清单：`ai-system/generated-skills-manifest.json`
- 迁移计划：`ai-system/migration-plan.md`
- 初始化入口 skill：`skills/members/初始化者skill.md`
- 通用初始化骨架：`skills/initializer-system/SKILL.md`

## 维护规则

1. 角色边界变化时，先更新 `project-skill-profile.json`。
2. active skill 变化时，先更新 `generated-skills-manifest.json`。
3. 初始化体系更新后，必须重新运行：

```bash
python3 skills/initializer-system/scripts/validate_outputs.py ai-system/project-skill-profile.json ai-system/generated-skills-manifest.json
```

4. 若未来决定把当前成员 skill 全部迁移为 `skills/generated/`，先更新 manifest，再做物理迁移。

# 通用工具系统 Migration Plan

## 已执行

- 建立了可复用的 `skills/initializer-system/` 初始化 skill 骨架。
- 将成员级 `skills/members/初始化者skill.md` 改造成“扫描 -> 生成 -> 校验”的通用初始化入口。
- 生成了当前仓库的 `project profile`、`generated skills manifest` 与 `skill manual`。
- 增加了初始化输出校验脚本 `skills/initializer-system/scripts/validate_outputs.py`。

## 建议后续执行

- 持续把新增工具统一落到 `frontend/src/tools/<group>/<tool_key>/` 与 `backend/app/modules/<group>/<tool_key>/`。
- 在架构师交付包中逐步增加更稳定的机器可读字段，降低后续生成 role skill 的人工判断成本。
- 等现有成员 skill 稳定后，再决定是否把运行时 canonical skill 路径统一迁移到 `skills/generated/`。

## 需要人工确认

- 当前仓库后续是否要以 `skills/generated/` 作为正式运行时 skill 根目录。
- 设计文档、测试文档、任务清单是否要补一份 JSON 或 YAML 机器格式。
- 是否要为未来的非前后端角色预留 `mobile`、`data` 或 `infra` 类型 skill。

## 不在本次初始化中执行

- 不批量搬迁现有业务代码。
- 不删除任何遗留目录。
- 不重命名任何现有工具目录。
- 不修改当前前后端实现逻辑，仅建立初始化体系与初始化输出物。

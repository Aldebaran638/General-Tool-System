# Project Skill Profile Contract

初始化者必须生成一个机器可读的 `project-skill-profile.json`。

推荐字段如下。

```json
{
  "profile_version": "1.0",
  "generated_at": "YYYY-MM-DD",
  "project": {
    "name": "Project Name",
    "repository_root": ".",
    "summary": "..."
  },
  "system_target": {
    "orchestration_model": "architect-led-multi-agent",
    "canonical_group_key": "group",
    "canonical_tool_key": "tool_key"
  },
  "technology": {
    "surfaces": [],
    "database": {},
    "testing": {}
  },
  "repository_mapping": {
    "canonical_patterns": {},
    "executable_patterns": {},
    "integration_files": []
  },
  "roles": [],
  "verification_commands": [],
  "initialization_outputs": {}
}
```

## 1. 必填顶层字段

1. `profile_version`
2. `generated_at`
3. `project`
4. `system_target`
5. `technology`
6. `repository_mapping`
7. `roles`
8. `verification_commands`
9. `initialization_outputs`

## 2. `project`

至少包含：

1. `name`
2. `repository_root`
3. `summary`

## 3. `system_target`

至少包含：

1. `orchestration_model`
2. `canonical_group_key`
3. `canonical_tool_key`
4. `supports_group_tool_pipeline`

## 4. `technology`

至少包含：

1. `surfaces`
2. `database`
3. `testing`

`surfaces` 是数组，每项至少包含：

1. `surface_id`
2. `kind`
3. `language`
4. `framework`

## 5. `repository_mapping`

至少包含：

1. `canonical_patterns`
2. `executable_patterns`
3. `integration_files`

`canonical_patterns` 用于表达抽象模型。

`executable_patterns` 用于表达目标仓库里的真实落点。

路径模式允许使用占位符：

- `<group>`
- `<tool_key>`

## 6. `roles`

每个角色至少包含：

1. `role_id`
2. `role_kind`
3. `scope`
4. `skill_path`
5. `builder_skill_path`
6. `allowed_path_patterns`
7. `forbidden_path_patterns`
8. `required_inputs`
9. `report_name`

`builder_skill_path` 在无需 builder 时可为 `null`。

## 7. `verification_commands`

每条命令至少包含：

1. `command_id`
2. `cwd`
3. `command`
4. `purpose`

## 8. `initialization_outputs`

至少包含：

1. `profile_path`
2. `manifest_path`
3. `skill_manual_path`
4. `migration_plan_path`

## 9. 设计原则

1. 该文件必须只写仓库事实与初始化结论，不写空泛口号。
2. 所有路径必须相对仓库根目录可解析。
3. 如果仓库已存在可复用 skill，仍然要写入 `roles[].skill_path`。
4. 如果项目不是前后端结构，也不得强行伪造 `frontend` 与 `backend` 字段。

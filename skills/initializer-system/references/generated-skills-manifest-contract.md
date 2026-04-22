# Generated Skills Manifest Contract

初始化者必须生成 `generated-skills-manifest.json`，用于声明“当前项目最终使用哪些 skill 文件”。

## 1. 顶层字段

```json
{
  "manifest_version": "1.0",
  "project_profile_path": "ai-system/project-skill-profile.json",
  "shared_protocol_files": [],
  "skills": []
}
```

必填字段：

1. `manifest_version`
2. `project_profile_path`
3. `shared_protocol_files`
4. `skills`

## 2. `shared_protocol_files`

这里列出所有角色共同依赖的规则文件。

例如：

- tool system 共享规则
- 架构说明
- 目录契约
- 初始化协议

## 3. `skills`

每条 skill 记录至少包含：

1. `skill_id`
2. `role_id`
3. `role_kind`
4. `skill_path`
5. `status`
6. `selection_reason`
7. `depends_on`

可选字段：

1. `builder_skill_path`
2. `owned_scopes`

## 4. `status`

允许值：

1. `generated`
2. `existing_project_skill`
3. `shared_template`

## 5. 写法要求

1. 每个 `role_id` 只能解析到一个主 skill。
2. 如果角色还有 builder，需要在同一条记录中写清 `builder_skill_path`。
3. 如果复用仓库已有 skill，必须在 `selection_reason` 中写明为什么可以复用。
4. `depends_on` 中的路径必须真实存在。

# Reliability Gate

初始化者在交付前必须通过以下闸门。

## 1. 输出物闸门

以下文件必须存在：

1. `ai-system/project-skill-profile.json`
2. `ai-system/generated-skills-manifest.json`
3. `ai-system/skill-manual.md`
4. `ai-system/migration-plan.md`

## 2. 结构闸门

`project-skill-profile.json` 必须满足 contract 要求。

`generated-skills-manifest.json` 必须满足 manifest contract 要求。

## 3. 路径闸门

1. 每个 `skill_path` 必须真实存在。
2. 每个 `builder_skill_path` 若非空，必须真实存在。
3. 每个 `depends_on` 路径必须真实存在。
4. `repository_mapping.executable_patterns` 的每个路径模式静态前缀必须在仓库中存在。
5. `repository_mapping.canonical_patterns` 只要求表达抽象模型，不要求在仓库里物理存在。

## 4. 角色一致性闸门

1. `roles` 中的 `role_id` 必须唯一。
2. manifest 中每个 `role_id` 必须能在 profile 中找到。
3. `architect` 必须存在。
4. 复用仓库现有 skill 时，必须有明确复用理由。

## 5. 命令闸门

1. 每个验证命令必须有 `cwd` 与 `command`。
2. 当命令使用 `npm run <script>` 或 `bun run <script>` 时，对应 `package.json` 中必须存在该 script。

## 6. 说明书闸门

`skill-manual.md` 必须写清：

1. 当前项目实际启用哪些角色
2. 每个角色对应哪个 skill
3. 初始化者产出了哪些文件
4. 用户后续如何驱动流水线

## 7. 最终动作

必须运行：

`python3 skills/initializer-system/scripts/validate_outputs.py ai-system/project-skill-profile.json ai-system/generated-skills-manifest.json`

脚本返回成功后，才允许宣告初始化完成。

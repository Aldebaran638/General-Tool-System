# Initializer Reliability Report

## 执行范围

本次验证针对以下初始化输出物：

- `ai-system/project-skill-profile.json`
- `ai-system/generated-skills-manifest.json`
- `ai-system/skill-manual.md`
- `ai-system/migration-plan.md`

## 执行命令

```bash
python3 skills/initializer-system/scripts/validate_outputs.py ai-system/project-skill-profile.json ai-system/generated-skills-manifest.json
```

## 结果

- 结果：通过
- 结论：当前仓库的初始化输出在结构、路径、角色映射、共享协议引用、以及 Node script 声明层面全部通过校验

## 本轮发现并修复的问题

- 初版验证器错误地把 `canonical_patterns` 当成仓库中的物理路径校验，导致抽象模型与可执行映射混淆。
- 已修复为：
  - `canonical_patterns` 只检查是否表达了抽象模型
  - `executable_patterns` 才检查真实路径前缀是否存在

## 当前仍然存在的风险

- 当前验证器验证的是“初始化输出是否自洽”，不是“任意新仓库都能零人工初始化成功”。
- 当前仓库仍然存在历史遗留目录与测试路径，初始化体系已兼容，但未在本次任务中做物理迁移。
- 若未来引入 `mobile`、`data`、`infra` 等新执行角色，需要扩充 profile 与 manifest，而不是依赖当前四角色集合。

## 补充验证

- 已额外执行外部临时仓库压测：
  `python3 skills/initializer-system/scripts/run_smoke_tests.py`
- 外部压测在 `/tmp/initializer-smoke-*` 下动态生成样本仓库并自动清理。
- 当前已覆盖 `web + api`、`backend-only`、`mobile + api`、`data pipeline` 四类样本。

# Cross-Ecosystem Smoke Report

## 执行命令

```bash
python3 skills/initializer-system/scripts/run_smoke_tests.py
```

## 样本结果

1. `skills/initializer-system/fixtures/java-spring-suite`
   角色：`architect`, `backend_tool_worker`, `test_worker`
   结果：通过

2. `skills/initializer-system/fixtures/ts-platform-kit`
   角色：`architect`, `web_tool_worker`, `api_tool_worker`, `qa_worker`
   结果：通过

## 这轮验证证明了什么

- 初始化协议不依赖当前仓库的 `frontend/` 与 `backend/` 命名。
- 角色集合可以按仓库事实变化，不需要固定成前端、后端、测试三件套。
- 同一套 `project profile + manifest + validator` 可以覆盖：
  - TypeScript web + api 单仓
  - Java/Spring backend-only 仓

## 这轮验证没有证明什么

- 还没有证明“任意真实大型仓库”都能一次零人工初始化成功。
- 还没有覆盖 `mobile`、`data pipeline`、`infra` 等角色类型。
- 当前 smoke test 验证的是初始化输出契约，而不是完整代码生成质量。

## 当前结论

初始化体系已经从“只适配当前项目”提升到“至少能被异构样本仓库复用并通过统一校验”。

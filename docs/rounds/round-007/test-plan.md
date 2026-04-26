# Round 007 Test Plan - finance_dashboard

## 后端测试

必须新增：

```text
backend/tests/finance/dashboard/index_test.py
```

覆盖：

- 普通用户 summary 只统计自己的购买记录、发票、匹配。
- 管理员 summary 统计全局。
- 未匹配购买记录数量正确。
- 发票 unallocated / partially_allocated / fully_allocated 数量正确。
- needs_review 数量正确。
- pending 默认最多返回 20 条。
- pending 中普通用户看不到他人数据。
- by-user 普通用户 403。
- by-user 管理员返回按用户聚合结果。
- 逻辑删除数据不进入普通 active 统计，但 deleted 单独统计。

必须执行：

```bash
docker compose exec backend pytest tests/finance/dashboard/index_test.py -q
docker compose exec backend alembic current
```

如 Round 005 已合并，还应执行：

```bash
docker compose exec backend pytest tests/finance/invoice_matching/index_test.py -q
```

## 前端测试

必须新增：

```text
frontend/tests/finance/dashboard/index.spec.ts
```

覆盖：

- 财务侧边栏出现统计入口。
- 普通用户能打开统计页。
- 统计卡片显示。
- 待处理列表空状态或数据状态显示。
- 管理员能看到按用户分组表格。
- 普通用户看不到按用户分组表格。
- 如果 i18n 已合并，切换英文后页面核心文案变化。

必须执行：

```bash
docker compose exec frontend bun run build
docker compose exec frontend bun run test -- tests/finance/dashboard/index.spec.ts --reporter=line
```

如果 Playwright 因环境限制失败，报告必须记录真实命令和真实输出。

## 联调检查

- `/api/v1/finance/dashboard/summary` 正常返回。
- `/api/v1/finance/dashboard/pending` 正常返回。
- 管理员 `/api/v1/finance/dashboard/by-user` 正常返回。
- 前端页面显示数据，不在控制台报错。
- 普通用户和管理员视角不同。

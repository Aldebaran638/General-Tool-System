# Round 008 Test Plan - reimbursement_excel

## 后端测试

必须新增：

```text
backend/tests/finance/reimbursement_exports/index_test.py
```

覆盖：

- 普通用户访问 records/generate/history/settings 返回 403。
- 管理员能查询可导出购买记录。
- records 支持日期、用户、大类、小类、币种、关键词、已导出筛选。
- 生成时必须至少选择 1 条记录。
- 未批准购买记录不能导出。
- 未确认匹配购买记录不能导出。
- 发票 voided 的记录不能导出。
- 多币种不能同一份导出。
- 多用户可以同一份导出。
- 已导出记录可以重复导出。
- 生成后创建 reimbursement_export。
- 生成后创建 reimbursement_export_item 快照。
- 单据编号按类别顺序生成。
- 组内按 purchase_date / created_at / id 升序。
- 其他项目费用按小类汇总。
- Excel 文件存在且能用 openpyxl 打开。
- Excel 包含 `報銷單分类` 和 `報銷單` 两个 sheet。
- 下载未过期文件成功。
- 过期/已清理文件下载返回 410。
- 设置 retention_days 仅管理员可改。
- retention_days 校验 1 到 365。
- purge-expired-files 只删除物理文件，不删除历史。

必须执行：

```bash
docker compose exec backend pytest tests/finance/reimbursement_exports/index_test.py -q
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
```

如果 Round 005 已合并，还应执行：

```bash
docker compose exec backend pytest tests/finance/invoice_matching/index_test.py -q
```

## 前端测试

必须新增：

```text
frontend/tests/finance/reimbursement_exports/index.spec.ts
```

覆盖：

- 财务侧边栏出现报销导出入口。
- 普通用户不能进入或看到生成能力。
- 管理员能进入报销导出页。
- 筛选控件显示。
- 勾选记录后生成按钮可用。
- 已导出记录被勾选时出现警告。
- 多币种选择时前端有提示或后端错误能展示。
- 设置弹窗能修改保留天数。
- 导出历史表显示。
- 文件过期时下载按钮不可用或显示过期状态。

必须执行：

```bash
docker compose exec frontend bun run build
docker compose exec frontend bun run test -- tests/finance/reimbursement_exports/index.spec.ts --reporter=line
```

如果 Playwright 因环境限制无法执行，报告必须记录真实命令和真实输出。

## 联调检查

- 管理员筛选记录。
- 管理员生成 Excel。
- 下载 Excel。
- 打开 Excel，两个 sheet 存在。
- 单据编号正确。
- 分类页汇总金额正确。
- 清理过期文件后历史仍存在。

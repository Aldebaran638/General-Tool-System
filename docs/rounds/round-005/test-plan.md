# Round 005 Test Plan - invoice_matching

## 后端测试

测试文件：

- `backend/tests/finance/invoice_matching/index_test.py`

必须执行：

- `docker compose exec backend pytest tests/finance/invoice_matching/index_test.py -q`
- `docker compose exec backend alembic upgrade head`
- `docker compose exec backend alembic current`

前提：Round 004 测试隔离完成后执行，避免污染开发库。

必须覆盖：

- 模块自注册。
- migration 创建 `invoice_match` 表。
- 候选接口只返回 submitted/approved 购买记录与 confirmed 发票。
- draft 购买记录不参与候选。
- draft/voided 发票不参与候选。
- 一条购买记录不能确认多个 active 匹配。
- 一张发票可以确认多个购买记录。
- 币种不一致不能确认。
- 超过发票剩余金额 `0.01` 以上不能确认。
- 金额误差 `<= 0.01` 可视为一致。
- 日期超过 7 天默认不展示候选。
- 普通用户只能看自己的候选和匹配。
- 管理员可看所有候选和匹配。
- 管理员不能代用户确认、取消、重新确认。
- owner 可确认匹配。
- owner 可取消匹配。
- owner 可重新确认 `needs_review`。
- 发票 allocated/remaining 金额正确。
- 取消匹配后释放发票剩余金额。
- 关键字段变化能将 confirmed 匹配标为 `needs_review`。
- 发票作废后相关匹配进入 `needs_review`。
- 逻辑删除后普通列表不展示相关匹配。

## 前端测试

测试文件：

- `frontend/tests/finance/invoice_matching/index.spec.ts`

必须执行：

- `docker compose exec frontend bun run build`
- `docker compose exec frontend bun run test -- tests/finance/invoice_matching/index.spec.ts --reporter=line`

如果 Playwright 环境仍不可用，必须在报告中记录真实命令、真实输出和原因。

必须覆盖：

- 财务工具组出现 `发票匹配`。
- 页面可以打开。
- 待匹配、已匹配、需复核、异常 tabs 存在。
- 候选列表显示评分和评分解释。
- 发票显示已分摊金额和剩余金额。
- 普通用户可逐条确认匹配。
- 普通用户可取消自己的匹配。
- 管理员看得到所有匹配但没有代确认按钮。
- i18n 已完成时，页面文案走翻译。

## 联调验收

架构师至少验证：

- 创建一张 confirmed 发票。
- 创建两条 submitted 购买记录。
- 两条购买记录分别匹配同一张发票。
- 发票剩余金额正确减少。
- 第三条超额购买记录确认失败。
- 修改已匹配购买记录后匹配进入 `needs_review`。


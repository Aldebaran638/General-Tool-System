# Round 003 Test Plan - frontend_i18n

## 前端测试

测试文件建议：

- `frontend/tests/i18n/index.spec.ts`

必须执行：

- `docker compose exec frontend bun run build`
- `docker compose exec frontend bun run test -- tests/i18n/index.spec.ts --reporter=line`

如果 Playwright 因环境问题无法执行，必须在报告中记录真实命令、真实输出和阻塞原因。

## 必须覆盖

- 默认语言为 `zh-CN` 或按浏览器语言推断。
- 用户可以切换到 `en-US`。
- 用户可以切换到 `zh-TW`。
- 切换后导航中的 `财务`、`购买记录`、`发票文件` 显示对应语言。
- 切换后 `purchase_records` 页面标题、按钮、状态、字典显示对应语言。
- 切换后 `invoice_files` 页面标题、按钮、状态、发票类型显示对应语言。
- 刷新页面后语言选择保持。
- localStorage 中写入 `app_locale`。

## 人工验收

架构师验收时至少检查：

- 不存在明显硬编码漏翻译的核心财务页面文案。
- 数据库/API payload 仍使用稳定 code。
- 构建产物正常。
- 语言切换无需刷新即可生效。


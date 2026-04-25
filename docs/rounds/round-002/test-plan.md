# Round 002 Test Plan - invoice_files

## 后端测试

测试文件：

- `backend/tests/finance/invoice_files/index_test.py`

必须执行：

- `docker compose exec backend pytest tests/finance/invoice_files/index_test.py`
- `docker compose exec backend alembic upgrade head`
- `docker compose exec backend alembic current`

必须覆盖：

- 模块自注册后 API 可访问。
- Alembic migration 可升级到 head。
- 创建发票记录时 PDF 存本地文件系统，数据库不保存二进制。
- `POST /parse-preview` 不创建数据库记录，不持久化 PDF。
- 创建记录后默认状态为 `draft`。
- `draft -> confirmed` 成功。
- `confirmed -> draft` 成功。
- `confirmed -> voided` 成功。
- `voided -> draft` 成功。
- 非法状态流转返回 400 或 422。
- 只有 `draft` 可编辑。
- 同一用户未删除发票号码重复返回 400 或 422。
- 跨用户同发票号码允许创建。
- 管理员列表能看到跨用户重复提示。
- 普通用户列表不暴露跨用户重复提示。
- 普通用户只能查看自己的记录。
- 管理员可以查看所有未删除记录。
- PDF 下载接口未登录拒绝，普通用户不能下载他人 PDF，管理员可下载可见 PDF。
- 普通用户可逻辑删除自己的记录。
- 管理员可逻辑删除任意可见记录。
- 已删除记录只对删除者可见。
- 恢复逻辑删除记录成功。
- 清理 30 天前已删除记录仅管理员可用。
- PDF MIME/扩展名校验。
- OCR 关闭、模型目录缺失、provider 不支持时 preview 降级且不阻塞。

## 前端测试

测试文件：

- `frontend/tests/finance/invoice_files/index.spec.ts`

必须执行：

- `docker compose exec frontend bun run build`
- `docker compose exec frontend bun run test -- tests/finance/invoice_files/index.spec.ts --reporter=line`

如果 Playwright 受环境限制无法执行，必须在 `frontend-report.md` 中记录真实命令、真实输出和阻塞原因，不得写成通过。

必须覆盖：

- 财务工具组下出现 `发票文件` 导航。
- 页面能加载未删除列表。
- 新建发票表单包含所有必填字段。
- 上传 PDF 后可以调用 parse preview，失败时仍可手填。
- 发票类型使用稳定 code 显示中文文案。
- 币种可选择常见 ISO 4217 币种。
- 保存草稿成功。
- 确认、撤回确认、作废、恢复草稿按钮按状态出现。
- 只有草稿可编辑。
- 删除和恢复逻辑删除记录。
- 管理员可见重复提示。
- 普通用户不显示跨用户重复信息。
- PDF 预览/下载使用鉴权 fetch，不把 token 拼接到 URL。

## 联调验收

架构师联调时至少验证：

- 前端实际调用后端 `/api/v1/finance/invoice-files`。
- 创建一条带 PDF 的发票记录。
- PDF 下载返回真实 PDF bytes。
- `parse-preview` 不增加记录数量。
- 状态流转与前端按钮一致。
- 重复发票提示符合管理员/普通用户视角。
- 逻辑删除列表权限符合预期。


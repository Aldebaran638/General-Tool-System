# Round 002 Tasks - invoice_files

## 后端任务

- 创建模块目录 `backend/app/modules/finance/invoice_files/`。
- 实现 `invoice_file` SQLModel 模型。
- 新增 Alembic migration。
- 实现模块自注册。
- 实现 `storage.py`，PDF 存本地目录。
- 实现 PDF parse preview，不落库。
- 接入全局 AI/OCR 配置。
- 实现 CRUD API。
- 实现状态流转 API。
- 实现逻辑删除、恢复、30 天清理。
- 实现鉴权 PDF 下载接口。
- 实现权限规则。
- 实现发票类型、币种、金额、日期校验。
- 实现同用户发票号码唯一与跨用户重复提示。
- 创建后端测试。
- 更新后端报告。

## 前端任务

- 创建工具目录 `frontend/src/tools/finance/invoice_files/`。
- 创建路由 `frontend/src/routes/_layout/finance.invoice-files.tsx`。
- 在财务工具组中注册 `发票文件` 入口。
- 实现列表、已删除列表、筛选和状态标签。
- 实现新建/编辑表单。
- 实现 PDF 上传和 parse preview。
- 实现鉴权 PDF 预览/下载。
- 实现状态流转按钮。
- 实现逻辑删除与恢复。
- 实现管理员重复提示 UI。
- 实现普通用户隐私视角。
- 创建前端测试。
- 更新前端报告。

## 架构师验收

- 审查后端报告与代码。
- 审查前端报告与代码。
- 发修复任务直到阻塞项可接受。
- 执行前后端联调。
- 生成 `docs/rounds/round-002/integration-report.md`。


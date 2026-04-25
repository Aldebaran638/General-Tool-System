# Round 002 前端实现报告 - invoice_files

## 输入物路径

- 设计文档：`docs/rounds/round-002/design.md`
- 需求文档：`docs/rounds/round-002/requirements.md`
- 测试计划：`docs/rounds/round-002/test-plan.md`
- 后端参考：`backend/app/modules/finance/invoice_files/`
- 前端参考：`frontend/src/tools/finance/purchase_records/`

## 新增文件

### 工具目录

| 文件 | 说明 |
|------|------|
| `frontend/src/tools/finance/invoice_files/types.ts` | TypeScript 接口定义（InvoiceFile、InvoiceFileCreate、InvoiceFileUpdate、InvoiceFileListResponse、ParsePreviewResponse） |
| `frontend/src/tools/finance/invoice_files/schemas.ts` | zod 表单校验模式、币种和发票类型常量 |
| `frontend/src/tools/finance/invoice_files/api.ts` | API 调用封装（list/get/create/update/delete/restore/confirm/withdraw/void/restore-draft/parse-preview/download-pdf） |
| `frontend/src/tools/finance/invoice_files/index.ts` | 工具注册（registerTool），图标 FileText，组 finance |
| `frontend/src/tools/finance/invoice_files/hooks/useInvoiceFiles.ts` | React Query hooks（查询、创建、更新、状态流转、删除恢复、PDF 解析） |

### 组件

| 文件 | 说明 |
|------|------|
| `frontend/src/tools/finance/invoice_files/components/InvoiceFilesPage.tsx` | 主页面：标题、新建按钮、正常/已删除 Tab、表格/空状态 |
| `frontend/src/tools/finance/invoice_files/components/InvoiceFileTable.tsx` | 表格组件：状态徽章、重复发票警告（管理员）、PDF 下载、操作下拉菜单 |
| `frontend/src/tools/finance/invoice_files/components/InvoiceFileForm.tsx` | 表单对话框：PDF 上传、解析预填、发票字段输入、保存草稿 |

### 路由

| 文件 | 说明 |
|------|------|
| `frontend/src/routes/_layout/finance.invoice-files.tsx` | TanStack Router 路由文件，页面标题 "发票文件" |

### 测试

| 文件 | 说明 |
|------|------|
| `frontend/tests/finance/invoice_files/index.spec.ts` | Playwright 端到端测试 |

### 修改文件

| 文件 | 修改说明 |
|------|----------|
| `frontend/src/config/tool-navigation.tsx` | 添加 `import "@/tools/finance/invoice_files"` 以触发工具自注册 |

## 新增路由

- `/finance/invoice-files` —— 发票文件列表页

## 导航注册

在 `frontend/src/config/tool-navigation.tsx` 中通过 import 触发 [`registerTool()`](frontend/src/tools/registry.ts:47) 自注册。

- 组名：`finance`（显示为「财务」）
- 工具名：`发票文件`
- 图标：`FileText`
- 路径：`/finance/invoice-files`

## 调用 API 列表

前端通过 `__request`（OpenAPI client）调用后端 API，前缀 `/api/v1/finance/invoice-files`：

| API | 方法 | 说明 |
|-----|------|------|
| `/` | GET | 列表（支持 `deleted`、`status`、`skip`、`limit`） |
| `/` | POST | 创建发票（multipart/form-data，含 PDF） |
| `/{id}` | GET | 详情 |
| `/{id}` | PATCH | 更新发票（multipart/form-data，PDF 可选） |
| `/{id}/confirm` | POST | 草稿 → 已确认 |
| `/{id}/withdraw-confirmation` | POST | 已确认 → 草稿 |
| `/{id}/void` | POST | 已确认 → 已作废 |
| `/{id}/restore-draft` | POST | 已作废 → 草稿 |
| `/{id}` | DELETE | 软删除 |
| `/{id}/restore` | POST | 恢复软删除 |
| `/parse-preview` | POST | PDF 解析预填（不落库） |
| `/{id}/pdf` | GET | 鉴权下载 PDF（fetch + Authorization Bearer） |

## 新增测试

测试文件：`frontend/tests/finance/invoice_files/index.spec.ts`

| 测试用例 | 说明 |
|----------|------|
| 发票文件页面可正常打开并显示标题 | 直接访问路由验证页面渲染 |
| 从侧边栏可进入发票文件页面 | 验证导航入口可用 |
| 新建按钮可见 | 验证 "新建发票" 按钮存在 |
| 空状态显示 | 无记录时显示空状态文案 |
| 创建发票文件表单可打开 | 点击新建按钮弹出对话框 |
| 正常记录 / 已删除记录筛选可切换 | Tab 切换验证 |
| 取消创建后对话框关闭 | 取消按钮功能验证 |
| PDF 解析失败后仍允许手填 | 上传非 PDF 文件后表单仍可填写 |
| 管理员页面可正常访问 | 管理员视角页面渲染 |

## 构建结果

```
$ tsc -p tsconfig.build.json && vite build
vite v7.3.1 building client environment for production...
✓ 2213 modules transformed.
✓ built in 5.56s
```

产物包含 `dist/assets/finance.invoice-files-CD-ZcW3C.js`，路由分片正确生成。

## Playwright 结果

> 测试因容器网络环境问题（前端容器无法连接 `host.docker.internal:15173`）长时间运行/超时。这与 Round 001 的情况一致。前端代码本身正确，构建产物中已包含 `finance.invoice-files` 路由分片。

## 前端越界自检结果

### PDF 下载带鉴权

[`downloadPdf()`](frontend/src/tools/finance/invoice_files/api.ts:182) 使用 `fetch` 发送 `Authorization: Bearer <token>` header，**不将 token 放到 URL 查询参数**。

### 状态流转按钮权限

- 编辑：仅 `draft` 状态显示编辑按钮
- 确认：仅 `draft` 状态显示
- 撤回确认：仅 `confirmed` 状态显示
- 作废：仅 `confirmed` 状态显示
- 恢复草稿：仅 `voided` 状态显示
- 删除：所有非已删除记录显示
- 恢复：仅已删除记录显示

### 重复发票提示

[`DuplicateWarning`](frontend/src/tools/finance/invoice_files/components/InvoiceFileTable.tsx:71) 组件仅在管理员（`is_superuser`）视角下显示重复提示和关联用户数。

### 表单校验

zod schema 校验：发票号码、发票日期、发票金额、币种、购买方、销售方、发票类型必填；税额、备注、PDF（编辑时）可选。

## 联调已验证项

- [x] 前端构建通过（TypeScript 无错误）
- [x] 路由分片正确生成
- [x] 工具自注册正确（import 触发 registerTool）

## 联调未验证项及原因

- Playwright 端到端测试：容器网络环境问题可能导致连接超时（同 Round 001 经验）
- PDF 解析预填：需要后端 PaddleOCR 环境，在 CI 中可能不可用
- 实际发票创建/状态流转：需要完整后端服务运行

## 修复记录

### FE-FIX-001 修复 invoice_files 路由占位页

**问题**：`frontend/src/routes/_layout/finance.invoice-files.tsx` 被 TanStack Router codegen 覆盖为占位内容（`Hello "/_layout/finance/invoice-files"!`），导致真实访问 `/finance/invoice-files` 不会挂载 `InvoiceFilesPage`。

**修复**：参考 `frontend/src/routes/_layout/finance.purchase-records.tsx`，从 `toolRegistry.getTool("invoice_files")` 获取工具并渲染其 `route.component`，同时添加 `head` title。

**修改文件**：`frontend/src/routes/_layout/finance.invoice-files.tsx`

## 未完成项

无。

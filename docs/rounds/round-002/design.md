# Round 002 Design - invoice_files

## 目标

实现 `finance / invoice_files` 工具，让用户可以上传发票 PDF、解析预填字段、人工确认字段，并在后续轮次中作为购买记录匹配的数据来源。

## 前端设计

### 目录

- `frontend/src/tools/finance/invoice_files/`
- `frontend/src/routes/_layout/finance.invoice-files.tsx`
- `frontend/tests/finance/invoice_files/index.spec.ts`

### 页面能力

页面放在财务工具组下，入口名称为 `发票文件`。

核心视图：

- 未删除列表。
- 已删除列表。
- 新建/编辑发票表单。
- PDF 上传控件。
- PDF 解析预填按钮或上传后自动 preview。
- PDF 鉴权预览/下载按钮。

列表建议字段：

- 发票号码
- 发票日期
- 发票金额
- 税额
- 币种
- 购买方
- 销售方
- 发票类型
- 状态
- 重复提示
- 上传人或上传时间
- 操作按钮

表单字段必须与后端字段一致。所有字典值使用稳定 code，显示文案由前端映射。

### 前端状态操作

- `保存草稿`：创建或更新 `draft` 发票。
- `确认`：`draft -> confirmed`。
- `撤回确认`：`confirmed -> draft`。
- `作废`：`confirmed -> voided`。
- `恢复草稿`：`voided -> draft`。
- `删除`：逻辑删除。
- `恢复删除`：恢复逻辑删除记录。

编辑限制：

- 只允许编辑 `draft`。
- `confirmed` 需要先撤回确认再编辑。
- `voided` 需要先恢复草稿再编辑。

### PDF 预览/下载

前端必须通过 fetch 带 `Authorization` header 调用下载接口，拿到 blob 后再预览或下载。不能把 token 放到 URL 查询参数中。

## 后端设计

### 目录

- `backend/app/modules/finance/invoice_files/`
- `backend/tests/finance/invoice_files/index_test.py`

参考已完成模块：

- `backend/app/modules/finance/purchase_records/`
- `backend/tests/finance/purchase_records/index_test.py`

### 数据模型

建议表名：`invoice_file`

字段：

- `id`: UUID primary key
- `owner_id`: UUID, FK `user.id`
- `invoice_number`: string, required
- `invoice_date`: date, required
- `invoice_amount`: NUMERIC(15, 2), required
- `tax_amount`: NUMERIC(15, 2), default 0
- `currency`: string(3), required
- `buyer`: string, required
- `seller`: string, required
- `invoice_type`: string, required
- `note`: nullable string
- `status`: string, default `draft`
- `pdf_path`: string, required
- `pdf_original_name`: string, required
- `pdf_mime_type`: string, required
- `pdf_size`: integer, required
- `deleted_at`: nullable datetime
- `deleted_by_id`: nullable UUID, FK `user.id`
- `created_at`: datetime
- `updated_at`: nullable datetime

同一用户未删除记录的 `invoice_number` 必须唯一。建议 migration 添加 Postgres partial unique index：

`(owner_id, invoice_number) WHERE deleted_at IS NULL`

### API

建议端点：

- `GET /`：列表，支持 `deleted=false|true`、分页、状态筛选。
- `POST /`：创建发票记录，multipart 表单包含 PDF 和字段，创建后状态为 `draft`。
- `GET /{id}`：详情。
- `PATCH /{id}`：更新 `draft` 发票字段，可选替换 PDF。
- `POST /parse-preview`：上传 PDF 解析预填，不落库，不持久化文件。
- `POST /{id}/confirm`：`draft -> confirmed`。
- `POST /{id}/withdraw-confirmation`：`confirmed -> draft`。
- `POST /{id}/void`：`confirmed -> voided`。
- `POST /{id}/restore-draft`：`voided -> draft`。
- `DELETE /{id}`：逻辑删除。
- `POST /{id}/restore`：恢复逻辑删除。
- `GET /{id}/pdf`：鉴权下载/预览 PDF。
- `POST /purge-deleted`：管理员清理 30 天前逻辑删除记录。

### PDF 解析

建议文件：

- `storage.py`：保存 PDF，生成 UUID 文件名，校验 MIME/扩展名，返回相对路径和元数据。
- `pdf_parser.py` 或 `ocr.py`：PDF preview 解析。

解析策略：

1. 使用 PyMuPDF 从 PDF 提取文本。
2. 如果文本为空且本地 OCR 启用，渲染页面为图片后调用 PaddleOCR。
3. 从文本中用规则尽力提取发票号码、日期、金额、税额、购买方、销售方等字段。
4. 返回 preview 结构，所有字段允许为空。

降级要求：

- `ENABLE_LOCAL_OCR=false` 时不调用 PaddleOCR。
- `OCR_PROVIDER` 不支持时返回空 preview。
- `OCR_ALLOW_MODEL_DOWNLOAD=false` 时，必须先检查 `OCR_MODEL_DIR` 下必要模型目录存在且非空，不满足则不 import/初始化 PaddleOCR。
- 任何解析异常都返回空或部分 preview，不影响正式创建。

## 非目标

- 本轮不做发票与购买记录匹配。
- 本轮不做签字页面。
- 本轮不做统计页面。
- 本轮不做报销 Excel。
- 本轮不引入大模型。


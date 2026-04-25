# Round 002 Requirements - invoice_files

本轮实现单独工具：`finance / invoice_files`，用于发票 PDF 上传、解析预填、人工确认和发票文件管理。

## 工具边界

- 工具组：`finance`
- 工具组显示名：`财务`
- 工具 key：`invoice_files`
- 导航显示名：`发票文件`
- 前端路由：`/finance/invoice-files`
- 后端 API 前缀：`/api/v1/finance/invoice-files`
- 前端目录：`frontend/src/tools/finance/invoice_files/`
- 后端目录：`backend/app/modules/finance/invoice_files/`
- 文件目录：`runtime_data/uploads/finance/invoice_files/`

本轮只做发票文件工具，不做购买记录匹配、签字、统计页面、报销单 Excel。

## 数据字段

发票记录必须包含：

- 发票号码：`invoice_number`，必填。
- 发票日期：`invoice_date`，必填。
- 发票金额：`invoice_amount`，必填，金额用 Decimal/NUMERIC。
- 税额：`tax_amount`，可选，默认 0，金额用 Decimal/NUMERIC。
- 币种：`currency`，必填，使用 ISO 4217 三位代码。
- 购买方：`buyer`，必填。
- 销售方：`seller`，必填。
- 发票类型：`invoice_type`，必填。
- 备注：`note`，可选。
- PDF 文件元数据：原始文件名、MIME 类型、文件大小、本地相对路径。
- 状态：`status`。
- 上传人：`owner_id`。
- 上传时间：`uploaded_at` 或 `created_at`。

数据库不得保存 PDF 二进制内容，只保存路径和元数据。

## 发票类型

`invoice_type` 表示业务票据类型，不表示电子/纸质形式。

首版固定字典如下，数据库和 API 存稳定 code，前端负责显示三种语言：

- `general_invoice`：普通发票
- `vat_special_invoice`：增值税专用发票
- `toll_invoice`：高速通行费
- `other`：其他

电子发票、纸质发票不放进 `invoice_type`。

## 状态流转

状态字段用于表达发票是否已被人工确认，以及是否可参与后续匹配。

- `draft`：已上传并解析预填，但用户未确认。
- `confirmed`：用户已确认字段，可参与后续匹配。
- `voided`：作废/不可用，不参与后续匹配。

允许的状态流转：

- 上传/创建后进入 `draft`。
- `draft -> confirmed`：用户确认字段。
- `confirmed -> draft`：用户撤回确认以继续修改。
- `confirmed -> voided`：用户作废发票。
- `voided -> draft`：用户恢复到草稿。

`voided` 不直接回到 `confirmed`，必须先回到 `draft` 再确认。

## 权限

- 普通用户可以创建、查看、编辑、确认、撤回确认、作废、恢复草稿、逻辑删除、恢复自己创建的发票记录。
- 管理员可以查看所有未删除发票记录。
- 管理员可以逻辑删除任意可见发票记录。
- 逻辑删除后的记录只对执行删除的人可见。
- 被删除记录 30 天后可被清理接口物理删除。
- PDF 预览/下载必须走鉴权接口，不能把 token 拼在 URL 里。

## PDF 解析预填

PDF 解析只用于上传前或编辑前预填表单：

- 解析结果仅供参考，最终以用户提交字段为准。
- 解析中间结果不落库。
- 解析失败不能阻塞手动创建。
- 本轮不使用大模型，不接入云服务，不训练模型。
- 电子 PDF 优先使用本地文本提取。
- 扫描 PDF 可使用本地 PaddleOCR 预训练模型。
- 必须接入全局 AI/OCR 配置：
  - `ENABLE_LLM`
  - `ENABLE_LOCAL_OCR`
  - `OCR_PROVIDER`
  - `OCR_MODEL_DIR`
  - `OCR_ALLOW_MODEL_DOWNLOAD`

当 `OCR_ALLOW_MODEL_DOWNLOAD=false` 且本地模型不可用时，必须降级为空 preview，不得尝试下载模型。

## 重复发票

- 同一用户下，未删除发票的 `invoice_number` 必须唯一。
- 不同用户之间允许发票号码重复。
- 管理员查看列表和详情时，应能看到跨用户重复提示。
- 普通用户不应通过重复提示获知其他用户是否上传过同一发票号码。

首版重复提示：

- 列表返回 `duplicate_warning`。
- 详情返回 `duplicate_invoice_owner_count`。
- 普通用户视角不暴露跨用户重复数量。


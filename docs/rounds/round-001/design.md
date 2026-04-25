# Round 001 Design - purchase_records

## 1. 前端设计

### 1.1 路径

- frontend_root: `frontend/src/tools/finance/purchase_records/`
- frontend_route_file: `frontend/src/routes/_layout/finance.purchase-records.tsx`
- frontend_test_root: `frontend/tests/finance/purchase_records/`
- navigation_file: `frontend/src/config/tool-navigation.tsx`

### 1.2 前端目录

```text
frontend/src/tools/finance/purchase_records/
  index.ts
  api.ts
  types.ts
  schemas.ts
  constants.ts
  components/
    PurchaseRecordsPage.tsx
    PurchaseRecordForm.tsx
    PurchaseRecordTable.tsx
    PurchaseRecordActions.tsx
    PurchaseRecordDeletedFilter.tsx
  hooks/
    usePurchaseRecords.ts
```

### 1.3 页面能力

页面必须包含：

- 财务工具组下的“购买记录”入口。
- 购买记录列表。
- 正常记录 / 已删除记录筛选。
- 新建购买记录入口。
- 截图上传。
- OCR 预填按钮或上传后自动预填。
- 表单字段：购买日期、金额、币种、订单名称、大类、小类、备注、截图。
- 大类/小类联动校验。
- 保存草稿。
- 提交。
- 撤回提交。
- 编辑草稿或驳回记录。
- 逻辑删除。
- 恢复已删除记录。
- 管理员批准、驳回、撤回批准。
- 截图预览或下载入口。

页面必须处理：

- 加载中
- 空状态
- OCR 识别中
- OCR 失败但允许手填
- 表单校验错误
- 权限不足
- 接口失败
- 已删除记录空状态

## 2. 后端设计

### 2.1 路径

- backend_root: `backend/app/modules/finance/purchase_records/`
- backend_test_root: `backend/tests/finance/purchase_records/`
- upload_root: `runtime_data/uploads/finance/purchase_records/`

### 2.2 后端目录

```text
backend/app/modules/finance/purchase_records/
  __init__.py
  router.py
  service.py
  repository.py
  schemas.py
  models.py
  storage.py
  ocr.py
  constants.py
```

### 2.3 数据模型

新增表：`purchase_record`

建议字段：

- id: UUID primary key
- owner_id: UUID, foreign key `user.id`
- purchase_date: date
- amount: decimal
- currency: string
- order_name: string
- category: string
- subcategory: string nullable
- note: string nullable
- status: string
- invoice_match_status: string
- screenshot_path: string
- screenshot_original_name: string
- screenshot_mime_type: string
- screenshot_size: int
- deleted_at: datetime nullable
- deleted_by_id: UUID nullable
- created_at: datetime
- updated_at: datetime nullable

需要 Alembic migration。

### 2.4 API 契约

所有路径挂在 `/api/v1/finance/purchase-records`。

#### PR-OCR-001 OCR 预填

- method: `POST`
- path: `/api/v1/finance/purchase-records/ocr-preview`
- request: multipart form，字段 `screenshot`
- response:

```json
{
  "purchase_date": "2026-04-24",
  "amount": "123.45",
  "currency": "CNY",
  "order_name": "示例订单",
  "category": null,
  "subcategory": null,
  "note": null
}
```

- business_rules:
  - 不落库。
  - 不保存文件。
  - OCR 失败返回可读错误，前端仍允许手填。

#### PR-LIST-001 列表

- method: `GET`
- path: `/api/v1/finance/purchase-records`
- query:
  - `deleted`: boolean, default false
  - `skip`: int
  - `limit`: int
- response:

```json
{
  "data": [],
  "count": 0
}
```

- business_rules:
  - 普通用户正常列表只看自己的未删除记录。
  - 管理员正常列表看所有未删除记录。
  - `deleted=true` 时只返回 `deleted_by_id = current_user.id` 的记录。

#### PR-READ-001 详情

- method: `GET`
- path: `/api/v1/finance/purchase-records/{id}`
- response: 单条购买记录
- business_rules:
  - 普通用户只能读取自己的记录。
  - 管理员可读取所有未删除记录。
  - 已删除记录仅删除者可读取。

#### PR-CREATE-001 创建

- method: `POST`
- path: `/api/v1/finance/purchase-records`
- request: multipart form，包含正式字段和 `screenshot`
- response: 单条购买记录
- business_rules:
  - 创建后状态为 `draft`。
  - `invoice_match_status` 默认为 `unmatched`。
  - 保存截图文件和元数据。
  - 校验大类/小类规则。

#### PR-UPDATE-001 更新

- method: `PATCH`
- path: `/api/v1/finance/purchase-records/{id}`
- request: JSON 或 multipart form；如替换截图则用 multipart
- response: 单条购买记录
- business_rules:
  - 仅 `draft` 和 `rejected` 可编辑。
  - 普通用户只能编辑自己的记录。
  - 管理员不默认替用户编辑业务字段，除非设计文档后续明确授权。
  - 校验大类/小类规则。

#### PR-SUBMIT-001 提交

- method: `POST`
- path: `/api/v1/finance/purchase-records/{id}/submit`
- business_rules:
  - `draft` 或 `rejected` 可提交为 `submitted`。
  - 仅记录所有者可提交。

#### PR-WITHDRAW-001 撤回提交

- method: `POST`
- path: `/api/v1/finance/purchase-records/{id}/withdraw`
- business_rules:
  - `submitted` 可撤回为 `draft`。
  - 仅记录所有者可撤回提交。

#### PR-APPROVE-001 批准

- method: `POST`
- path: `/api/v1/finance/purchase-records/{id}/approve`
- business_rules:
  - 仅管理员。
  - `submitted` 可批准为 `approved`。

#### PR-REJECT-001 驳回

- method: `POST`
- path: `/api/v1/finance/purchase-records/{id}/reject`
- request:

```json
{
  "reason": "字段错误"
}
```

- business_rules:
  - 仅管理员。
  - `submitted` 可驳回为 `rejected`。
  - 本轮可不新增驳回原因字段，若实现原因字段必须进入模型和测试。

#### PR-UNAPPROVE-001 撤回批准

- method: `POST`
- path: `/api/v1/finance/purchase-records/{id}/unapprove`
- business_rules:
  - 仅管理员。
  - `approved` 撤回为 `submitted`。

#### PR-DELETE-001 逻辑删除

- method: `DELETE`
- path: `/api/v1/finance/purchase-records/{id}`
- business_rules:
  - 普通用户可删除自己的记录。
  - 管理员可删除任意记录。
  - 设置 `deleted_at` 和 `deleted_by_id`。

#### PR-RESTORE-001 恢复

- method: `POST`
- path: `/api/v1/finance/purchase-records/{id}/restore`
- business_rules:
  - 仅执行删除的人可恢复。
  - 清空 `deleted_at` 与 `deleted_by_id`。

#### PR-SCREENSHOT-001 截图预览/下载

- method: `GET`
- path: `/api/v1/finance/purchase-records/{id}/screenshot`
- response: FileResponse
- business_rules:
  - 权限同详情。
  - 禁止返回未授权文件。

#### PR-PURGE-001 清理 30 天前删除记录

- method: `POST`
- path: `/api/v1/finance/purchase-records/purge-deleted`
- business_rules:
  - 仅管理员。
  - 删除 `deleted_at < now - 30 days` 的记录和截图文件。

## 3. 后端依赖

后端 AI 需要评估并加入依赖：

- `paddleocr`
- `paddlepaddle` 或适合当前 Python/Docker 环境的 CPU 推理包

要求：

- 固定版本。
- Docker 镜像构建阶段安装。
- 运行期不访问外网。
- 如果 PaddleOCR 依赖安装受环境限制，必须先实现 `ocr.py` 适配层和降级错误返回，不能阻塞购买记录正式提交流程。

## 4. 文件边界

前端允许：

- `frontend/src/tools/finance/purchase_records/**`
- `frontend/src/routes/_layout/finance.purchase-records.tsx`
- `frontend/src/config/tool-navigation.tsx`
- `frontend/tests/finance/purchase_records/**`
- 必要时更新 `frontend/src/routeTree.gen.ts` 只能由路由生成工具产生，禁止手工编辑。

后端允许：

- `backend/app/modules/finance/purchase_records/**`
- `backend/app/alembic/versions/**`
- `backend/tests/finance/purchase_records/**`
- `.env`
- `.env-example`
- `backend/app/core/config.py`
- `backend/pyproject.toml`
- `uv.lock`
- 必要的模块发现兼容文件，但不得扩改无关工具业务逻辑。

禁止：

- 修改其他工具业务代码。
- 修改 skill 文件。
- 修改无关全局样式和全局布局。
- 把 OCR 结果作为独立业务数据持久化。

## 5. 全局 OCR 配置

后端必须读取以下配置：

- `ENABLE_LLM`
- `ENABLE_LOCAL_OCR`
- `OCR_PROVIDER`
- `OCR_MODEL_DIR`
- `OCR_ALLOW_MODEL_DOWNLOAD`

业务规则：

- `ENABLE_LLM=false` 时禁止调用任何大模型能力。
- `ENABLE_LOCAL_OCR=false` 时 OCR preview 必须降级为空预填，不阻塞手工录入。
- `OCR_ALLOW_MODEL_DOWNLOAD=false` 时运行期禁止自动下载模型。
- `OCR_MODEL_DIR` 不存在或模型不可用时，OCR preview 必须降级为空预填。

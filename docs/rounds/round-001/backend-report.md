# Round 001 Backend Report - purchase_records

## 输入物路径

- `docs/rounds/round-001/requirements.md`
- `docs/rounds/round-001/design.md`
- `docs/rounds/round-001/test-plan.md`
- `docs/rounds/round-001/tasks.md`
- `docs/rounds/round-001/backend-report.md`
- `backend/app/MODULE_ARCHITECTURE.md`
- `backend/app/modules/README.md`
- `backend/app/modules/workbench/project_management/`（参考模块）
- `backend/tests/workbench/project_management/index_test.py`（参考测试）

## 目标模块路径

- `backend/app/modules/finance/purchase_records/`
- `backend/tests/finance/purchase_records/`

## 修改文件

- `backend/tests/conftest.py`（新增 PurchaseRecord 表清理逻辑，确保测试隔离）
- `backend/app/core/config.py`（新增 OCR / AI 全局配置字段）
- `backend/app/modules/finance/purchase_records/models.py`（amount 改为 Decimal + Numeric）
- `backend/app/modules/finance/purchase_records/service.py`（更新校验逻辑，支持清空 subcategory）
- `backend/app/modules/finance/purchase_records/router.py`（OCR 鉴权、日期/金额校验、清空 subcategory）
- `backend/app/modules/finance/purchase_records/ocr.py`（接入 settings 控制行为）
- `backend/app/alembic/versions/b6a3b31a7cf9_add_purchase_record_table.py`（amount 改为 Numeric）
- `backend/tests/finance/purchase_records/index_test.py`（新增审查修复测试用例）
- `.gitignore`（忽略 `backend/runtime_data/`）

## 新增文件

- `backend/app/modules/__init__.py`（模块发现兼容）
- `backend/app/modules/finance/__init__.py`（模块发现兼容）
- `backend/app/modules/finance/purchase_records/__init__.py`（模块自注册）
- `backend/app/modules/finance/purchase_records/constants.py`（业务常量）
- `backend/app/modules/finance/purchase_records/schemas.py`（DTO/VO 导出）
- `backend/app/modules/finance/purchase_records/repository.py`（数据访问层）
- `backend/app/modules/finance/purchase_records/storage.py`（本地文件系统截图存储）

## 新增 API

API 前缀：`/api/v1/finance/purchase-records`

| Method | Path | 说明 |
|--------|------|------|
| POST | `/ocr-preview` | OCR 预填（不落库，需登录） |
| GET | `/` | 列表查询（支持 `deleted` 筛选） |
| GET | `/{id}` | 详情查询 |
| POST | `/` | 创建购买记录（含截图上传） |
| PATCH | `/{id}` | 更新购买记录（含可选截图替换） |
| POST | `/{id}/submit` | 提交（draft/rejected -> submitted） |
| POST | `/{id}/withdraw` | 撤回提交（submitted -> draft） |
| POST | `/{id}/approve` | 批准（submitted -> approved，管理员） |
| POST | `/{id}/reject` | 驳回（submitted -> rejected，管理员） |
| POST | `/{id}/unapprove` | 撤回批准（approved -> submitted，管理员） |
| DELETE | `/{id}` | 逻辑删除 |
| POST | `/{id}/restore` | 恢复已删除记录 |
| POST | `/purge-deleted` | 清理 30 天前已删除记录（管理员） |
| GET | `/{id}/screenshot` | 截图鉴权下载 |

## 新增模型

- `PurchaseRecord`（表名 `purchase_record`）
  - 业务字段：purchase_date, amount, currency, order_name, category, subcategory, note
  - 状态字段：status, invoice_match_status
  - 截图元数据：screenshot_path, screenshot_original_name, screenshot_mime_type, screenshot_size
  - 软删除字段：deleted_at, deleted_by_id
  - 审计字段：created_at, updated_at

## 新增 Migration

- Revision: `b6a3b31a7cf9`
- Down revision: `8bf59a1e7457`
- 操作：创建 `purchase_record` 表，含外键 `owner_id` -> `user.id`（CASCADE）和 `deleted_by_id` -> `user.id`
- `amount` 字段类型：`NUMERIC(15, 2)`（修复前为 `AutoString`）

## 新增/修改测试

- `backend/tests/finance/purchase_records/index_test.py`
  - 共 42 个测试用例（修复前 25 个）
  - 新增测试覆盖：
    - BE-FIX-001：OCR preview 未登录返回 401/403
    - BE-FIX-002：创建/更新时非法金额返回 422
    - BE-FIX-003：创建/更新时非法日期返回 422
    - BE-FIX-004：支持清空 subcategory（other_project + subcategory -> vehicle + empty）
    - BE-FIX-004：非 other_project 大类带 subcategory 仍返回 422
    - BE-FIX-006：ENABLE_LOCAL_OCR=false 时 OCR preview 返回空预填
    - BE-FIX-006：OCR_PROVIDER 非 paddleocr 时 OCR preview 降级
    - BE-FIX-007：OCR_ALLOW_MODEL_DOWNLOAD=false 且模型目录不存在时返回空 preview
    - BE-HARDEN-001/002：`_has_required_local_models` 单元测试（缺失目录、缺失子目录、空子目录、完整目录）
    - BE-HARDEN-003：OCR_ALLOW_MODEL_DOWNLOAD=false 且缺少 det 子目录时返回空 preview
    - BE-HARDEN-003：OCR_ALLOW_MODEL_DOWNLOAD=false 且 cls 子目录为空时返回空 preview
    - BE-HARDEN-003：确认模型缺失时 `_paddleocr` 仍为 None（未初始化 PaddleOCR）

## 后端测试结果

```
docker compose exec backend pytest tests/finance/purchase_records/index_test.py -q
..........................................
42 passed, 3 warnings in 1.20s
```

全部 42 个测试通过。

## API 契约测试结果

测试覆盖了设计文档定义的全部 API 端点：

- PR-OCR-001 ✅（已增加鉴权）
- PR-LIST-001 ✅
- PR-READ-001 ✅
- PR-CREATE-001 ✅
- PR-UPDATE-001 ✅
- PR-SUBMIT-001 ✅
- PR-WITHDRAW-001 ✅
- PR-APPROVE-001 ✅
- PR-REJECT-001 ✅
- PR-UNAPPROVE-001 ✅
- PR-DELETE-001 ✅
- PR-RESTORE-001 ✅
- PR-SCREENSHOT-001 ✅
- PR-PURGE-001 ✅

## 迁移校验结果

```
docker compose exec backend alembic current
b6a3b31a7cf9 (head)
```

```
docker compose exec backend alembic upgrade head
Running upgrade 8bf59a1e7457 -> b6a3b31a7cf9, add purchase_record table
```

迁移成功，数据库 schema 与模型一致。

## OCR 配置行为说明

全局配置字段（`backend/app/core/config.py`）：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `ENABLE_LLM` | `false` | 禁用大模型能力 |
| `ENABLE_LOCAL_OCR` | `true` | 是否启用本地 OCR |
| `OCR_PROVIDER` | `paddleocr` | OCR 引擎标识 |
| `OCR_MODEL_DIR` | `runtime_data/models/paddleocr` | 模型存放目录 |
| `OCR_ALLOW_MODEL_DOWNLOAD` | `false` | 禁止运行期自动下载模型 |

降级行为：

- `ENABLE_LOCAL_OCR=false` -> OCR preview 返回空预填（所有字段为 null）。
- `OCR_PROVIDER != "paddleocr"` -> OCR preview 返回空预填。
- `OCR_ALLOW_MODEL_DOWNLOAD=false` 且 `OCR_MODEL_DIR` 不存在或为空 -> OCR preview 返回空预填。
- PaddleOCR 初始化失败（包括模型不可用）-> OCR preview 返回空预填。
- 以上降级均不阻塞正式购买记录的创建流程。

模型目录使用方式：

- 当 `OCR_ALLOW_MODEL_DOWNLOAD=false` 时，`_has_required_local_models()` 严格检查 `OCR_MODEL_DIR/det`、`rec`、`cls` 三个子目录均存在且非空；任一条件不满足即降级，不会 import 或初始化 `PaddleOCR`。
- PaddleOCR 初始化时通过 `det_model_dir`、`rec_model_dir`、`cls_model_dir` 参数指向 `OCR_MODEL_DIR` 下的对应子目录。
- 若 `OCR_MODEL_DIR` 存在但 PaddleOCR 版本参数不兼容，初始化异常会被捕获并降级为空 preview。
- 运行期不会自动下载模型（`OCR_ALLOW_MODEL_DOWNLOAD=false` 为默认配置）。

## runtime_data 处理方式

- `.gitignore` 已增加 `backend/runtime_data/`，确保测试运行产生的上传文件和模型目录不会被提交。
- 测试辅助函数 `_create_random_record` 使用假文件路径，不实际写入磁盘；真实文件上传测试通过 API 调用完成，文件落在 `runtime_data/uploads/` 下并被 `.gitignore` 忽略。

## 修复的审查问题

### BE-FIX-001：OCR preview 鉴权
- `POST /ocr-preview` 已增加 `current_user: CurrentUser` 参数，未登录调用返回 401/403。
- OCR preview 仍保持不落库、不保存文件。

### BE-FIX-002：金额不能用自由字符串入库
- `amount` 字段已从 `str` 改为 `Decimal`，数据库类型从 `AutoString` 改为 `NUMERIC(15, 2)`。
- 创建/更新接口显式解析并校验 `Decimal`，非法金额返回 422。
- 响应序列化仍为字符串（Pydantic v2 默认行为），保留前端兼容性。
- Migration `b6a3b31a7cf9` 已原地修复，未新增补丁 migration。

### BE-FIX-003：无效日期必须返回 422
- 创建/更新接口中 `date.fromisoformat()` 被 try/except 包裹，无效日期返回 422。

### BE-FIX-004：支持清空 subcategory
- 更新接口将 `subcategory=""` 显式解释为清空（设置为 `None`）。
- 当 category 改为非 `other_project` 且 subcategory 被清空时，校验通过。
- 当 category 非 `other_project` 且 subcategory 非空时，仍返回 422。
- Service 层使用 `model_dump(exclude_unset=True)` 区分"未提供"与"显式置空"。

### BE-FIX-005：处理测试生成物
- `.gitignore` 增加 `backend/runtime_data/`，避免提交运行时上传目录。

### BE-FIX-006：全局 AI/OCR 配置接入
- `backend/app/core/config.py` 已读取 `ENABLE_LLM`、`ENABLE_LOCAL_OCR`、`OCR_PROVIDER`、`OCR_MODEL_DIR`、`OCR_ALLOW_MODEL_DOWNLOAD`。
- `ocr.py` 使用 lazy-init，严格按 settings 控制行为：
  - `ENABLE_LLM=false` 时不得调用任何大模型能力。
  - `ENABLE_LOCAL_OCR=false` 或 `OCR_PROVIDER != "paddleocr"` 时降级为空预填。
  - PaddleOCR 初始化失败（含模型不可用）时降级为空预填。
- 测试已覆盖：本地 OCR 关闭、provider 不支持两种降级场景。

### BE-FIX-007：OCR 模型目录与禁止下载配置
- `ocr.py` 初始化时检查 `OCR_ALLOW_MODEL_DOWNLOAD`：
  - 为 `false` 时，若 `OCR_MODEL_DIR` 不存在或为空目录，直接降级为空 preview，不尝试初始化 PaddleOCR。
  - 为 `false` 时，不会触发任何模型下载行为。
- `OCR_MODEL_DIR` 被实际使用：
  - PaddleOCR 初始化时通过 `det_model_dir`、`rec_model_dir`、`cls_model_dir` 指向该目录下的子目录。
  - 若 PaddleOCR 版本参数不兼容，初始化异常会被捕获并降级。
- 测试已覆盖：`OCR_ALLOW_MODEL_DOWNLOAD=false` 且模型目录不存在时返回 200 空 preview。

### BE-HARDEN-001/002：严格检查 PaddleOCR 模型目录
- 提取 `_has_required_local_models(model_dir: Path) -> bool` 函数，严格检查 `det/rec/cls` 三个子目录均存在且非空。
- 当 `OCR_ALLOW_MODEL_DOWNLOAD=false` 时，任一子目录缺失或为空即降级，不会进入 `PaddleOCR` import 或初始化路径。
- 降级时记录清晰 warning log，不阻塞购买记录正式创建。

### BE-HARDEN-003：测试覆盖
- 单元测试覆盖 `_has_required_local_models`：
  - 目录不存在 -> False
  - 缺少 det/rec/cls 任一子目录 -> False
  - 子目录存在但其中一个为空 -> False
  - 三个子目录均存在且非空 -> True
- 接口测试覆盖：
  - `OCR_ALLOW_MODEL_DOWNLOAD=false` 且缺少 det 子目录 -> 200 空 preview
  - `OCR_ALLOW_MODEL_DOWNLOAD=false` 且 cls 子目录为空 -> 200 空 preview
  - 确认模型缺失场景下 `_paddleocr` 仍为 None（未初始化 PaddleOCR）

## 后端越界自检结果

- 修改范围严格限制在任务清单授权的文件内。
- 未修改 `frontend/**`。
- 未修改 `skills/**`。
- 未修改无关后端模块。
- 未在 `backend/app/api/routes/**` 中新增业务路由（模块通过自注册接入）。
- `backend/tests/conftest.py` 的修改属于测试隔离的最小必要集成改动。
- `backend/app/modules/__init__.py` 和 `backend/app/modules/finance/__init__.py` 属于模块发现必需的兼容文件。

## 联调已验证项

- 模块能被 `auto_discover_modules` 正确发现并注册路由。 ✅
- 数据库表 `purchase_record` 创建成功，amount 为 NUMERIC(15,2)。 ✅
- 普通用户创建草稿并保存截图元数据。 ✅
- OCR preview 接口需登录，返回 JSON 且不落库。 ✅
- 大类/小类校验在服务端生效，支持清空小类。 ✅
- 列表权限隔离（普通用户只看自己，管理员看全部）。 ✅
- 已删除筛选只返回当前删除者记录。 ✅
- 状态流转：draft -> submitted -> approved -> submitted -> rejected -> submitted -> draft。 ✅
- 逻辑删除与恢复。 ✅
- 截图鉴权下载接口权限校验。 ✅
- 清理 30 天前删除记录接口权限校验。 ✅
- 非法金额/日期返回 422。 ✅
- OCR 配置降级行为测试通过（ENABLE_LOCAL_OCR、OCR_PROVIDER、OCR_ALLOW_MODEL_DOWNLOAD、严格模型目录检查）。 ✅

## 联调未验证项及原因

- **前端上传截图 -> 后端 OCR -> 表单预填 -> 保存 -> 提交流程**：属于前后端联调主链路，需要前端代码配合验证。当前仅通过后端独立测试验证了各原子接口行为。
- **PaddleOCR 真实识别效果**：测试环境中 PaddleOCR 依赖未安装，当前 `ocr.py` 已实现基于 settings 的降级逻辑，所有 OCR 测试均验证降级分支。
- **截图文件实际下载（FileResponse）**：测试环境使用假文件路径验证了权限和 404 行为，真实文件下载需联调时配合实际上传验证。
- **OCR_MODEL_DIR 真实模型目录与 PaddleOCR 实际识别效果**：当前未在容器中部署真实 PaddleOCR 模型文件，所有 OCR 测试均验证降级分支。若需真实 OCR 能力，需在 Docker 镜像中安装 `paddlepaddle` + `paddleocr`，并将模型文件放置到 `OCR_MODEL_DIR/det`、`rec`、`cls` 子目录下。

## 未完成项

- 无。后端原子接口、模型、迁移、测试均已完成并全部通过。
- PaddleOCR 依赖如需完整启用，建议后续在 Docker 镜像中安装 `paddlepaddle` + `paddleocr` 的 CPU 版本，并挂载 `OCR_MODEL_DIR` 对应目录。

# Round 002 后端交付报告 — invoice_files

## 1. 完成情况

| 需求 | 状态 |
|------|------|
| 数据模型（invoice_file 表） | 完成 |
| Alembic 迁移（含部分唯一索引） | 完成 |
| 模块自注册（registry） | 完成 |
| PDF 存储与校验 | 完成 |
| PDF 解析预览（PyMuPDF + PaddleOCR fallback） | 完成 |
| CRUD API | 完成 |
| 状态流转（draft → confirmed → voided → draft） | 完成 |
| 软删除 / 恢复 / 清理 | 完成 |
| PDF 鉴权下载 | 完成 |
| 权限控制（owner / admin） | 完成 |
| 发票类型与币种校验 | 完成 |
| 同一用户发票号唯一 | 完成 |
| 跨用户重复提示（admin 可见） | 完成 |
| 测试覆盖 | **54** 个测试全部通过 |

## 2. 模块文件清单

```
backend/app/modules/finance/invoice_files/
├── __init__.py          # 模块自注册
├── constants.py         # 状态 / 发票类型 / 币种常量
├── models.py            # SQLModel 表模型 + InvoiceFilePublic VO
├── schemas.py           # Re-export 模型
├── storage.py           # PDF 文件存储、校验、删除
├── pdf_parser.py        # PyMuPDF 文本提取 + PaddleOCR fallback
├── repository.py        # 数据访问层（CRUD + 重复计数 + purge 返回 pdf_paths）
├── service.py           # 业务逻辑层（含 VO 转换、重复提示、事务安全 PDF 替换）
└── router.py            # HTTP 接口层（multipart form + endpoints）
```

## 3. 数据库变更

- **迁移文件**: `backend/app/alembic/versions/16583fefb912_add_invoice_file_table.py`
- **表名**: `invoice_file`
- **关键字段**: `id`, `owner_id`, `invoice_number`, `invoice_date`, `invoice_amount` (NUMERIC(15,2)), `tax_amount`, `currency`, `buyer`, `seller`, `invoice_type`, `note`, `status`, `pdf_path`, `pdf_original_name`, `pdf_mime_type`, `pdf_size`, `deleted_at`, `deleted_by_id`, `created_at`, `updated_at`
- **索引**: 部分唯一索引 `ix_invoice_file_owner_invoice_number` on `(owner_id, invoice_number)` where `deleted_at IS NULL`

## 4. 测试报告

```
pytest tests/finance/invoice_files/index_test.py -v
======================== 54 passed, 3 warnings in 2.04s ========================
```

**测试覆盖范围**:
- PDF 解析预览（无持久化、未认证、非法 MIME）
- 创建（正常用户、默认税额为 0、非法类型/币种/金额/日期）
- 同一用户发票号唯一（拒绝重复）
- 跨用户发票号允许重复
- 列表查询（普通用户仅看自己、超管看全部、已删除列表仅看自己的）
- 详情查询（成功、404、403）
- 重复提示（admin 可见 `duplicate_invoice_owner_count`、普通用户不可见）
- 更新（成功、已确认状态禁止编辑、非法金额/日期）
- 状态流转（confirm、withdraw-confirmation、void、restore-draft、非法状态流转）
- 软删除与恢复（删除、恢复、非删除者无法查看已删除记录）
- 清理（admin only）
- PDF 下载（鉴权通过、403、未认证）
- OCR 配置行为（禁用本地 OCR、不支持 provider、模型目录缺失且禁止下载）
- PaddleOCR 模型目录存在性检查（缺子目录、空子目录、全部存在）

**BE-FIX-001 — PDF 替换事务安全**
- 更新草稿时替换 PDF：先保存新文件 → 写入 DB 元数据并提交 → 成功后删除旧文件；DB 失败则回滚删除新文件。

**BE-FIX-002 — 管理员权限拆分**
- 管理员可读取全部记录、可删除任意记录。
- 业务写操作（update、confirm、withdraw-confirmation、void、restore-draft）仅限记录所有者，管理员对其他人的记录返回 403。

**BE-FIX-003 — 清理时同步删除物理 PDF**
- `purge-deleted` 在删除 DB 记录后，遍历关联的 `pdf_path` 并删除磁盘文件；文件缺失时静默跳过。

## 5. 边界影响

- 全局测试套件中唯一失败项为 `tests/api/routes/test_private.py::test_create_user`（用户 email 唯一冲突，系已有测试数据残留，与本模块无关）。
- `tests/conftest.py` 已补充 `delete(InvoiceFile)` 清理逻辑，避免模块间测试数据干扰。

## 6. 运行方式

```bash
# 运行本模块测试
docker compose exec backend pytest tests/finance/invoice_files/index_test.py -v

# 验证迁移
docker compose exec backend alembic current
```

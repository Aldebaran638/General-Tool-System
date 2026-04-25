# Round 001 Tasks - purchase_records

## 一、任务上下文

- group: `finance`
- tool_key: `purchase_records`
- frontend_root: `frontend/src/tools/finance/purchase_records/`
- backend_root: `backend/app/modules/finance/purchase_records/`
- frontend_test_root: `frontend/tests/finance/purchase_records/`
- backend_test_root: `backend/tests/finance/purchase_records/`
- design_doc: `docs/rounds/round-001/design.md`
- test_plan: `docs/rounds/round-001/test-plan.md`
- requirements_doc: `docs/rounds/round-001/requirements.md`

## 二、前端任务

### FE-001

- title: 实现购买记录前端工具目录与导航入口
- description: 创建 `finance/purchase_records` 前端工具目录，注册“财务”工具组下的“购买记录”入口，新增薄路由 `/finance/purchase-records`。
- depends_on: 无
- allowed_files:
  - `frontend/src/tools/finance/purchase_records/**`
  - `frontend/src/routes/_layout/finance.purchase-records.tsx`
  - `frontend/src/config/tool-navigation.tsx`
  - `frontend/tests/finance/purchase_records/**`
- done_when:
  - 侧边栏显示“财务”工具组。
  - “购买记录”入口可进入页面。
  - route 文件保持薄封装。

### FE-002

- title: 实现购买记录列表、筛选与状态展示
- description: 实现正常记录/已删除记录筛选、空状态、加载状态、状态标签、匹配状态标签、截图入口。
- depends_on: FE-001, BE API 契约
- allowed_files:
  - `frontend/src/tools/finance/purchase_records/**`
  - `frontend/tests/finance/purchase_records/**`
- done_when:
  - 普通用户页面能展示自己的记录。
  - 管理员页面能展示所有正常记录。
  - 已删除筛选只展示当前删除者可见记录。

### FE-003

- title: 实现购买记录表单与 OCR 预填
- description: 实现截图上传、OCR preview 调用、表单预填、用户修改、保存草稿、提交。
- depends_on: FE-001, BE OCR/API 契约
- allowed_files:
  - `frontend/src/tools/finance/purchase_records/**`
  - `frontend/tests/finance/purchase_records/**`
- done_when:
  - 表单包含购买日期、金额、币种、订单名称、大类、小类、备注、截图。
  - OCR 成功后预填表单。
  - OCR 失败后仍允许手填。
  - 大类/小类规则在前端校验。

### FE-004

- title: 实现操作按钮与权限表现
- description: 实现编辑、提交、撤回提交、批准、驳回、撤回批准、逻辑删除、恢复操作的前端交互和权限显隐。
- depends_on: FE-002, FE-003, BE API 契约
- allowed_files:
  - `frontend/src/tools/finance/purchase_records/**`
  - `frontend/tests/finance/purchase_records/**`
- done_when:
  - 普通用户只看到自己可执行的操作。
  - 管理员看到批准、驳回、撤回批准操作。
  - 操作成功后列表刷新或本地状态同步。

### FE-005

- title: 实现前端 Playwright 测试与前端报告
- description: 按测试计划补充前端测试，执行构建与 Playwright 测试，输出 frontend report。
- depends_on: FE-001, FE-002, FE-003, FE-004
- allowed_files:
  - `frontend/tests/finance/purchase_records/**`
  - `docs/rounds/round-001/frontend-report.md`
- done_when:
  - `docker compose exec frontend bun run build` 通过。
  - `docker compose exec frontend bun run test -- tests/finance/purchase_records/index.spec.ts --reporter=line` 通过或报告明确阻塞原因。
  - frontend report 包含修改文件、测试结果、越界自检、联调已验证/未验证项。

## 三、后端任务

### BE-001

- title: 实现购买记录后端模块与数据模型
- description: 创建 `backend/app/modules/finance/purchase_records/`，实现模型、schema、repository、service、router、自注册。
- depends_on: 无
- allowed_files:
  - `backend/app/modules/finance/purchase_records/**`
  - `backend/app/alembic/versions/**`
  - `backend/tests/finance/purchase_records/**`
- done_when:
  - 模块能被 auto_discover_modules 发现。
  - `purchase_record` 表模型覆盖设计字段。
  - Alembic migration 存在并可升级。

### BE-002

- title: 实现文件存储与截图鉴权访问
- description: 使用本地文件系统保存截图，数据库只保存元数据，提供截图下载/预览接口。
- depends_on: BE-001
- allowed_files:
  - `backend/app/modules/finance/purchase_records/**`
  - `backend/tests/finance/purchase_records/**`
- done_when:
  - 文件保存到 `runtime_data/uploads/finance/purchase_records/`。
  - 文件名由后端生成 UUID。
  - 截图接口做权限校验。

### BE-003

- title: 实现 OCR preview 适配层
- description: 接入 PaddleOCR 本地预训练模型，OCR 结果只返回预填字段，不落库；如依赖安装受限，必须提供清晰降级错误且不影响正式创建。
- depends_on: BE-001
- allowed_files:
  - `backend/app/modules/finance/purchase_records/**`
  - `backend/pyproject.toml`
  - `uv.lock`
  - `.env`
  - `.env-example`
  - `backend/app/core/config.py`
  - `backend/tests/finance/purchase_records/**`
- done_when:
  - OCR preview 接口存在。
  - OCR 不保存文件、不写数据库。
  - OCR 行为受全局配置控制。
  - PaddleOCR 依赖版本固定，或报告明确安装阻塞与降级实现。

### BE-004

- title: 实现购买记录 CRUD、状态流转、逻辑删除与恢复
- description: 实现列表、详情、创建、更新、提交、撤回、批准、驳回、撤回批准、逻辑删除、恢复、清理 30 天前删除记录。
- depends_on: BE-001, BE-002
- allowed_files:
  - `backend/app/modules/finance/purchase_records/**`
  - `backend/tests/finance/purchase_records/**`
- done_when:
  - API 契约与设计文档一致。
  - 权限规则与状态流转被 service 层强制执行。
  - 逻辑删除可恢复。
  - 清理函数删除记录和截图文件。

### BE-005

- title: 实现后端测试、迁移校验与后端报告
- description: 按测试计划补充后端测试，执行后端目标测试与迁移校验，输出 backend report。
- depends_on: BE-001, BE-002, BE-003, BE-004
- allowed_files:
  - `backend/tests/finance/purchase_records/**`
  - `docs/rounds/round-001/backend-report.md`
- done_when:
  - `docker compose exec backend pytest tests/finance/purchase_records/index_test.py` 通过或报告明确阻塞原因。
  - `docker compose exec backend alembic upgrade head` 通过或报告明确阻塞原因。
  - backend report 包含 API 契约测试、迁移校验、越界自检、联调已验证/未验证项。

## 四、联调任务

### INT-001

- title: 前后端购买记录主链路联调
- description: 前端 AI 与后端 AI 在各自报告中说明以下主链路是否已验证：登录 -> 财务 -> 购买记录 -> 上传截图 -> OCR 预填 -> 修改字段 -> 保存草稿 -> 提交 -> 撤回 -> 删除 -> 已删除筛选 -> 恢复。
- depends_on: FE-005, BE-005
- allowed_files:
  - `docs/rounds/round-001/frontend-report.md`
  - `docs/rounds/round-001/backend-report.md`
- done_when:
  - frontend report 和 backend report 都写明联调已验证项和未验证项。
  - 未验证项必须写明原因。

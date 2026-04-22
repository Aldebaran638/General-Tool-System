# project-management 测试文档

## 一、工具上下文

- group: workbench
- tool_key: project-management
- frontend_test_root: frontend/tests/workbench/project-management/
- backend_test_root: backend/tests/workbench/project-management/
- current_legacy_backend_test_root: backend/tests/items/
- current_legacy_frontend_test_root: 当前未发现 items 工具的独立 Playwright 主测试目录。

## 二、前端测试点

- 路由 /items 可访问，并在工作台导航中可进入。
- 列表加载成功时展示 DataTable。
- 空状态下展示 You don't have any items yet 文案。
- 点击 Add Item 可以打开对话框并成功创建记录。
- 点击 Edit Item 可以打开对话框并成功更新记录。
- 点击 Delete Item 可以打开确认对话框并成功删除记录。
- title 为空时，新增和编辑表单都会阻止提交并显示校验错误。
- API 返回失败时，通过统一错误处理展示错误提示。

## 三、后端测试点

- GET /api/v1/items/ 超管可查看全部记录。
- GET /api/v1/items/ 普通用户只能查看自己的记录。
- GET /api/v1/items/{id} 查询成功。
- GET /api/v1/items/{id} 查询不存在记录返回 404。
- GET /api/v1/items/{id} 查询他人记录返回 403。
- POST /api/v1/items/ 创建成功。
- POST /api/v1/items/ title 缺失或为空时返回 422。
- PUT /api/v1/items/{id} 更新成功。
- PUT /api/v1/items/{id} 更新他人记录返回 403。
- DELETE /api/v1/items/{id} 删除成功。
- DELETE /api/v1/items/{id} 删除不存在记录返回 404。

## 四、接口检查点

### 1. read-items

- success_case: 超管读取两条以上数据时返回 data 和 count，分页参数生效。
- failure_case: 认证无效时返回认证错误。
- permission_case: 普通用户只看到 owner_id 属于自己的记录。

### 2. read-item

- success_case: 已存在 item 按 id 读取成功。
- failure_case: 不存在 id 返回 404 Item not found。
- permission_case: 普通用户读取他人 item 返回 403 Not enough permissions。

### 3. create-item

- success_case: title 合法时成功创建，owner_id 自动等于当前用户。
- failure_case: title 缺失或空字符串返回 422。
- permission_case: 已登录普通用户也允许创建自己的 item。

### 4. update-item

- success_case: title、description 更新后返回最新 ItemPublic。
- failure_case: 不存在 id 返回 404。
- permission_case: 普通用户更新他人 item 返回 403。

### 5. delete-item

- success_case: 删除成功返回 message。
- failure_case: 不存在 id 返回 404。
- permission_case: 普通用户删除他人 item 返回 403。

## 五、联调检查点

- 登录 -> 工作台导航 -> 项目管理页面 -> Add Item -> Edit Item -> Delete Item。
- 前端列表 query key items 与后端 /api/v1/items/ 保持一致。
- 前端对 title 的本地校验与后端 422 约束保持一致。

## 六、越界与回归检查

- allowed_files 检查：仅允许改动项目管理工具相关 route、组件、target tool root、相关测试、必要的 backend items 路由与模块文件。
- 契约一致性检查：不得更改 /items 路由，不得更改 /api/v1/items/ 路径，不得额外暴露 amount/test_amount。
- 共享能力回归检查：DataTable 样式和行为不得被项目管理工具定制破坏。
- 范围回归检查：admin、settings、purchase_records、system_management 不得被顺手改动。

## 七、验收门槛

- backend/tests/items/index_test.py 作为当前基线必须可执行通过。
- 新的 backend/tests/workbench/project-management/index_test.py 在迁移完成后必须覆盖相同主要分支。
- frontend/tests/workbench/project-management/index.spec.ts 必须覆盖至少一条成功主链路和一条失败或空状态分支。
- 主链路必须至少真实跑通一次：创建 -> 编辑 -> 删除。
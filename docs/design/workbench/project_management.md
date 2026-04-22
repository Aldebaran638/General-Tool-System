# project_management 设计文档

## 一、工具身份

- request_type: existing-tool-change
- group: workbench
- tool_key: project_management
- tool_name: 项目管理
- route_path: /items
- navigation_label: 项目管理
- frontend_root: frontend/src/tools/workbench/project_management/
- backend_root: backend/app/modules/workbench/project_management/
- frontend_test_root: frontend/tests/workbench/project_management/
- backend_test_root: backend/tests/workbench/project_management/

## 二、需求摘要

- summary: 将现有 /items 工具纳入 group/tool 流水线，保留当前用户可见路由和后端 API，不扩大业务范围。
- primary_actor: authenticated-user
- core_actions:
  - list
  - read
  - create
  - update
  - delete

## 三、当前实现基线

- current_frontend_entry: frontend/src/routes/_layout/items.tsx
- current_frontend_location: frontend/src/routes/_layout/items.tsx 和 frontend/src/components/Items/**
- current_frontend_structure: 当前页面逻辑散落在 components 目录，本轮目标是将主要业务代码收敛到 frontend/src/tools/workbench/project_management/，同时保持 /items 路由不变。
- current_frontend_components:
  - frontend/src/components/Items/AddItem.tsx
  - frontend/src/components/Items/EditItem.tsx
  - frontend/src/components/Items/DeleteItem.tsx
  - frontend/src/components/Items/columns.tsx
  - frontend/src/components/Items/ItemActionsMenu.tsx
- current_backend_entry: backend/app/api/routes/items.py
- current_backend_domain:
  - backend/app/models.py
  - backend/app/crud.py
- current_backend_tests:
  - backend/tests/items/index_test.py
  - backend/tests/items/helpers.py
- current_frontend_tests: 当前未发现针对 /items 工具的独立 Playwright 主测试文件。

## 四、前端依赖与实现框架

- api_client: @/client 中自动生成的 ItemsService
- state_query: @tanstack/react-query
- form_stack: react-hook-form + zod
- ui_stack: shadcn/ui
- table_stack: @tanstack/react-table + frontend/src/components/Common/DataTable.tsx
- toast_stack: useCustomToast + handleError
- reference_files:
  - frontend/src/routes/_layout/items.tsx
  - frontend/src/components/Items/AddItem.tsx
  - frontend/src/components/Items/EditItem.tsx
  - frontend/src/components/Items/DeleteItem.tsx
  - frontend/tests/items/index.spec.ts

## 五、数据与持久化决策

- schema_strategy: reuse
- migration_required: false
- tables:
  - item: 复用现有 Item 表，不新增表、不扩字段。
- relations:
  - item.owner_id -> user.id
- notes:
  - 保留 owner_id 归属隔离。
  - 保留 created_at 排序逻辑。
  - amount 与 test_amount 本轮继续保持未公开状态。

## 六、API 契约

### 1. read-items

- method: GET
- path: /api/v1/items/
- purpose: 列表查询 item；超管可看全部，普通用户只看自己的 item。
- auth_requirement: 已登录用户；超管拥有全量读取权限，普通用户仅可读取 owner_id == current_user.id 的记录。
- request_shape:
  - query.skip: int, default 0
  - query.limit: int, default 100
- response_shape:
  - data: ItemPublic[]
  - count: int
- error_shape:
  - 401/403: 标准认证错误
- business_rules:
  - 超管按 created_at desc 读取全量数据。
  - 普通用户按 created_at desc 读取自己的数据。

### 2. read-item

- method: GET
- path: /api/v1/items/{id}
- purpose: 读取单条 item 详情。
- auth_requirement: 已登录用户；超管可读任意 item，普通用户只能读取自己的 item。
- request_shape:
  - path.id: uuid
- response_shape:
  - id: uuid
  - title: string
  - description: string | null
  - owner_id: uuid
  - created_at: datetime | null
- error_shape:
  - 404: Item not found
  - 403: Not enough permissions
- business_rules:
  - item 不存在时返回 404。
  - item 属于他人且当前用户非超管时返回 403。

### 3. create-item

- method: POST
- path: /api/v1/items/
- purpose: 创建新 item。
- auth_requirement: 已登录用户。
- request_shape:
  - body.title: string, min_length 1, max_length 255
  - body.description: string | null, max_length 255
- response_shape:
  - ItemPublic
- error_shape:
  - 422: 请求参数不合法
- business_rules:
  - owner_id 必须始终取 current_user.id。
  - title 不能为空。

### 4. update-item

- method: PUT
- path: /api/v1/items/{id}
- purpose: 更新已有 item。
- auth_requirement: 已登录用户；超管可更新任意 item，普通用户只能更新自己的 item。
- request_shape:
  - path.id: uuid
  - body.title: string | null
  - body.description: string | null
- response_shape:
  - ItemPublic
- error_shape:
  - 404: Item not found
  - 403: Not enough permissions
  - 422: 请求参数不合法
- business_rules:
  - 只更新已提供字段。
  - title 如提供则仍需满足最小长度约束。

### 5. delete-item

- method: DELETE
- path: /api/v1/items/{id}
- purpose: 删除已有 item。
- auth_requirement: 已登录用户；超管可删除任意 item，普通用户只能删除自己的 item。
- request_shape:
  - path.id: uuid
- response_shape:
  - message: Item deleted successfully
- error_shape:
  - 404: Item not found
  - 403: Not enough permissions
- business_rules:
  - 删除后不返回 ItemPublic。

## 七、前端页面状态

- loading: 列表查询未返回时展示 PendingItems。
- empty: data.length === 0 时展示空状态文案和引导。
- success: DataTable 正常渲染列表，支持新增、编辑、删除动作。
- validation_error: 新增和编辑对话框内 title 为空时展示表单校验错误。
- permission_denied: 普通用户对他人 item 执行详情、更新、删除时，应接收后端 403 并通过 handleError + useCustomToast 展示错误提示，沿用 frontend/src/components/Items/AddItem.tsx 与 EditItem.tsx 中现有 mutation onError 模式。
- backend_failure: 请求失败时通过 handleError + toast 展示错误。

## 八、文件边界

- allowed_files:
  - frontend/src/config/tool-navigation.tsx
  - frontend/src/routes/_layout/items.tsx
  - frontend/src/components/Items/**
  - frontend/src/components/Pending/PendingItems.tsx
  - frontend/src/components/Common/DataTable.tsx
  - frontend/src/tools/workbench/project_management/**
  - frontend/tests/workbench/project_management/**
  - backend/app/api/routes/items.py
  - backend/app/models.py
  - backend/app/crud.py
  - backend/app/modules/workbench/project_management/**
  - backend/tests/items/**
  - backend/tests/workbench/project_management/**
- forbidden_files:
  - frontend/src/routes/_layout/admin.tsx
  - frontend/src/routes/_layout/settings.tsx
  - frontend/src/routeTree.gen.ts
  - backend/app/api/routes/users.py
  - backend/app/modules/purchase_records/**
  - backend/app/modules/system_management/**

## 九、后端实现路线图

### 1. 模块结构约定

- target_module_root: backend/app/modules/workbench/project_management/
- required_files:
  - __init__.py
  - router.py
  - service.py
  - repository.py
  - schemas.py

### 2. 与现有代码的关系

- models.py 处理方式:
  - backend/app/models.py 中的 Item 存储模型继续保留，不在本轮迁移中改字段。
  - module/repository.py 直接通过 from app.models import Item 导入现有存储模型。
  - 本轮不要求也不允许为了 module 落地而给 Item 额外添加业务方法、展示字段或新的持久化字段。
  - module 内允许在 schemas.py 中重新定义或包装公开 schema，用来确保 amount 和 test_amount 不被暴露。
- 公开字段过滤方式:
  - 当前仓库已经通过 response_model=ItemPublic 或 response_model=ItemsPublic 自动裁剪公开字段。
  - module/service.py 与 module/repository.py 可以继续返回 Item 或 list[Item] 这一存储实体结果。
  - module/router.py 负责声明 response_model 并组装 ItemsPublic(data=items, count=count) 这种 API 输出外壳。
- crud.py 处理方式:
  - backend/app/crud.py 当前不是 items 逻辑主入口，本轮不要求把 items 逻辑写入 crud.py。
  - item 的查询与持久化逻辑应下沉到 backend/app/modules/workbench/project_management/repository.py。
- routes/items.py 处理方式:
  - backend/app/api/routes/items.py 允许继续存在，但最终应只作为兼容导出层。
  - 默认形态是 backend/app/api/routes/items.py 仅保留 from app.modules.workbench.project_management.router import router 这一类兼容导出，不再保留具体的 @router.get、@router.post、@router.put、@router.delete 处理函数。
  - 权限判断、分页条件、owner_id 过滤、更新删除规则应下沉到 module/service.py 与 module/repository.py。
  - 当前公开 API 在 backend/app/api/main.py 中只注册了 items.router，因此本轮默认接入方式是保留 api/main.py 不变，并让 api/main.py 继续经由 routes/items.py 取得 module/router.py 中定义的 router。
- testing 处理方式:
  - backend/tests/items/index_test.py 保留为 legacy baseline。
  - backend/tests/workbench/project_management/index_test.py 作为新结构下的主测试文件。

### 3. 模块集成要求

- 如果 backend/app/api/routes/items.py 继续作为入口，则不新增公开 API 路径。
- 默认优先采用 routes/items.py 作为稳定入口，避免为了本轮迁移额外改动 backend/app/api/main.py。
- 默认采用唯一接入方案：backend/app/modules/workbench/project_management/router.py 直接声明 router = APIRouter(prefix="/items", tags=["items"])，并在其中定义全部 handlers 与 response_model。
- backend/app/api/routes/items.py 只保留兼容导出代码，例如 from app.modules.workbench.project_management.router import router。
- backend/app/api/main.py 保持不改，因为它已经注册了 items.router，而 items.router 会继续指向 module/router.py 中的公开 router。

## 十、验收清单

- frontend_acceptance:
  - /items 路由保持可访问。
  - 工作台导航中的“项目管理”入口保持不变。
  - 页面继续支持列表、新增、编辑、删除。
  - 新增 Playwright 主测试文件落在 frontend/tests/workbench/project_management/index.spec.ts。
- backend_acceptance:
  - /api/v1/items/ 与 /api/v1/items/{id} 契约保持不变。
  - 权限规则保持“超管全量，普通用户仅自己的数据”。
  - 后端主测试文件最终落在 backend/tests/workbench/project_management/index_test.py，覆盖当前 index_test.py 的主要分支。
- integration_acceptance:
  - 前端请求路径与后端实际路径完全一致。
  - 现有用户在 /items 上至少能跑通一次创建 -> 编辑 -> 删除主链路。
  - 本轮不得顺带改动 admin、settings、purchase_records、system_management。
# project_management 任务清单

## 一、任务上下文

- group: workbench
- tool_key: project_management
- frontend_root: frontend/src/tools/workbench/project_management/
- backend_root: backend/app/modules/workbench/project_management/
- frontend_test_root: frontend/tests/workbench/project_management/
- backend_test_root: backend/tests/workbench/project_management/

## 二、前端任务

### FE-001

- title: 建立项目管理工具前端根目录
- description: 在 frontend/src/tools/workbench/project_management/ 下建立 api、types、schemas、components、hooks 结构，用于承接当前 /items 工具逻辑。
- depends_on: []
- allowed_files:
  - frontend/src/tools/workbench/project_management/**
  - frontend/src/routes/_layout/items.tsx
- done_when:
  - target tool root 建立完成。
  - route 文件仍然保持薄，只做页面装配和入口导出。
  - 目录至少包含：
    - api.ts
    - types.ts
    - schemas.ts
    - components/
    - hooks/

### FE-002

- title: 将项目管理页面逻辑收敛到 tool root
- description: 把当前列表、新增、编辑、删除、列定义等页面逻辑从 legacy 组件目录收敛到 target tool root，同时保持 /items 页面行为不变。
- depends_on:
  - FE-001
- allowed_files:
  - frontend/src/routes/_layout/items.tsx
  - frontend/src/components/Items/**
  - frontend/src/components/Pending/PendingItems.tsx
  - frontend/src/components/Common/DataTable.tsx
  - frontend/src/tools/workbench/project_management/**
- done_when:
  - /items 页面仍能正常展示列表和操作入口。
  - Add Item、Edit Item、Delete Item 的 UI 与行为保持一致。
  - route 文件不再直接承载业务细节。
  - 现有 AddItem、EditItem、DeleteItem、columns、ItemActionsMenu 的主要逻辑已迁入 target tool root，legacy 目录仅保留必要兼容层或被删除。
  - 所有 API 调用继续使用 @/client 中的 ItemsService。

### FE-003

- title: 为项目管理工具补齐 Playwright 主测试
- description: 新建 frontend/tests/workbench/project_management/index.spec.ts，覆盖路由进入、列表展示、创建、编辑、删除、至少一个失败或空状态分支。
- depends_on:
  - FE-002
- allowed_files:
  - frontend/tests/workbench/project_management/**
  - frontend/tests/utils/**
- done_when:
  - 主测试文件位于 frontend/tests/workbench/project_management/index.spec.ts。
  - 至少一条成功主链路和一条失败或空状态分支被覆盖。
  - 现有 frontend/tests/items/index.spec.ts 保留为参考或 legacy baseline，不要求在本轮删除。

## 三、后端任务

### BE-001

- title: 建立项目管理后端模块骨架
- description: 在 backend/app/modules/workbench/project_management/ 下建立 router、service、repository、schemas、models 骨架，用于承接当前 items 工具的业务边界。
- depends_on: []
- allowed_files:
  - backend/app/modules/workbench/project_management/**
- done_when:
  - backend 模块骨架建立完成。
  - router、service、repository 职责边界清晰。
  - 至少建立以下文件：
    - __init__.py
    - router.py
    - service.py
    - repository.py
    - schemas.py

### BE-002

- title: 将 items 业务逻辑向模块边界收敛
- description: 以不改变 /api/v1/items 契约为前提，将当前 backend/app/api/routes/items.py、backend/app/crud.py、backend/app/models.py 中的 items 相关逻辑向模块根目录收敛，保留必要的最小接入层。
- depends_on:
  - BE-001
- allowed_files:
  - backend/app/api/routes/items.py
  - backend/app/crud.py
  - backend/app/models.py
  - backend/app/modules/workbench/project_management/**
- done_when:
  - /api/v1/items/ 和 /api/v1/items/{id} 的方法、参数、响应保持不变。
  - 权限规则仍然是“超管全量、普通用户仅自己的记录”。
  - 新业务代码不继续扩散进 backend/app/api/routes/。
  - backend/app/api/routes/items.py 最终只保留 from app.modules.workbench.project_management.router import router 这一类兼容导出职责。
  - backend/app/api/main.py 不需要为本轮新增或改写 router 注册；稳定入口继续是已注册的 backend/app/api/routes/items.py。
  - module/repository.py 明确复用 from app.models import Item，不为迁移新增 Item 字段或业务方法。
  - item 查询、owner 过滤、更新和删除规则位于 module/service.py 与 module/repository.py。
  - amount 和 test_amount 仍仅存在于存储实体；公开裁剪继续由 module/router.py 中的 response_model=ItemPublic/ItemsPublic 保证。

### BE-003

- title: 迁移项目管理后端主测试到标准路径
- description: 将当前 backend/tests/items/index_test.py 的主覆盖迁移或镜像到 backend/tests/workbench/project_management/index_test.py，并保留必要 helpers。
- depends_on:
  - BE-002
- allowed_files:
  - backend/tests/items/**
  - backend/tests/workbench/project_management/**
- done_when:
  - backend/tests/workbench/project_management/index_test.py 成为新的主测试文件。
  - 现有列表、详情、创建、更新、删除、403、404、422 分支保持覆盖。
  - backend/tests/items/index_test.py 保留为 legacy baseline，用于验证 API 兼容性。

## 四、联调任务

### INT-001

- title: 校验前后端路径与契约稳定性
- description: 确认 /items 仍然调用 /api/v1/items/ 相关接口，且前端字段、分页、错误处理与后端契约保持一致。
- depends_on:
  - FE-002
  - BE-002
- allowed_files:
  - frontend/src/routes/_layout/items.tsx
  - frontend/src/tools/workbench/project_management/**
  - backend/app/api/routes/items.py
  - backend/app/modules/workbench/project_management/**
- done_when:
  - 前端未引入不存在的 API 或字段。
  - 后端未修改既有公开路径。
  - 创建、编辑、删除主链路能用真实接口跑通。

## 五、测试任务

### QA-001

- title: 执行项目管理工具验收
- description: 先运行 backend/tests/items/index_test.py 作为基线，再运行新的 backend/tests/workbench/project_management/index_test.py 和 frontend/tests/workbench/project_management/index.spec.ts，检查越界与契约一致性。
- depends_on:
  - FE-003
  - BE-003
  - INT-001
- allowed_files:
  - backend/tests/items/**
  - backend/tests/workbench/project_management/**
  - frontend/tests/workbench/project_management/**
- done_when:
  - 基线 backend tests 通过。
  - 新 backend tests 通过。
  - 新 frontend tests 通过。
  - 无越界修改。
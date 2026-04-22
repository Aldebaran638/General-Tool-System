# project-management 任务清单

## 一、任务上下文

- group: workbench
- tool_key: project-management
- frontend_root: frontend/src/tools/workbench/project-management/
- backend_root: backend/app/modules/workbench/project-management/
- frontend_test_root: frontend/tests/workbench/project-management/
- backend_test_root: backend/tests/workbench/project-management/

## 二、前端任务

### FE-001

- title: 建立项目管理工具前端根目录
- description: 在 frontend/src/tools/workbench/project-management/ 下建立 api、types、schemas、components、hooks 结构，用于承接当前 /items 工具逻辑。
- depends_on: []
- allowed_files:
  - frontend/src/tools/workbench/project-management/**
  - frontend/src/routes/_layout/items.tsx
- done_when:
  - target tool root 建立完成。
  - route 文件仍然保持薄，只做页面装配和入口导出。

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
  - frontend/src/tools/workbench/project-management/**
- done_when:
  - /items 页面仍能正常展示列表和操作入口。
  - Add Item、Edit Item、Delete Item 的 UI 与行为保持一致。
  - route 文件不再直接承载业务细节。

### FE-003

- title: 为项目管理工具补齐 Playwright 主测试
- description: 新建 frontend/tests/workbench/project-management/index.spec.ts，覆盖路由进入、列表展示、创建、编辑、删除、至少一个失败或空状态分支。
- depends_on:
  - FE-002
- allowed_files:
  - frontend/tests/workbench/project-management/**
  - frontend/tests/utils/**
- done_when:
  - 主测试文件位于 frontend/tests/workbench/project-management/index.spec.ts。
  - 至少一条成功主链路和一条失败或空状态分支被覆盖。

## 三、后端任务

### BE-001

- title: 建立项目管理后端模块骨架
- description: 在 backend/app/modules/workbench/project-management/ 下建立 router、service、repository、schemas、models 骨架，用于承接当前 items 工具的业务边界。
- depends_on: []
- allowed_files:
  - backend/app/modules/workbench/project-management/**
- done_when:
  - backend 模块骨架建立完成。
  - router、service、repository 职责边界清晰。

### BE-002

- title: 将 items 业务逻辑向模块边界收敛
- description: 以不改变 /api/v1/items 契约为前提，将当前 backend/app/api/routes/items.py、backend/app/crud.py、backend/app/models.py 中的 items 相关逻辑向模块根目录收敛，保留必要的最小接入层。
- depends_on:
  - BE-001
- allowed_files:
  - backend/app/api/routes/items.py
  - backend/app/crud.py
  - backend/app/models.py
  - backend/app/modules/workbench/project-management/**
- done_when:
  - /api/v1/items/ 和 /api/v1/items/{id} 的方法、参数、响应保持不变。
  - 权限规则仍然是“超管全量、普通用户仅自己的记录”。
  - 新业务代码不继续扩散进 backend/app/api/routes/。

### BE-003

- title: 迁移项目管理后端主测试到标准路径
- description: 将当前 backend/tests/items/index_test.py 的主覆盖迁移或镜像到 backend/tests/workbench/project-management/index_test.py，并保留必要 helpers。
- depends_on:
  - BE-002
- allowed_files:
  - backend/tests/items/**
  - backend/tests/workbench/project-management/**
- done_when:
  - backend/tests/workbench/project-management/index_test.py 成为新的主测试文件。
  - 现有列表、详情、创建、更新、删除、403、404、422 分支保持覆盖。

## 四、联调任务

### INT-001

- title: 校验前后端路径与契约稳定性
- description: 确认 /items 仍然调用 /api/v1/items/ 相关接口，且前端字段、分页、错误处理与后端契约保持一致。
- depends_on:
  - FE-002
  - BE-002
- allowed_files:
  - frontend/src/routes/_layout/items.tsx
  - frontend/src/tools/workbench/project-management/**
  - backend/app/api/routes/items.py
  - backend/app/modules/workbench/project-management/**
- done_when:
  - 前端未引入不存在的 API 或字段。
  - 后端未修改既有公开路径。
  - 创建、编辑、删除主链路能用真实接口跑通。

## 五、测试任务

### QA-001

- title: 执行项目管理工具验收
- description: 先运行 backend/tests/items/index_test.py 作为基线，再运行新的 backend/tests/workbench/project-management/index_test.py 和 frontend/tests/workbench/project-management/index.spec.ts，检查越界与契约一致性。
- depends_on:
  - FE-003
  - BE-003
  - INT-001
- allowed_files:
  - backend/tests/items/**
  - backend/tests/workbench/project-management/**
  - frontend/tests/workbench/project-management/**
- done_when:
  - 基线 backend tests 通过。
  - 新 backend tests 通过。
  - 新 frontend tests 通过。
  - 无越界修改。
# project-management 样例派单包

## 一、工具身份

- group: workbench
- tool_key: project-management
- tool_name: 项目管理
- route_path: /items
- frontend_root: frontend/src/tools/workbench/project-management/
- backend_root: backend/app/modules/workbench/project-management/
- frontend_test_root: frontend/tests/workbench/project-management/
- backend_test_root: backend/tests/workbench/project-management/

## 二、输入物路径

- tool intake: docs/packets/workbench/project-management/01-tool-intake.json
- db design: docs/packets/workbench/project-management/02-db-design.json
- design doc: docs/design/workbench/project-management.md
- test doc: docs/test/workbench/project-management.md
- task list: docs/tasks/workbench/project-management.md

## 三、前端 AI 派单文案

你现在只负责一个工具：workbench / project-management。

先读取以下输入物：

1. docs/design/workbench/project-management.md
2. docs/test/workbench/project-management.md
3. docs/tasks/workbench/project-management.md
4. skills/members/前端skill.md
5. skills/tool-frontend-builder/SKILL.md

你的目标：

1. 保持 /items 路由不变。
2. 将项目管理工具的主要前端代码收敛到 frontend/src/tools/workbench/project-management/。
3. 补齐 frontend/tests/workbench/project-management/index.spec.ts。
4. 不得修改 admin、settings 等无关工具。

允许修改范围：

- frontend/src/routes/_layout/items.tsx
- frontend/src/components/Items/**
- frontend/src/components/Pending/PendingItems.tsx
- frontend/src/components/Common/DataTable.tsx
- frontend/src/tools/workbench/project-management/**
- frontend/tests/workbench/project-management/**

禁止修改范围：

- frontend/src/routes/_layout/admin.tsx
- frontend/src/routes/_layout/settings.tsx
- frontend/src/routeTree.gen.ts

完成后必须输出 frontend report。

## 四、后端 AI 派单文案

你现在只负责一个工具：workbench / project-management。

先读取以下输入物：

1. docs/design/workbench/project-management.md
2. docs/test/workbench/project-management.md
3. docs/tasks/workbench/project-management.md
4. skills/members/后端skill.md
5. skills/tool-module-builder/SKILL.md

你的目标：

1. 保持 /api/v1/items/ 与 /api/v1/items/{id} 契约不变。
2. 在 backend/app/modules/workbench/project-management/ 下建立模块骨架并收敛 items 逻辑。
3. 将主后端测试迁移或镜像到 backend/tests/workbench/project-management/index_test.py。
4. 不得修改 purchase_records、system_management 等无关模块。

允许修改范围：

- backend/app/api/routes/items.py
- backend/app/crud.py
- backend/app/models.py
- backend/app/modules/workbench/project-management/**
- backend/tests/items/**
- backend/tests/workbench/project-management/**

禁止修改范围：

- backend/app/api/routes/users.py
- backend/app/modules/purchase_records/**
- backend/app/modules/system_management/**

完成后必须输出 backend report。

## 五、测试 AI 派单文案

你现在只负责一个工具：workbench / project-management。

先读取以下输入物：

1. docs/design/workbench/project-management.md
2. docs/test/workbench/project-management.md
3. docs/tasks/workbench/project-management.md
4. 前端 report
5. backend report
6. skills/members/测试skill.md

你的目标：

1. 检查是否越界修改。
2. 先运行 backend/tests/items/index_test.py 作为基线。
3. 再运行 backend/tests/workbench/project-management/index_test.py。
4. 再运行 frontend/tests/workbench/project-management/index.spec.ts。
5. 至少跑通一次创建 -> 编辑 -> 删除主链路。

验收失败条件：

1. 路由或 API 路径被改动。
2. 新测试路径未落在 group/tool-key 结构下。
3. amount 或 test_amount 被无授权暴露。
4. admin、settings、purchase_records、system_management 被顺手改动。
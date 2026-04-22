# project_management 样例派单包

## 一、工具身份

- group: workbench
- tool_key: project_management
- tool_name: 项目管理
- route_path: /items
- frontend_root: frontend/src/tools/workbench/project_management/
- backend_root: backend/app/modules/workbench/project_management/
- frontend_test_root: frontend/tests/workbench/project_management/
- backend_test_root: backend/tests/workbench/project_management/

## 二、输入物路径

- tool intake: docs/packets/workbench/project_management/01-tool-intake.json
- db design: docs/packets/workbench/project_management/02-db-design.json
- design doc: docs/design/workbench/project_management.md
- test doc: docs/test/workbench/project_management.md
- task list: docs/tasks/workbench/project_management.md
- frontend report template: docs/packets/workbench/project_management/frontend-report.template.md
- backend report template: docs/packets/workbench/project_management/backend-report.template.md
- expected frontend report output: docs/packets/workbench/project_management/frontend-report.md
- expected backend report output: docs/packets/workbench/project_management/backend-report.md

## 三、前端 AI 派单文案

你现在只负责一个工具：workbench / project_management。

先读取以下输入物：

1. docs/design/workbench/project_management.md
2. docs/test/workbench/project_management.md
3. docs/tasks/workbench/project_management.md
4. skills/members/前端skill.md
5. skills/tool-frontend-builder/SKILL.md

你的目标：

1. 保持 /items 路由不变。
2. 将项目管理工具的主要前端代码收敛到 frontend/src/tools/workbench/project_management/。
3. 补齐 frontend/tests/workbench/project_management/index.spec.ts。
4. 不得修改 admin、settings 等无关工具。

输入补充：

1. 现有实现位置：
	- frontend/src/routes/_layout/items.tsx
	- frontend/src/components/Items/**
	- frontend/tests/items/index.spec.ts
2. 本轮要求：
	- 保持 /items 路由和工作台导航入口不变。
	- 将主要业务代码收敛到 frontend/src/tools/workbench/project_management/。
	- route 文件改为从 target tool root 装配页面。
3. API 调用方式：
	- 继续使用 @/client 中自动生成的 ItemsService。
	- 禁止绕过 ItemsService 改用自写 fetch 或 axios。
4. 导航状态：
	- frontend/src/config/tool-navigation.tsx 中“工作台 -> 项目管理 -> /items”当前已存在，本轮无需新增重复入口。

允许修改范围：

- frontend/src/routes/_layout/items.tsx
- frontend/src/components/Items/**
- frontend/src/components/Pending/PendingItems.tsx
- frontend/src/components/Common/DataTable.tsx
- frontend/src/tools/workbench/project_management/**
- frontend/tests/workbench/project_management/**

禁止修改范围：

- frontend/src/routes/_layout/admin.tsx
- frontend/src/routes/_layout/settings.tsx
- frontend/src/routeTree.gen.ts

完成后必须输出 frontend report。

## 四、后端 AI 派单文案

你现在只负责一个工具：workbench / project_management。

先读取以下输入物：

1. docs/design/workbench/project_management.md
2. docs/test/workbench/project_management.md
3. docs/tasks/workbench/project_management.md
4. skills/members/后端skill.md
5. skills/tool-module-builder/SKILL.md

你的目标：

1. 保持 /api/v1/items/ 与 /api/v1/items/{id} 契约不变。
2. 在 backend/app/modules/workbench/project_management/ 下建立模块骨架并收敛 items 逻辑。
3. 将主后端测试迁移或镜像到 backend/tests/workbench/project_management/index_test.py。
4. 不得修改 purchase_records、system_management 等无关模块。

关键澄清：

1. models.py 处理方式：
	- backend/app/models.py 中的 Item 存储模型保留。
	- module/repository.py 直接使用 from app.models import Item。
	- 本轮不要为了 module 落地去扩 Item 字段、方法或公开字段。
	- 如需限制公开字段，应在 module/schemas.py 中定义公开 schema，而不是暴露 amount 或 test_amount。
2. 公开字段过滤方式：
	- 当前仓库已经依赖 response_model=ItemPublic / ItemsPublic 自动裁剪 amount 与 test_amount。
	- service.py 与 repository.py 可以返回 Item 或 list[Item]；module/router.py 继续负责声明 response_model 和组装 ItemsPublic(data=items, count=count)。
	- 不需要额外发明一层手写字段映射才能满足当前契约。
3. crud.py 处理方式：
	- backend/app/crud.py 当前不是 items 逻辑主入口，本轮不要求把 items 逻辑迁入 crud.py。
4. routes/items.py 最终形态：
	- backend/app/modules/workbench/project_management/router.py 直接声明 router = APIRouter(prefix="/items", tags=["items"])，并承载全部 handlers 与 response_model。
	- backend/app/api/routes/items.py 允许保留，但最终只作为兼容导出层，默认形态就是 from app.modules.workbench.project_management.router import router。
	- owner 过滤、权限判断、分页、更新删除规则应下沉到 module/service.py 与 module/repository.py。
	- 当前 backend/app/api/main.py 只注册了 items.router，所以本轮默认不要改 api/main.py；保持 routes/items.py 为稳定接入点即可。
5. 测试迁移策略：
	- backend/tests/items/index_test.py 保留为 legacy baseline。
	- backend/tests/workbench/project_management/index_test.py 为新结构主测试文件。

允许修改范围：

- backend/app/api/routes/items.py
- backend/app/crud.py
- backend/app/models.py
- backend/app/modules/workbench/project_management/**
- backend/tests/items/**
- backend/tests/workbench/project_management/**

禁止修改范围：

- backend/app/api/routes/users.py
- backend/app/modules/purchase_records/**
- backend/app/modules/system_management/**

完成后必须输出 backend report。

## 五、测试AI前置条件检查

1. frontend report 是否存在于 docs/packets/workbench/project_management/frontend-report.md。
2. backend report 是否存在于 docs/packets/workbench/project_management/backend-report.md。
3. backend/tests/items/index_test.py 是否存在。
4. backend/tests/workbench/project_management/index_test.py 是否存在。
5. frontend/tests/workbench/project_management/index.spec.ts 是否存在。
6. 缺失上述任一输入物时，测试AI必须输出“输入物不完整，无法验收”。

## 六、测试 AI 派单文案

你现在只负责一个工具：workbench / project_management。

先读取以下输入物：

1. docs/design/workbench/project_management.md
2. docs/test/workbench/project_management.md
3. docs/tasks/workbench/project_management.md
4. docs/packets/workbench/project_management/frontend-report.md
5. docs/packets/workbench/project_management/backend-report.md
6. skills/members/测试skill.md

你的目标：

1. 检查是否越界修改。
2. 先运行 backend/tests/items/index_test.py 作为基线。
3. 再运行 backend/tests/workbench/project_management/index_test.py。
4. 再运行 frontend/tests/workbench/project_management/index.spec.ts。
5. 至少跑通一次创建 -> 编辑 -> 删除主链路。

验收失败条件：

1. 路由或 API 路径被改动。
2. 新测试路径未落在 group/tool-key 结构下。
3. amount 或 test_amount 被无授权暴露。
4. admin、settings、purchase_records、system_management 被顺手改动。
6. 前端 report 或 backend report 缺失。
7. 任何一个必需测试文件缺失。
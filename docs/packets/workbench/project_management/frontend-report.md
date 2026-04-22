# Frontend Report

## 输入物路径

- design_doc: docs/design/workbench/project_management.md
- test_doc: docs/test/workbench/project_management.md
- task_list: docs/tasks/workbench/project_management.md

## 修改文件

- frontend/src/routes/_layout/items.tsx
- frontend/src/components/Items/AddItem.tsx
- frontend/src/components/Items/EditItem.tsx
- frontend/src/components/Items/DeleteItem.tsx
- frontend/src/components/Items/columns.tsx

## 新增文件

- frontend/src/tools/workbench/project_management/types.ts
- frontend/src/tools/workbench/project_management/schemas.ts
- frontend/src/tools/workbench/project_management/api.ts
- frontend/src/tools/workbench/project_management/hooks/useItemsQuery.ts
- frontend/src/tools/workbench/project_management/components/ProjectManagementPage.tsx
- frontend/tests/workbench/project_management/index.spec.ts

## 新增或修改路由

- 保持 /items 路由不变
- frontend/src/routes/_layout/items.tsx 改为从 frontend/src/tools/workbench/project_management/components/ProjectManagementPage.tsx 装配页面

## 新增或修改导航

- 无新增导航
- 继续复用现有的 工作台 -> 项目管理 -> /items 入口

## 调用的 API

- ItemsService.readItems
- ItemsService.createItem
- ItemsService.updateItem
- ItemsService.deleteItem

## 执行的验证

- docker compose exec frontend bun run build
- 结果：构建通过
- docker compose exec -T frontend bun x playwright --version
- 结果：Playwright 1.57.0 可执行
- docker compose exec -T frontend bun x playwright test --list tests/items/index.spec.ts tests/workbench/project_management/index.spec.ts
- 结果：命令在当前容器环境中持续挂起，仅输出空行，未返回测试发现结果
- docker compose exec frontend bun x playwright test tests/items/index.spec.ts tests/workbench/project_management/index.spec.ts
- 结果：命令在当前容器环境中持续挂起，仅输出空行，未返回可判定结果
- cd frontend && npm install --no-save @playwright/test@1.57.0 playwright@1.57.0
- 结果：宿主机补齐与仓库一致的 Playwright 1.57.0 本地依赖
- cd frontend && PLAYWRIGHT_DISABLE_WEBSERVER=1 PLAYWRIGHT_BASE_URL=http://localhost:15173 npx playwright test --list tests/items/index.spec.ts tests/workbench/project_management/index.spec.ts
- 结果：成功发现 21 tests in 3 files
- cd frontend && npx playwright install chromium
- 结果：Chromium 与 Chromium Headless Shell 安装完成
- cd frontend && PLAYWRIGHT_DISABLE_WEBSERVER=1 PLAYWRIGHT_BASE_URL=http://localhost:15173 npx playwright test tests/items/index.spec.ts tests/workbench/project_management/index.spec.ts --reporter=line
- 结果：21 passed (22.6s)

## 未完成项

- 无阻塞未完成项。
- frontend/src/components/Items/** 当前仍保留为兼容层，但不影响 /items 路由、tool root 收敛和本轮验收。
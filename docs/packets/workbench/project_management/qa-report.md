# QA Report

## 输入物路径

- design_doc: docs/design/workbench/project_management.md
- test_doc: docs/test/workbench/project_management.md
- task_list: docs/tasks/workbench/project_management.md
- frontend_report: docs/packets/workbench/project_management/frontend-report.md
- backend_report: docs/packets/workbench/project_management/backend-report.md

## 验收范围

- 验收对象：workbench / project_management
- 前端入口保持为 /items
- 后端公开接口保持为 /api/v1/items/ 与 /api/v1/items/{id}
- 验收重点：路径契约稳定、创建/编辑/删除主链路真实跑通、标准测试路径落地、无越界修改

## 执行的验证

- docker compose exec -T backend pytest tests/items/index_test.py tests/workbench/project_management/index_test.py -q
- 结果：44 passed，3 warnings
- cd frontend && PLAYWRIGHT_DISABLE_WEBSERVER=1 PLAYWRIGHT_BASE_URL=http://localhost:15173 npx playwright test tests/items/index.spec.ts tests/workbench/project_management/index.spec.ts --reporter=line
- 结果：21 passed (22.6s)

## 验收结论

- 结论：通过

## 结论依据

- /items 路由保持不变，legacy 路径与标准路径测试都能进入项目管理页面。
- /api/v1/items/ 与 /api/v1/items/{id} 契约保持不变，legacy baseline 与标准后端测试同时通过。
- 创建 -> 编辑 -> 删除主链路已经通过真实 Playwright 用例执行。
- 当前验收范围内未发现 admin、settings、purchase_records、system_management 的越界修改。
- 当前验收范围内未发现 amount 或 test_amount 的无授权公开暴露。

## 运行备注

- frontend 容器内直接执行 bun x playwright test 会持续挂起，因此本轮前端验收采用宿主机锁定版 Playwright 1.57.0 运行。
- 复用当前 compose 启动的 frontend 服务时，PLAYWRIGHT_BASE_URL 必须指向 docker compose port frontend 5173 对应的宿主机端口；本次实际端口为 http://localhost:15173。
# Backend Report

## 输入物路径

- design_doc: docs/design/workbench/project_management.md
- test_doc: docs/test/workbench/project_management.md
- task_list: docs/tasks/workbench/project_management.md

## 目标模块路径

- backend/app/modules/workbench/project_management/

## 修改文件

- backend/app/api/routes/items.py

## 新增文件

- backend/app/modules/workbench/project_management/__init__.py
- backend/app/modules/workbench/project_management/models.py
- backend/app/modules/workbench/project_management/schemas.py
- backend/app/modules/workbench/project_management/repository.py
- backend/app/modules/workbench/project_management/service.py
- backend/app/modules/workbench/project_management/router.py
- backend/tests/workbench/project_management/index_test.py

## 新增或修改接口

- 保持公开接口不变：GET/POST /api/v1/items/，GET/PUT/DELETE /api/v1/items/{id}
- 将 handlers 与 response_model 收敛到 backend/app/modules/workbench/project_management/router.py
- backend/app/api/routes/items.py 改为兼容导出层，api/main.py 无需改动

## 新增或修改模型

- backend/app/modules/workbench/project_management/models.py 复用 app.models.Item
- backend/app/modules/workbench/project_management/schemas.py 复用 ItemCreate、ItemUpdate、ItemPublic、ItemsPublic、Message

## 执行的验证

- docker compose exec backend pytest tests/items/index_test.py tests/workbench/project_management/index_test.py -q
- 结果：44 passed，3 warnings

## 未完成项

- 无阻塞未完成项。
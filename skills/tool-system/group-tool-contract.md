# 工具组与工具契约

## 1. 命名规则

1. group 使用稳定英文标识，推荐 kebab-case 或 snake_case 中与当前仓库一致的一种。
2. tool_key 使用稳定英文标识。
3. 一个工具的前后端目录、测试目录、文档标识必须共享同一组 group 与 tool_key。
4. 用户看到的中文名称与内部 tool_key 必须分离。

## 2. 前端目录契约

新工具的主要前端代码必须位于：

frontend/src/tools/<group>/<tool-key>/

该目录至少应包含：

- api.ts
- types.ts
- schemas.ts
- components/
- hooks/

需要时允许增加：

- constants.ts
- utils.ts
- queries.ts
- mutations.ts
- pages/

## 3. 前端路由契约

1. 路由定义位于 frontend/src/routes/_layout/ 下。
2. 路由文件必须保持薄。
3. 侧边栏入口必须注册到 frontend/src/config/tool-navigation.tsx。
4. 路由路径、导航标识、工具目录三者必须能互相映射。

## 4. 后端目录契约

新工具的主要后端代码必须位于：

backend/app/modules/<group>/<tool-key>/

该目录至少应包含：

- router.py
- service.py
- repository.py
- schemas.py
- models.py

复杂模块允许扩展为子目录，但职责边界必须仍然清晰。

## 5. 测试目录契约

前端测试目录：

frontend/tests/<group>/<tool-key>/

主测试文件：

frontend/tests/<group>/<tool-key>/index.spec.ts

后端测试目录：

backend/tests/<group>/<tool-key>/

主测试文件：

backend/tests/<group>/<tool-key>/index_test.py

## 6. 允许的遗留兼容

1. 已存在的单层前端工具目录允许继续存在。
2. 已存在的单层后端模块目录允许继续存在。
3. 对旧工具做小修时，允许不迁移目录。
4. 新增工具禁止继续采用单层目录。
5. 旧工具若被大幅重写，架构师必须在任务包中明确是否顺带迁移到 group/tool-key 结构。

## 7. 交付物命名契约

架构师交付包中必须明确：

- group
- tool_key
- tool_name
- frontend_route
- frontend_entry_label
- backend_module_root
- frontend_root
- backend_test_root
- frontend_test_root
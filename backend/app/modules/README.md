# 后端模块开发约定

这个项目正在逐步演进为“面向工具”的模块化后端。

## 目标规则

每一个前端工具，都应当对应一个后端模块。一个后端模块负责：

1. 请求与响应 schema
2. 业务 service 逻辑
3. 该领域的数据访问
4. router 注册
5. API 与业务规则测试

## 推荐的模块目录结构

```text
app/modules/<group>/<tool_key>/
  router.py
  service.py
  repository.py
  schemas.py
  models.py
```

历史上已经存在的单层模块目录视为过渡结构。

从现在开始：

1. 新增工具必须使用 `app/modules/<group>/<tool_key>/`。
2. 旧工具小修时允许暂不迁移。
3. 若执行结构迁移，最终目标也必须是 `group/tool_key`。

## 当前迁移策略

- `app/api/routes`、`app/models.py`、`app/crud.py` 下的历史代码暂时仍然有效。
- 新工具优先使用模块内聚的写法。
- 认证、数据库会话处理、公共依赖等共享能力继续保留在 `app/core` 和 `app/api/deps.py`。
- 在迁移过程中，每个新工具都必须保证 OpenAPI 契约足够稳定，能够支持前端客户端生成。

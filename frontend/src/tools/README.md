# 前端工具开发约定

从现在开始，所有新的业务能力都应当按“工具”来实现。

## 工具放置规则

- 一个工具对应 `src/routes/_layout` 下的一个路由。
- 新工具自己的界面代码应放在 `src/tools/<group>/<tool-key>/`。
- 通用基础组件继续放在 `src/components/ui/`。
- 跨工具复用的公共组件继续放在 `src/components/Common/`。
- 侧边栏注册必须写入 `src/config/tool-navigation.tsx`。

历史上已经存在的 `src/tools/<tool-key>/` 单层目录视为过渡结构。

从现在开始：

1. 新增工具必须使用 `src/tools/<group>/<tool-key>/`。
2. 修改旧工具时，若任务范围只是小修，允许暂不迁移。
3. 若架构师明确要求迁移，则迁移后也必须以 `group/tool-key` 为最终结构。

## 推荐的工具目录结构

```text
src/tools/<group>/<tool-key>/
  api.ts
  components/
  hooks/
  schemas.ts
  types.ts
```

## 前端交付规则

新增一个工具时，前端工作必须至少包含以下内容才算完成：

1. 路由
2. 侧边栏注册
3. API 调用封装或查询入口
4. 工具自己的页面组件
5. 覆盖主流程的 Playwright 测试

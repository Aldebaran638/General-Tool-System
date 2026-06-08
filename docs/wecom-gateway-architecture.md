# 企微网关架构说明

## 核心原则

> 企微网关负责"把外部企微世界映射进数据库"；业务模块只看数据库，永远不感知企微 API 的存在。

"分离关注点"靠**文件夹隔离 + import 规则**来维持，不需要独立进程。

---

## 数据流

```
企微服务器
    │  OAuth code / 通讯录数据
    ▼
┌─────────────────────────────┐
│      企微网关（唯一边界）     │  写 DB
│  services/wecom.py          │ ──────────────┐
│  api/routes/wecom_auth.py   │               ▼
│  modules/wecom_gateway/     │   ┌───────────────────────┐
└─────────────────────────────┘   │  数据库                │
                                  │  user                 │
                                  │  department           │
                                  │  wecomconfig          │
                                  │  systemuserrole       │
                                  └──────────┬────────────┘
                                             │  只读
                                             ▼
                                  ┌─────────────────────────┐
                                  │  业务模块                │
                                  │  modules/exam/          │
                                  │  modules/training/      │
                                  │  modules/.../           │
                                  └─────────────────────────┘
```

---

## 文件夹归属

### 企微网关（只在这里开发，禁止溢出）

```
backend/
  app/
    services/
      wecom.py                ← WecomClient，唯一调用企微 API 的地方
    api/routes/
      wecom_auth.py           ← OAuth 路由 /api/auth/wecom/*
    modules/
      wecom_gateway/          ← 通讯录同步、企微状态管理接口
        __init__.py
        router.py
        deps.py               ← CurrentWecomUser、角色守卫
        schemas.py

frontend/
  src/
    routes/auth/
      wecom-callback.tsx      ← OAuth 回调落地页
    hooks/
      useAuth.ts              ← isWecomBrowser / redirectToWecomOAuth
```

### 业务模块（只在这里开发）

```
backend/
  app/
    modules/
      <group>/
        <tool-key>/           ← 一个工具一个文件夹，遵循 tool-module-architecture.md
          __init__.py
          router.py
          models.py
          schemas.py
          crud.py

frontend/
  src/
    routes/_layout/
      <tool>/                 ← 对应工具的前端页面
    tools/
      <group>/
        <tool-key>/           ← 工具自有组件
```

---

## import 规则

| 场景 | 允许 | 禁止 |
|------|------|------|
| 业务模块鉴权 | `from app.modules.wecom_gateway.deps import CurrentWecomUser` | `from app.services.wecom import get_wecom_client` |
| 业务模块数据 | 直接查询 `User`、`department` 等 DB 表 | 调用任何企微 API |
| 企微网关内部 | 调用 `WecomClient`，读写所有 DB 表 | 引用任何业务模块 |

**`CurrentWecomUser` 不算"感知企微"**——它只从 JWT 取出已存 DB 的 `User` 对象，不发任何企微 API 请求，业务模块可以自由使用。

---

## 为什么不单独拆成顶层服务

将 `gateway/` 拆成与 `backend/` 平行的独立服务会引入以下问题，在当前阶段不值得：

1. **数据库归属混乱**：`User`、`department` 表由谁 own？两个服务共享同一张表，Alembic 迁移需要双边协调。
2. **JWT 需要共享**：gateway 签发、backend 验签，必须共享 `SECRET_KEY` 和验证逻辑。
3. **运维成本增加**：多一个 FastAPI 进程、Docker 容器、端口，本地调试链路变长。
4. **跨服务调用**：如果 backend 需要查询企微用户状态，变成 HTTP 内网请求。

**满足以下任一条件时再考虑拆分**：
- 企微网关需要同时服务多个后端系统
- 网关与业务由不同团队维护
- 企微 API 调用量需要独立扩容

---

## 企微登录流程（供前端开发参考）

```
WeCom 浏览器打开工作台
    │
    ▼
_layout.tsx beforeLoad
    │  检测 isWecomBrowser() → true
    │  调用 redirectToWecomOAuth()
    ▼
GET /api/auth/wecom/login          → 302 跳转企微 OAuth 页
    │
    ▼  用户静默授权（snsapi_base，无感知）
    │
GET /api/auth/wecom/callback?code= → code 换 userid → 创建/找到 User → 签发 JWT
    │                                → 302 跳转 /auth/wecom-callback?token=JWT
    ▼
/auth/wecom-callback.tsx           → 写入 localStorage.access_token → 跳转主页
```

普通浏览器访问时 `isWecomBrowser()` 返回 false，走正常登录页，流程不受影响。

---

## 首次上线操作（超管初始化）

`systemuserrole` 表初始为空，需手动插入第一个超管：

```sql
-- 在 Adminer (localhost:18081) 执行
INSERT INTO systemuserrole (userid, role_code)
VALUES ('<企微 userid>', 'SUPER_ADMIN');
```

之后该账号可调用 `POST /api/v1/wecom/sync/all` 同步全公司人员结构。

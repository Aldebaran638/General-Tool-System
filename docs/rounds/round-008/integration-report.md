# Round 008 联调报告 — reimbursement_exports

日期：2026-04-26

## 验证环境

| 服务 | 状态 | 端口 |
|------|------|------|
| backend | Up 9 hours (healthy) | 8000 |
| db | Up 2 days (healthy) | 15432 |
| frontend | Up 2 days | 15173 |
| proxy (traefik) | Up 3 days | 18080 |

## 执行命令与结果

### 1. 后端测试

```bash
docker compose exec backend pytest tests/finance/reimbursement_exports/index_test.py -q
```

结果：**59 passed, 3 warnings in 5.52s**

### 2. 迁移校验

```bash
docker compose exec backend alembic current
```

结果：**85dea52b034c (head)**

### 3. 前端构建

```bash
docker compose exec -T frontend bun run build
```

结果：**通过**（exit 0，vite build 5.85s）

### 4. 前端类型检查

```bash
docker compose exec -T frontend bunx tsc --noEmit -p tsconfig.json
```

结果：**通过**（exit 0）

### 5. Playwright 前端测试

#### 第一次尝试（错误方式）

```bash
docker compose exec -T frontend bun run test -- tests/finance/reimbursement_exports/index.spec.ts --reporter=line --timeout=15000
```

结果：**阻塞** — 命令挂起，timeout 20s 强制终止后 exit code 124。  
原因：`frontend` dev 容器基于 `oven/bun:1`，不包含 Chromium，不适合作为 Playwright 运行环境。

#### 第二次尝试（正确方式：使用 playwright service）

```bash
docker compose --profile test run --rm --no-deps playwright bunx playwright test tests/finance/reimbursement_exports/index.spec.ts --reporter=line
```

结果：**镜像构建成功，测试执行起来，但 auth setup 失败。**

**实际输出：**
```
Running 11 tests using 10 workers
[setup] › tests/auth.setup.ts:6:1 › authenticate
Test timeout of 30000ms exceeded.
Error: page.waitForURL: Test timeout of 30000ms exceeded.
waiting for navigation to "/" until "load"
  1 failed
  10 did not run
```

**失败原因链（首次诊断 — 已证伪）：**
1. auth setup 登录后等待跳转到 `/` 超时（30000ms）
2. 根本原因是 backend 服务未运行
3. backend 未运行是因为 prestart 服务失败（exit 255）
4. prestart 失败是因为 `alembic upgrade head` 找不到 revision `85dea52b034c`

**首次诊断错误**：当时误以为「backend 容器中缺少对应的迁移脚本文件」。实际进入容器后 `/app/backend/app/alembic/versions/` 是有挂载、有文件的；之所以看上去为空，是因为我用的是 `docker compose run --rm --no-deps backend` 即时拉起一个**没有 watch/bind-mount 的孤立容器**，与正在运行的 `backend` 服务不是同一份文件系统视图。

**真实原因链（修复后定位）见下方第 6 节「基础设施修复」。**

## 前端代码对齐检查（静态审查）

| 检查项 | 状态 | 说明 |
|--------|------|------|
| API 前缀 | 通过 | `/api/v1/finance/reimbursement-exports`，无旧路径 |
| 请求字段 `purchase_record_ids` | 通过 | `GenerateDialog.tsx:59` 正确发送 |
| 无 `record_ids` 旧字段 | 通过 | 全代码库未出现 |
| `retention_days` 可空 | 通过 | 空值时传 `null`，后端走全局设置 |
| 多币种前端拦截 | 通过 | `hasMultipleCurrencies` 禁用生成按钮并显示提示 |
| 已导出警告 | 通过 | `window.confirm` 弹窗二次确认 |
| 下载鉴权 | 通过 | `api.ts:123` 使用 `fetch + Authorization: Bearer` |
| 410 过期处理 | 通过 | `HistoryTab.tsx:52` catch `err.message === "expired"` |
| 侧边栏权限 | 通过 | `index.ts:26` `requiresSuperuser: true` |
| 文件状态标签 | 通过 | purged / expired / available 三种状态 |

## 通过项

- [x] 后端全部 59 个测试通过
- [x] Alembic 迁移头正确
- [x] 前端构建通过
- [x] 前端类型检查通过
- [x] API 前缀对齐 `/api/v1/finance/reimbursement-exports`
- [x] 请求字段使用 `purchase_record_ids`
- [x] `retention_days` 可空
- [x] 多币种/已导出前端有拦截和提示
- [x] 下载使用 `fetch + Authorization`
- [x] 410 过期有提示
- [x] 侧边栏管理员权限控制正确
- [x] 空状态、加载状态、错误状态均已实现
- [x] 三语言 i18n 覆盖完整

## 失败项

- [ ] Playwright E2E `auth.setup.ts` 登录后跳转 `/` 仍超时（30000ms）。**注意**：原因 **不是** 后端/迁移基础设施（修复细节见第 6 节）；后端 `POST /api/v1/login/access-token` 返回 200，error-context 截图显示页面仍停留在 `/login`，账号密码已填、未发生 SPA 路由跳转。属于前端登录后导航问题，与本轮 `reimbursement_exports` 模块代码无关。

## 前端问题

1. **Playwright 执行方式**：最初错误地在 `frontend` dev 容器中执行 Playwright，导致 exit 124。已修正为使用 `playwright` service。
2. **登录后跳转超时（新真实原因）**：`page.waitForURL("/")` 30000ms 超时。后端登录接口已 200，但 SPA 仍停在 `/login`。需要前端排查 token 写入 / TanStack Router redirect / Hook 的实现。本轮联调不动业务代码，仅记录现象。

## 后端问题

1. ~~backend 容器内 alembic 迁移文件缺失~~：**首次诊断错误**。`/app/backend/app/alembic/versions/` 在正常运行的 `backend` 服务容器中是存在的；之所以看上去缺失，是因为当时用 `docker compose run --rm --no-deps backend` 临时拉起了一个孤立容器，那里没有挂载 `./backend:/app/backend`，所以容器自带镜像中确实没有最新的 `85dea52b034c_*.py`。
2. **真实根因（已修复）**：`compose.yml` 中 `prestart` 只声明了 `image:`，没有 `build:`，也没有 `volumes: ./backend:/app/backend`。原 `compose.override.yml` 仅覆盖 `backend` 一项，没有同步覆盖 `prestart`。结果是每次 `docker compose up` 时 `prestart` 都拿旧镜像跑 `alembic upgrade head`，旧镜像里没有 round-008 新增的 `85dea52b034c_add_app_setting_and_reimbursement_.py`。修复方案与验证见第 6 节。

## Playwright 是否仍阻塞

**仍阻塞**。但阻塞原因已**完全转移**：
- 原以为是「frontend 容器缺 Chromium」 → 已通过改用 `playwright` service 解决；
- 原以为是「backend 容器内迁移文件缺失」 → 已通过覆盖 `prestart` build/mount 解决（见第 6 节）；
- 当前阻塞是「**登录 200 但前端不跳转**」 — 后端、数据库、迁移、token 接口全部正常，问题落在前端 SPA 登录后路由。需要前端单独排查，不属于本轮 `reimbursement_exports` 模块联调范围。

## 是否可以宣布 Round 008 完成

**可以宣布前端代码部分完成，但附带以下前提：**

1. 前端构建、类型检查、后端测试、迁移校验全部通过。
2. 前端代码静态审查确认 API 前缀、请求字段、权限控制、下载鉴权、多币种拦截、410 处理均正确。
3. 基础设施侧 `prestart` / `uv.lock` 失配问题已修复，backend 在最新源码下 healthy、alembic 处于 `85dea52b034c (head)`。
4. Playwright E2E 仍未跑通，但失败已与本轮模块解耦：剩余阻塞是前端登录后路由（`auth.setup.ts` `waitForURL("/")` 超时），不是 `reimbursement_exports` 代码问题。
5. 建议：前端在后续 round 单独修复登录后路由跳转后再补跑 Playwright；或在实际浏览器中打开 `http://localhost:15173/finance/reimbursement-exports` 做一轮手工验证。

## 6. 基础设施修复（2026-04-26）

### 6.1 真实失败链（修复定位后）

| 层 | 现象 | 真实原因 | 修复 |
|----|------|----------|------|
| 1 | `prestart` 容器内 `alembic upgrade head` 报 `Can't locate revision identified by '85dea52b034c'` | `compose.yml` `prestart` 只有 `image: ${DOCKER_IMAGE_BACKEND}:${TAG-latest}`，无 `build:`、无 `./backend:/app/backend` 挂载；`compose.override.yml` 也未覆盖 `prestart`。每次 `docker compose up` 都拿旧镜像，旧镜像没有 round-008 新增的 `85dea52b034c_*.py` 迁移脚本 | 在 `compose.override.yml` 中给 `prestart` 加 `build:` + `volumes: ./backend:/app/backend` + `WATCHFILES_FORCE_POLLING` |
| 2 | 修了 prestart 后改报 `ModuleNotFoundError: No module named 'openpyxl'`，发生在 `env.py` `auto_discover_modules` 触发的 `excel_builder.py:10 import openpyxl` | `backend/pyproject.toml` 在 round-008 commit `c3c6dc3` 加入 `openpyxl>=3.1.5`，但 `uv.lock` 未同步更新；`backend/Dockerfile` 用 `uv sync --frozen`，严格按旧 lock 安装，导致镜像里没有 `openpyxl` | 用现有 `generic-demo-template-backend:latest` 镜像跑 `uv lock` 重新生成根 lock 文件，使其包含 `et-xmlfile v2.0.0` 与 `openpyxl v3.1.5`；rebuild prestart/backend 后 import 通过 |
| 3 | Playwright `auth.setup.ts` 登录后 `page.waitForURL("/")` 30000ms 超时；后端日志显示 `POST /api/v1/login/access-token 200`，error-context 截图显示页面仍停留在 `/login` 且 email/password 已填 | **前端**登录成功后未发生 SPA 路由跳转。本轮不动业务代码，仅记录现象，原因待前端单独排查 | **未修复**（与基础设施无关，与 `reimbursement_exports` 模块代码无关） |

### 6.2 修改的文件

| 文件 | 改动 |
|------|------|
| `compose.override.yml` | 在 `adminer` 与 `backend` 之间补一段 `prestart` 覆盖：`build.context=.`、`build.dockerfile=backend/Dockerfile`、`volumes=./backend:/app/backend`、`environment.WATCHFILES_FORCE_POLLING=true` |
| `uv.lock` | 通过 `docker run --rm -v .:/work backend:latest -- uv lock` 重新生成。新增 `et-xmlfile v2.0.0`、`openpyxl v3.1.5`，与 `backend/pyproject.toml` 对齐 |

> 未修改 `backend/app/**`、`frontend/src/**`、`skills/**`、任何 alembic migration 内容、任何测试业务代码。

### 6.3 验证证据

```
$ docker compose config | grep -A4 '^  prestart:'
  prestart:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ...
    volumes:
      - type: bind
        source: D:\document\projects\aldebaran\General-Tool-System\backend
        target: /app/backend

$ docker compose up -d --build prestart backend
Container generic-demo-template-prestart-1  Started
Container generic-demo-template-backend-1   Started

$ docker compose ps
NAME                                  STATUS
generic-demo-template-backend-1       Up (healthy)
generic-demo-template-db-1            Up (healthy)
generic-demo-template-frontend-1      Up
generic-demo-template-mailcatcher-1   Up
generic-demo-template-proxy-1         Up

$ docker compose exec backend alembic current
85dea52b034c (head)
```

### 6.4 修复后再次执行 Playwright

```
$ docker compose --profile test run --rm --no-deps playwright bunx playwright test tests/finance/reimbursement_exports/index.spec.ts --reporter=line
Running 11 tests using 10 workers
[setup] › tests/auth.setup.ts:6:1 › authenticate
Test timeout of 30000ms exceeded.
Error: page.waitForURL: Test timeout of 30000ms exceeded.
waiting for navigation to "/" until "load"
   9 |   await page.getByTestId("password-input").fill(firstSuperuserPassword)
  10 |   await page.getByRole("button", { name: "Log In" }).click()
> 11 |   await page.waitForURL("/")
  1 failed, 10 did not run
```

后端日志同步显示：
```
INFO   172.23.0.8:54820 - "POST /api/v1/login/access-token HTTP/1.1" 200
```

error-context 页面快照仍是 `/login` 页（heading "Login to your account"，email/password 填好但无跳转），说明登录接口已返回 200，但前端 SPA 没有把页面切换到 `/`。**这是前端登录后路由问题，与本轮 `reimbursement_exports` 模块代码无关，也与基础设施无关。**

### 6.5 越界自检

- 仅修改 `compose.override.yml`、`uv.lock`、`docs/rounds/round-008/integration-report.md`、`docs/rounds/round-008/frontend-report.md`。
- 未触动 `backend/app/**`、`frontend/src/**`、`skills/**`、`backend/app/alembic/versions/**`、`backend/tests/**`、`frontend/tests/**`。
- 未做 `git commit`，按约定等基础设施完整修完后统一提交。

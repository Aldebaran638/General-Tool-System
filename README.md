# 课程培训及考核管理平台

本仓库同时受 **Git** 和 **SVN** 双版本控制管理：

- **Git**：日常开发、分支管理、代码审查
- **SVN**：与远程 Exam 服务器 (`192.168.3.109`) 同步，用于部署

> 注意：`.git/`、`.env`、`node_modules/`、`backend/.venv/` 等文件已被 SVN 忽略，不会进入远程服务器。

---

## 目录

- [本地开发启动](#本地开发启动)
- [远程部署启动](#远程部署启动)
- [本地与远程的差异](#本地与远程的差异)
- [SVN 工作流](#svn-工作流)
- [服务端口](#服务端口)
- [企业微信后台配置](#企业微信后台配置)
- [OAuth 登录流程](#oauth-登录流程)
- [常用命令](#常用命令)
- [目录说明](#目录说明)
- [常见问题](#常见问题)

---

## 本地开发启动

### 前置条件

- Docker / Docker Compose
- `cloudflared`（用于生成临时公网隧道）
- 已存在 `.env` 文件（从 `.env.example` 复制并修改）

### 启动命令

```bash
./dev-start.sh
```

`dev-start.sh` 会依次执行：

1. 端口冲突检查
2. 启动基础设施：`db`、`adminer`、`mailcatcher`
3. 启动 Cloudflare 临时隧道，获得公网 URL
4. 更新 `.env`、`backend/.env`、`frontend/.env` 中的域名和 CORS 配置
5. 启动 `backend`、`frontend` 应用容器
6. 生成 ChartDB 导入结果
7. 检查并补全前端依赖
8. 等待服务就绪并验证公网可达性
9. 输出企业微信后台配置指引

### 本地使用的 Compose 文件

- `compose.yml`：基础服务定义
- `compose.override.yml`：本地开发覆盖，包括端口映射、热重载挂载、调试命令等

### 本地访问地址

| 服务 | 地址 |
|------|------|
| 前端 (Vite) | http://localhost:10106 |
| 后端 (FastAPI) | http://localhost:10105 |
| Swagger 文档 | http://localhost:10105/api/v1/docs |
| Adminer (数据库管理) | http://localhost:10104 |
| ChartDB | http://localhost:10107 |
| MailCatcher (邮件) | http://localhost:10108 |
| PostgreSQL | localhost:10103 |
| Traefik UI | http://localhost:10102 |

> 每次运行 `./dev-start.sh` 都会生成新的 Cloudflare 临时域名，企业微信后台需要重新配置。

### 重启后正确恢复

重启电脑后，Cloudflare 隧道会丢失，需要重新运行 `./dev-start.sh`。

**不能用 `docker compose restart`，必须用 `docker compose up -d --force-recreate`**

原因：`restart` 只是重启容器进程，不会重新读取 `.env` 文件。更新 `.env` 中的域名后，必须 `--force-recreate` 重建容器才能让新配置生效。`dev-start.sh` 已自动处理这个问题。

**端口冲突排查**

如果其他项目的容器占用了 10101~10109 端口，启动会失败：

```bash
docker ps --format '{{.Names}}\t{{.Ports}}' | grep -E '1010[0-9]'
```

停掉冲突的容器：

```bash
docker stop <容器名>
```

---

## 远程部署启动

远程 Exam 服务器通过 SVN 获取代码，再用 Docker Compose 启动。

### 服务器信息

- **IP**：`192.168.3.109`
- **项目目录**：`/opt/course-training-assessment`
- **部署脚本**：`/tmp/deploy-remote.sh`

### 前置条件（已配置）

- 服务器已安装 Docker、Docker Compose、SVN
- 基础镜像已传输到服务器：`postgres:18`、`traefik:3.6`、`adminer`、`schickling/mailcatcher`、`ghcr.io/chartdb/chartdb:latest`、`node:20-bookworm`
- 前端镜像在本地构建后传输到服务器：`course-training-assessment-frontend:latest`
- 后端镜像在服务器上构建：`course-training-assessment-backend:latest`

### 启动命令

在远程服务器上执行：

```bash
bash /tmp/deploy-remote.sh
```

`deploy-remote.sh` 会依次执行：

1. `svn update` 拉取最新代码
2. `docker compose -f compose.yml -f compose.remote.yml up -d --build backend` 构建并启动后端
3. `docker compose -f compose.yml -f compose.remote.yml up -d` 启动全部服务
4. `docker compose -f compose.yml -f compose.remote.yml ps` 查看容器状态

### 远程使用的 Compose 文件

- `compose.yml`：基础服务定义
- `compose.remote.yml`：远程部署覆盖，**不加载 `compose.override.yml`**

### 远程访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://192.168.3.109:10106 |
| 后端 | http://192.168.3.109:10105 |
| Swagger | http://192.168.3.109:10105/api/v1/docs |
| Adminer | http://192.168.3.109:10104 |
| ChartDB | http://192.168.3.109:10107 |
| MailCatcher | http://192.168.3.109:10108 |
| Traefik Dashboard | http://192.168.3.109:10102 |

---

## 本地与远程的差异

| 维度 | 本地开发 | 远程部署 |
|------|----------|----------|
| 启动脚本 | `./dev-start.sh` | `/tmp/deploy-remote.sh` |
| Compose 文件 | `compose.yml` + `compose.override.yml` | `compose.yml` + `compose.remote.yml` |
| 前端镜像 | 本地构建/挂载源码热重载 | 本地构建好传到远程，直接运行镜像 |
| 前端 `node_modules` | 挂载宿主 `./node_modules` | 使用镜像内已复制好的 `node_modules`，无卷挂载 |
| 后端 | 挂载 `./backend` 热重载 | 远程构建镜像，同时挂载 `./backend` 热重载 |
| 公网访问 | Cloudflare 临时隧道 | 通过服务器 IP + 端口访问 |
| 额外操作 | 启动隧道、更新 `.env`、企业微信配置 | `svn update` |

### 为什么前端处理方式不同？

远程服务器访问 npm/bun 注册中心不稳定，前端依赖下载极慢或超时。因此：

- **本地**：正常安装依赖，`compose.override.yml` 将 `./node_modules` 挂载进容器
- **远程**：本地先执行 `npm install`，再用 `frontend/Dockerfile.dev-export` 构建镜像，把 `node_modules` 打包进镜像，最后 `docker save` 传输到远程 `docker load`

这样远程启动时不需要再下载前端依赖。

---

## SVN 工作流

本地代码变更要同步到远程，必须通过 SVN 提交。

### 已忽略的文件

以下内容不会被提交到 SVN，也不会同步到远程：

- `.git/`（Git 元数据）
- `.env`、`.env-example`、`backend/.env`、`frontend/.env`
- `node_modules/`、`frontend/node_modules/`
- `backend/.venv/`
- 构建缓存：`.vite/`、`dist/`、`__pycache__/`、`*.pyc`
- 测试产物：`frontend/test-results/`、`frontend/blob-report/`
- 上传目录：`backend/app/uploads/`、`img/`
- IDE/工具目录：`.claude/`、`.vscode/`、`.idea/`
- 日志文件：`*.log`

### 提交变更

```bash
cd ~/course-training-assessment

# 查看变更
svn status

# 如果有新增文件/目录，先 add
svn add 新文件或目录

# 提交
svn commit -m "描述信息"
```

### 远程更新

提交后，在远程服务器执行：

```bash
cd /opt/course-training-assessment
svn update
```

或者直接运行部署脚本：

```bash
bash /tmp/deploy-remote.sh
```

### Git 与 SVN 的关系

- 代码开发、分支、PR 继续走 Git
- 需要部署到远程时，把相关文件 `svn commit`
- 两个 VCS 互不干扰，`.git/` 已被 SVN 忽略

---

## 服务端口

| 端口 | 服务 | 说明 |
|------|------|------|
| 10101 | Traefik HTTP | 反向代理入口 |
| 10102 | Traefik Dashboard | 路由监控面板 |
| 10103 | PostgreSQL | 数据库 |
| 10104 | Adminer | 数据库管理 |
| 10105 | FastAPI 后端 | API 服务 |
| 10106 | Vite 前端 | 开发服务器 |
| 10107 | ChartDB | 数据库图表 |
| 10108 | MailCatcher Web | 邮件查看 |
| 10109 | MailCatcher SMTP | 邮件发送 |

---

## 企业微信后台配置

每次隧道域名变化后，需要在企业微信管理后台（work.weixin.qq.com/wework_admin）更新以下三个配置。

假设隧道域名为 `xxx.trycloudflare.com`（实际域名以 `dev-start.sh` 输出为准）：

### 1. 可信域名（基础）

**位置**：应用管理 → 选择目标应用 → 网页授权及JS-SDK → 设置可信域名

**填写内容**：只填域名，不带 `https://`，不带路径

```
xxx.trycloudflare.com
```

这是最基础的配置。授权回调域和应用主页的域名都必须在这个可信域名范围内，否则企微会报 "redirect_uri需使用应用可信域名" 错误。

### 2. 授权回调域

**位置**：应用管理 → 选择目标应用 → 企业微信授权登录 → 设置授权回调域

**填写内容**：只填域名，不带 `https://`，不带路径

```
xxx.trycloudflare.com
```

后端构造的 OAuth 回调地址格式为：
```
https://{域名}/api/auth/wecom/callback
```

企微会校验回调地址的域名是否与授权回调域匹配。如果域名不一致，OAuth 流程会失败。

### 3. 应用主页

**位置**：应用管理 → 选择目标应用 → 应用主页

**填写内容**：完整 URL，带 `https://`，末尾带 `/`

```
https://xxx.trycloudflare.com/
```

这是员工在企业微信工作台点击应用时进入的地址。域名必须在可信域名范围内。

### 配置验证

配置完成后，可以访问以下地址验证域名校验文件是否正常：

```
https://xxx.trycloudflare.com/WW_verify_xxx.txt
```

返回企业微信后台下载的校验文件内容，即表示域名校验通过。真实 `WW_verify_*.txt` 文件只放在本地或部署环境，不提交到 Git。

---

## OAuth 登录流程

1. 企微内打开应用 → 前端检测到企微 UA → 跳转 `/api/auth/wecom/login`
2. 后端 302 到企微 OAuth 页面（redirect_uri = `{FRONTEND_HOST}/api/auth/wecom/callback`）
3. 员工授权 → 企微回调到后端 → 后端换取 userid、签发 JWT
4. 后端 302 到前端 `/auth/wecom-callback?token=JWT`
5. 前端存入 localStorage，进入主界面

PC 端调试登录：直接访问 `https://xxx.trycloudflare.com/api/auth/wecom/login`

---

## 常用命令

一键启动本地开发（推荐）：
```bash
./dev-start.sh
```

手动启动本地（不使用隧道）：
```bash
docker compose up -d --force-recreate
```

清理旧容器并重启本地：
```bash
docker compose down --remove-orphans
docker compose up -d --force-recreate
```

查看容器状态：
```bash
docker compose ps -a
```

验证后端健康：
```bash
curl http://localhost:10105/api/v1/utils/health-check/
```

远程部署：
```bash
bash /tmp/deploy-remote.sh
```

---

## 目录说明

- `frontend/`：前端代码 (React + Vite + TanStack Router)
- `backend/`：后端代码 (FastAPI + SQLModel)
- `docs/`：文档
- `skills/`：AI 工作规范
- `dev-start.sh`：一键开发环境启动脚本
- `deploy-remote.sh`：远程部署脚本（位于服务器 `/tmp/`）
- `compose.yml`：基础 Docker Compose 配置
- `compose.override.yml`：本地开发覆盖配置
- `compose.remote.yml`：远程部署覆盖配置

---

## 常见问题

### 前端白屏，浏览器控制台报 `_jsxDEV is not a function`

原因：Vite dev 模式下 `NODE_ENV` 不是 `development`，导致 React JSX 转换异常。
解决：确保 `compose.override.yml` 或 `compose.remote.yml` 中前端环境变量包含 `NODE_ENV: "development"`。

### 远程前端提示 `@tanstack/router-plugin` 找不到

原因：`compose.override.yml` 的卷挂载把镜像里的 `node_modules` 覆盖了。
解决：远程使用 `compose.remote.yml`，不要加载 `compose.override.yml`。

### 远程 `docker compose up` 拉取镜像超时

原因：远程服务器无法访问 Docker Hub。
解决：基础镜像需要提前通过 `docker save` / `docker load` 传输到服务器。

### 后端数据库迁移失败

如果迁移记录和实际数据库状态不一致，可以清理数据卷后重新启动（会丢失数据）：

```bash
docker compose down -v
docker compose up -d
```

生产环境请勿随意执行 `-v`。

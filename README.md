# 课程培训及考核管理平台

## 快速启动

在 WSL (Ubuntu 24.04) 中执行：

```bash
cd /home/winkey/course-training-assessment
./dev-start.sh
```

脚本会自动完成：
1. 检查端口冲突
2. 启动 docker compose 全部服务
3. 启动 Cloudflare 临时隧道
4. 更新 `.env` / `backend/.env` / `frontend/.env` 中的域名配置
5. 重建后端容器使新配置生效
6. 验证公网可达性
7. 打印企微后台配置指引

### 依赖

- Docker + Docker Compose
- cloudflared（`/usr/local/bin/cloudflared`）
- curl, python3

## 本地服务地址

| 服务 | 地址 |
|------|------|
| 前端 (Vite) | http://localhost:8000 |
| 后端 (FastAPI) | http://localhost:8001 |
| Swagger 文档 | http://localhost:8001/api/v1/docs |
| Adminer (数据库管理) | http://localhost:18081 |
| MailCatcher (邮件) | http://localhost:1180 |
| PostgreSQL (宿主机) | localhost:15432 |
| Traefik UI | http://localhost:18090 |

## 重启后正确恢复

重启电脑后，Cloudflare 隧道会丢失，需要重新运行 `./dev-start.sh`。

### 关键注意事项

**不能用 `docker compose restart`，必须用 `docker compose up -d --force-recreate`**

原因：`restart` 只是重启容器进程，不会重新读取 `.env` 文件。更新 `.env` 中的域名后，必须 `--force-recreate` 重建容器才能让新配置生效。`dev-start.sh` 已自动处理这个问题。

**端口冲突**

如果其他项目的容器占用了 8001/8000/15432 端口，启动会失败。排查方法：

```bash
docker ps --format '{{.Names}}\t{{.Ports}}' | grep -E '8001|8000|15432'
```

停掉冲突的容器：

```bash
docker stop <容器名>
```

**隧道域名每次会变**

临时隧道每次重启会分配新的 `*.trycloudflare.com` 域名，需要重新去企微后台更新配置。

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
https://xxx.trycloudflare.com/WW_verify_HUz4rWBElVbwEoOX.txt
```

返回 `HUz4rWBElVbwEoOX` 即表示域名校验通过。

## OAuth 登录流程

1. 企微内打开应用 → 前端检测到企微 UA → 跳转 `/api/auth/wecom/login`
2. 后端 302 到企微 OAuth 页面（redirect_uri = `{FRONTEND_HOST}/api/auth/wecom/callback`）
3. 员工授权 → 企微回调到后端 → 后端换取 userid、签发 JWT
4. 后端 302 到前端 `/auth/wecom-callback?token=JWT`
5. 前端存入 localStorage，进入主界面

PC 端调试登录：直接访问 `https://xxx.trycloudflare.com/api/auth/wecom/login`

## 常用命令

一键启动（推荐）：
```bash
./dev-start.sh
```

手动启动（不使用隧道）：
```bash
docker compose up -d --force-recreate
```

清理旧容器并重启：
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
curl http://localhost:8001/api/v1/utils/health-check/
```

## 目录说明

- `frontend/`：前端代码 (React + Vite + TanStack Router)
- `backend/`：后端代码 (FastAPI + SQLModel)
- `docs/`：文档
- `skills/`：AI 工作规范
- `dev-start.sh`：一键开发环境启动脚本
- `compose.yml` / `compose.override.yml`：Docker Compose 配置

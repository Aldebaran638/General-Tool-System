# 项目管理面板

基于 FastAPI + React + Docker Compose 的项目管理面板。

## 技术栈

- **后端**：Python 3.11+、FastAPI、SQLModel、PostgreSQL
- **前端**：React、TypeScript、Vite、Bun
- **运维/工具**：Docker Compose、Traefik、Adminer、MailCatcher、ChartDB、uv、pre-commit
- **测试**：Playwright（前端 E2E）、pytest（后端）

## 快速启动

1. 准备环境文件：

   ```bash
   cp .env-example .env
   ```

2. 启动完整本地栈（会自动监听代码变更并热重载）：

   ```bash
   docker compose watch
   ```

3. 首次启动可能需要等待数据库初始化完成，可通过 `prestart` 服务执行迁移和种子数据。

## 本地服务地址

默认端口来自 `compose.override.yml`：

| 服务 | 地址 |
|---|---|
| 前端 | http://localhost:10116 |
| 后端 API | http://localhost:10105 |
| Swagger 文档 | http://localhost:10105/docs |
| ReDoc 文档 | http://localhost:10105/redoc |
| Adminer | http://localhost:10104 |
| MailCatcher | http://localhost:10108 |
| ChartDB | http://localhost:10107 |
| Traefik Dashboard | http://localhost:10102 |

## 验证

```bash
docker compose ps -a
curl http://localhost:10105/api/v1/utils/health-check/
```

## 常用命令

| 操作 | 命令 |
|---|---|
| 启动项目 | `docker compose watch` |
| 停止并清理容器 | `docker compose down --remove-orphans` |
| 查看日志 | `docker compose logs -f backend` |
| 生成前端 API 客户端 | `bash scripts/generate-client.sh` |
| 前端 lint | `bun run lint` |
| 后端 lint / 格式化 | `uv run ruff check .` / `uv run ruff format .` |
| 后端测试 | `uv run pytest` |
| 前端测试 | `bun run --filter frontend test` |

Windows 开发者可运行 `bootstrap-dev.ps1` 初始化本机 Python 虚拟环境、安装依赖与 Playwright 浏览器。

## 目录说明

- `backend/`：后端源码、测试、Dockerfile、依赖配置
- `frontend/`：前端源码、测试、Playwright 配置
- `hooks/`：copier 模板生成后钩子
- `scripts/`：开发/CI 辅助脚本
- `compose.yml`：生产型 Docker Compose 主配置
- `compose.override.yml`：本地开发覆盖配置（端口映射、热重载、额外工具）
- `compose.traefik.yml`：使用外部 Traefik 的部署配置
- `development.md`：通用开发说明
- `deployment.md`：部署说明
- `prompt.md`：项目架构师/AI 协作规范

## 注意事项

- 根目录必须存在 `.env`，不能只放 `.env-example`。
- 建议保留 `.env` 中的 `COMPOSE_PROJECT_NAME=project-management-board`，让容器名称保持统一前缀。
- `docker-ps-check.err.log` 等临时日志已忽略，无需手动清理。
- 生产部署请参考 `deployment.md` 和 `compose.traefik.yml`。

# Generic Demo Template

这是一个基于 FastAPI + React + Docker Compose 的通用演示模板。

## 一句话结论

- 只想把项目跑起来：优先按 [docs/本地启动与排障说明.md](docs/%E6%9C%AC%E5%9C%B0%E5%90%AF%E5%8A%A8%E4%B8%8E%E6%8E%92%E9%9A%9C%E8%AF%B4%E6%98%8E.md) 执行。
- 当前已经验证可走通的本地启动命令是 `docker compose watch`。
- 当前仓库要求根目录存在 `.env`，不能只放 `.env-example`。

## 1. 推荐阅读顺序

如果你是第一次接手这个仓库，按下面顺序看：

1. [docs/本地启动与排障说明.md](docs/%E6%9C%AC%E5%9C%B0%E5%90%AF%E5%8A%A8%E4%B8%8E%E6%8E%92%E9%9A%9C%E8%AF%B4%E6%98%8E.md)
2. [development.md](development.md)
3. [deployment.md](deployment.md)

说明：

- 第一份是当前仓库已经实际验证可跑通的本地流程。
- 第二份是项目的通用开发说明。
- 第三份更接近模板化生产部署说明，不代表当前仓库所有步骤都已经逐项验证。

## 2. 当前已验证可走通的本地流程

### 第一步：准备环境文件

如果根目录还没有 `.env`，先执行：

```bash
cp .env-example .env
```

### 第二步：启动

在项目根目录执行：

```bash
docker compose watch
```

### 第三步：验证是否真的跑通

```bash
docker compose ps -a
curl http://localhost:8000/api/v1/utils/health-check/
```

成功后可访问：

- 前端：http://localhost:5173
- 后端：http://localhost:8000
- Swagger：http://localhost:8000/docs
- Adminer：http://localhost:8080
- MailCatcher：http://localhost:1080
- Traefik UI：http://localhost:8090

补充：

- 当前数据库宿主机端口使用 15432，不再占用本机 5432。
- `prestart` 容器退出码为 0 属于正常现象。

## 3. 开发者初始化

如果你要参与开发，可以在项目根目录执行：

```powershell
.\bootstrap-dev.ps1
```

执行前需要先满足以下条件：

- 已安装 `Python 3.11`
- 已安装 `Node.js` 与 `npm`
- 已安装 `Docker Desktop`

说明：

- 后端开发环境固定使用 `Python 3.11`
- `bootstrap-dev.ps1` 会使用本机 Python 创建 `backend/.venv`
- 如果你只是运行项目，不需要本机安装 Python，直接按本 README 上面的本地流程启动

## 4. 常用命令

启动项目：

```bash
docker compose watch
```

清理旧容器并重启：

```bash
docker compose down --remove-orphans
docker compose watch
```

初始化开发环境：

```powershell
.\bootstrap-dev.ps1
```

运行前端构建：

```bash
npm --prefix frontend run build
```

运行前端 Playwright 测试：

```bash
cd frontend
npx playwright test --reporter=line
```

运行后端测试：

```powershell
backend\.venv\Scripts\python.exe -m pytest
```

## 5. 目录说明

- `frontend/`：前端代码
- `backend/`：后端代码
- `docs/`：运行说明与模板文档
- `skills/`：架构师、前端、后端、测试 AI 的工作规范
- `bootstrap-dev.ps1`：开发者初始化脚本

## 6. 说明

- 如果只是使用项目，不需要手动创建后端虚拟环境。
- 如果只是运行项目，不需要手动安装 Playwright 浏览器。
- 只有参与开发和测试时，才需要执行 `.\bootstrap-dev.ps1`。
- 本地启动优先以 [docs/本地启动与排障说明.md](docs/%E6%9C%AC%E5%9C%B0%E5%90%AF%E5%8A%A8%E4%B8%8E%E6%8E%92%E9%9A%9C%E8%AF%B4%E6%98%8E.md) 为准。

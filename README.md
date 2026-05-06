# 通用工具系统 / General Tool System

基于 **FastAPI + React + Docker Compose** 的通用工具系统，当前主要承载**发票管理系统**（Invoice Management System）。

---

## 功能概览

- **购买记录管理** — 上传截图、OCR 识别、记录采购信息
- **发票文件管理** — 上传发票 PDF、提取发票信息
- **发票匹配** — 智能匹配购买记录与发票文件，支持候选推荐与手动搜索
- **管理员审核** — 管理员审核已确认的发票匹配记录，审核通过后进入可报销状态
- **报销导出** — 按条件筛选已审核匹配记录，生成 Excel 报销单

---

## 启动说明

### 环境要求

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- （可选）Python 3.11 + Node.js — 仅本地开发时需要

验证安装：

```bash
docker --version
docker compose version
```

### 快速启动（推荐）

```bash
# 1. 克隆仓库后进入根目录
cd General-Tool-System

# 2. 创建环境文件
cp .env-example .env

# 3. 启动全部服务（首次构建需要几分钟）
docker compose watch
```

### 验证启动

```bash
# 查看容器状态
docker compose ps -a

# 验证后端健康检查
curl http://localhost:8000/api/v1/utils/health-check/
# 期望返回：true
```

### 访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:15173 |
| 后端 API | http://localhost:8000 |
| Swagger 文档 | http://localhost:8000/docs |
| Adminer (数据库管理) | http://localhost:18081 |
| MailCatcher (邮件调试) | http://localhost:1180 |
| Traefik Dashboard | http://localhost:18090 |

> **注意**：数据库宿主机端口映射为 `15432`，避免与本地 PostgreSQL 冲突。`prestart` 容器退出码为 0 属于正常现象。

### 停止服务

```bash
# 停止并移除容器
docker compose down --remove-orphans

# 停止并移除容器 + 数据卷（谨慎使用）
docker compose down --remove-orphans -v
```

---

## 本地开发

如果你需要参与开发（修改代码、运行测试），建议执行开发者初始化脚本：

```powershell
# Windows PowerShell
.\bootstrap-dev.ps1
```

前置条件：

- Python 3.11
- Node.js + npm
- Docker Desktop

脚本会自动创建后端虚拟环境 (`backend/.venv`) 并安装依赖。

### 前端独立开发（不依赖 Docker）

```bash
cd frontend
npm install
npm run dev
```

前端将运行在 http://localhost:5173，并通过 Vite 代理自动转发 `/api` 请求到 http://localhost:8000。

### 后端独立开发

```bash
cd backend
# 确保虚拟环境已激活
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux

# 运行后端（热重载）
fastapi run --reload app/main.py
```

### 数据库迁移

新增或修改模型后，需要生成并执行迁移：

```bash
cd backend

# 生成迁移脚本
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

> 在 Docker 环境中，`prestart` 容器会自动执行 `alembic upgrade head`。

---

## 测试

### 前端测试（Playwright）

```bash
cd frontend
npx playwright test --reporter=line
```

### 后端测试（pytest）

```powershell
backend\.venv\Scripts\python.exe -m pytest
```

---

## 项目结构

```
General-Tool-System/
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── modules/
│   │   │   └── finance/   # 财务模块（购买记录、发票文件、发票匹配、报销导出）
│   │   ├── alembic/       # 数据库迁移
│   │   └── main.py        # 应用入口
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/              # React + Vite 前端
│   ├── src/
│   │   ├── tools/
│   │   │   └── finance/   # 财务工具页面
│   │   ├── components/ui/ # shadcn/ui 组件
│   │   └── i18n/          # 国际化字典
│   ├── Dockerfile
│   └── package.json
├── docs/                  # 文档
├── compose.yml            # Docker Compose 基础配置
├── compose.override.yml   # 本地开发覆盖配置
├── .env-example           # 环境变量模板
└── bootstrap-dev.ps1      # 开发者初始化脚本
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11, FastAPI, SQLModel, SQLAlchemy, Alembic, PostgreSQL |
| 前端 | React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Router, TanStack Query |
| 测试 | Playwright (E2E), pytest (单元/集成) |
| 部署 | Docker, Docker Compose, Traefik |

---

## 相关文档

- [本地启动与排障说明](docs/%E6%9C%AC%E5%9C%B0%E5%90%AF%E5%8A%A8%E4%B8%8E%E6%8E%92%E9%9A%9C%E8%AF%B4%E6%98%8E.md)
- [development.md](development.md)
- [deployment.md](deployment.md)

# 固定 IP 生产部署

本部署用于没有域名、仅通过固定局域网 IP 访问的环境。当前服务器地址为
`192.168.3.187`，浏览器统一访问：

```text
http://192.168.3.187
```

Traefik 独占宿主机 TCP 80，并将 `/api/*` 转发到 Docker 内部后端，
其余请求转发到前端。数据库、前端、后端和 `work-report-reminder`
均不直接映射宿主机端口。

## 环境变量

生产 `.env` 至少包含：

```dotenv
ENVIRONMENT=production
DOMAIN=192.168.3.187
FRONTEND_HOST=http://192.168.3.187
BACKEND_CORS_ORIGINS=http://192.168.3.187
FEISHU_REDIRECT_URI=http://192.168.3.187/api/v1/login/feishu/callback
AUTH_COOKIE_SECURE=false

POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_DB=app
POSTGRES_USER=postgres

FIRST_SUPERUSER=zhongsihan@winkey-china.com
```

`AUTH_COOKIE_SECURE=false` 仅用于可信局域网内的 HTTP 部署。若以后启用 HTTPS，
应删除该覆盖或改为 `true`。

## 启动

必须同时指定主配置和固定 IP 生产覆盖，不得加载开发环境的
`compose.override.yml`：

```bash
docker network inspect traefik-public >/dev/null 2>&1 \
  || docker network create traefik-public

docker compose \
  -f compose.yml \
  -f compose.production-ip.yml \
  config

docker compose \
  -f compose.yml \
  -f compose.production-ip.yml \
  up -d --build proxy db backend frontend work-report-reminder
```

`prestart` 会自动执行数据库迁移和初始管理员创建。`adminer` 位于 `ops`
profile，默认不会启动。

## 验证

```bash
docker compose -f compose.yml -f compose.production-ip.yml ps
docker compose -f compose.yml -f compose.production-ip.yml logs --tail 100 prestart
docker compose -f compose.yml -f compose.production-ip.yml logs --tail 100 backend
docker compose -f compose.yml -f compose.production-ip.yml logs --tail 100 work-report-reminder
curl http://192.168.3.187/api/v1/utils/health-check/
```

飞书后台的重定向 URL 必须配置为：

```text
http://192.168.3.187/api/v1/login/feishu/callback
```

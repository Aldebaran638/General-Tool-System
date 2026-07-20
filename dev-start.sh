#!/bin/bash
# dev-start.sh — 一键开发环境启动脚本
#
# 功能：
#   1. 启动 docker compose 服务（若已运行则跳过）
#   2. 等待前端(10305)和后端(10304)就绪
#   3. 启动 Cloudflare 临时隧道（指向前端 localhost:10305）
#   4. 自动更新 .env 中的 DOMAIN / FRONTEND_HOST / BACKEND_CORS_ORIGINS
#   5. 重启后端使新 CORS 配置生效
#   6. 验证公网可达性
#   7. 打印企业微信后台应配置的内容
#
# 用法：
#   ./dev-start.sh
#
# 依赖：
#   - docker, docker compose
#   - cloudflared（https://github.com/cloudflare/cloudflared/releases）
#   - curl, python3

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── 颜色 ──────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }
header()  { echo -e "\n${BOLD}${CYAN}══════════════════════════════════════════${NC}"; echo -e "${BOLD}  $*${NC}"; echo -e "${BOLD}${CYAN}══════════════════════════════════════════${NC}"; }

# ── 前置检查 ──────────────────────────────────────────────────────────────────
header "前置检查"

if ! command -v docker &> /dev/null; then
    error "未找到 docker，请先安装 Docker Desktop 或 Docker Engine"
    exit 1
fi
success "docker 可用"

if ! command -v cloudflared &> /dev/null; then
    error "未找到 cloudflared"
    error "安装方法: https://github.com/cloudflare/cloudflared/releases"
    error "  Ubuntu/Debian: wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && sudo dpkg -i cloudflared-linux-amd64.deb"
    exit 1
fi
success "cloudflared 可用"

if [ ! -f ".env" ]; then
    error ".env 文件不存在，请先复制 .env.example 并填写必要配置"
    exit 1
fi
success ".env 文件存在"

# ── 检查端口冲突 ──────────────────────────────────────────────────────────────
header "检查端口冲突"

check_port() {
    local port=$1 name=$2
    # 检查是否有非本项目容器占用端口
    local occupant
    occupant=$(docker ps --format '{{.Names}}\t{{.Ports}}' 2>/dev/null | grep ":${port}->" | grep -v "project-management-board" | head -1)
    if [ -n "$occupant" ]; then
        local cname=$(echo "$occupant" | cut -f1)
        error "端口 ${port} 被其他容器占用: ${cname}"
        error "请先停止: docker stop ${cname}"
        return 1
    fi
    return 0
}

PORT_CONFLICT=0
check_port 10304 "后端" || PORT_CONFLICT=1
check_port 10305 "前端" || PORT_CONFLICT=1
check_port 10302 "数据库" || PORT_CONFLICT=1
check_port 10306 "ChartDB" || PORT_CONFLICT=1

if [ "$PORT_CONFLICT" -eq 1 ]; then
    error "存在端口冲突，请解决后重新运行"
    exit 1
fi
success "端口检查通过"

# ── 启动基础设施（db + adminer + mailcatcher）────────────────────────────────
header "启动基础设施"

DB_RUNNING=$(docker ps --filter "name=project-management-board-db" --filter "status=running" -q)

if [ -n "$DB_RUNNING" ]; then
    success "数据库容器已在运行，跳过启动"
else
    info "启动数据库和辅助服务..."
    docker compose up -d --force-recreate db adminer mailcatcher
    success "基础设施已启动"
fi

# ChartDB 是无状态的可视化工具，单独确保已启动（幂等，不强制重建）
docker compose up -d chartdb

# 确保 db 容器健康
if [ -z "$DB_RUNNING" ]; then
    info "等待数据库就绪..."
    for i in {1..30}; do
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' project-management-board-db-1 2>/dev/null || echo "unknown")
        if [ "$HEALTH" = "healthy" ]; then
            success "数据库已就绪"
            break
        fi
        echo -ne "  等待数据库健康检查... ${i}/30\r"
        sleep 2
    done
    echo ""
fi

# ── 启动 Cloudflare 隧道（在前端之前，获取 URL）──────────────────────────────
header "启动 Cloudflare 临时隧道"

# 清理旧 cloudflared 配置
CLOUDFLARE_DIR="$HOME/.cloudflared"
if [ -f "$CLOUDFLARE_DIR/config.yml" ]; then
    mv "$CLOUDFLARE_DIR/config.yml" "$CLOUDFLARE_DIR/config.yml.backup.$(date +%s)"
    info "已备份旧 cloudflared config.yml"
fi
for f in "$CLOUDFLARE_DIR"/*.json; do
    [ -e "$f" ] || continue
    mv "$f" "$CLOUDFLARE_DIR/$(basename "$f").backup.$(date +%s)"
    info "已备份旧凭证文件: $(basename "$f")"
done

# 隧道先指向前端端口（稍后前端启动后就能连上）
TUNNEL_PORT=10305
info "隧道目标: http://localhost:${TUNNEL_PORT} (Vite dev server)"

TMPFILE=$(mktemp)
cloudflared tunnel --url "http://localhost:${TUNNEL_PORT}" > "$TMPFILE" 2>&1 &
TUNNEL_PID=$!

# 捕获 Ctrl+C 清理
cleanup() {
    echo ""
    info "正在关闭隧道..."
    kill "$TUNNEL_PID" 2>/dev/null
    rm -f "$TMPFILE"
    echo "隧道已关闭"
    exit 0
}
trap cleanup SIGINT SIGTERM

# 等待隧道域名出现
URL=""
for i in {1..40}; do
    URL=$(grep -oP 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' "$TMPFILE" 2>/dev/null | head -1)
    if [ -n "$URL" ]; then
        break
    fi
    echo -ne "  等待隧道建立... ${i}/40\r"
    sleep 1
done
echo ""

if [ -z "$URL" ]; then
    error "未能获取隧道域名，cloudflared 输出："
    cat "$TMPFILE"
    kill "$TUNNEL_PID" 2>/dev/null
    rm -f "$TMPFILE"
    exit 1
fi

HOST="${URL#https://}"
success "隧道已建立: $URL"

# ── 更新配置文件（在启动应用容器之前）────────────────────────────────────────
header "更新本地配置"

# 替换或追加 .env 中的某个 KEY
update_env() {
    local file=$1 key=$2 value=$3
    if grep -q "^${key}=" "$file" 2>/dev/null; then
        sed -i "s|^${key}=.*|${key}=${value}|" "$file"
    else
        echo "${key}=${value}" >> "$file"
    fi
}

# BACKEND_CORS_ORIGINS：保留 localhost 条目，新增隧道域名
CORS_VALUE="${URL},http://localhost:10305,http://localhost:5173"

# 更新根 .env
update_env ".env" "DOMAIN"               "$HOST"
update_env ".env" "FRONTEND_HOST"        "$URL"
update_env ".env" "BACKEND_CORS_ORIGINS" "$CORS_VALUE"

# 更新 backend/.env（后端容器挂载了 ./backend 目录，会读取此文件）
update_env "backend/.env" "DOMAIN"               "$HOST"
update_env "backend/.env" "FRONTEND_HOST"        "$URL"
update_env "backend/.env" "BACKEND_CORS_ORIGINS" "$CORS_VALUE"

# 更新 frontend/.env（本地前端开发时使用；Docker 内 VITE_API_URL="" 走 proxy）
update_env "frontend/.env" "VITE_API_URL" "$URL"

info "已更新 .env / backend/.env / frontend/.env:"
info "  DOMAIN=$HOST"
info "  FRONTEND_HOST=$URL"
info "  BACKEND_CORS_ORIGINS=$CORS_VALUE"
info "  VITE_API_URL=$URL"

# ── 启动应用容器（.env 已就绪，Vite 不会触发 .env 变更重启）──────────────────
header "启动应用容器"

info "启动后端和前端（配置已写入，无需二次重启）..."
docker compose up -d --force-recreate backend frontend
success "应用容器已启动"

# ── 生成 ChartDB 导入结果（prestart 迁移完成后）──────────────────────────────
header "生成 ChartDB 导入结果"

if ./scripts/generate-chartdb-schema.sh; then
    success "ChartDB 导入结果已生成: docs/chartdb/schema.json"
else
    warn "ChartDB 导入结果生成失败；应用仍会继续启动"
fi

# ── 检查前端依赖完整性（volume 缓存可能导致 node_modules 过期）────────────────
header "检查前端依赖"

check_frontend_deps() {
    # 获取容器内 package.json 的依赖数量
    local container_deps
    container_deps=$(docker exec project-management-board-frontend-1 sh -c \
        'cat /app/frontend/package.json' 2>/dev/null | grep -c '"' || echo "0")

    # 检查几个关键依赖是否存在
    local missing=()
    local critical_deps=(
        "@radix-ui/react-alert-dialog"
        "@radix-ui/react-dialog"
        "@radix-ui/react-dropdown-menu"
        "@tanstack/react-router"
    )
    for dep in "${critical_deps[@]}"; do
        if ! docker exec project-management-board-frontend-1 sh -c \
            "test -d /app/frontend/node_modules/${dep}" 2>/dev/null; then
            missing+=("$dep")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        warn "前端缺少 ${#missing[@]} 个依赖: ${missing[*]}"
        info "正在安装缺失依赖..."
        docker exec project-management-board-frontend-1 sh -c \
            'cd /app/frontend && bun install --no-verify' 2>&1 | tail -3
        success "前端依赖已补全"

        # 依赖变化后需要重启 Vite，但这次 .env 没变，重启是安全的
        info "重启前端容器使依赖生效..."
        docker compose restart frontend
        sleep 3
        success "前端已重启"
    else
        success "前端依赖完整"
    fi
}

check_frontend_deps

# ── 等待服务就绪 ──────────────────────────────────────────────────────────────
header "等待服务就绪"

wait_for_port() {
    local port=$1
    local name=$2
    local max=60
    for i in $(seq 1 $max); do
        if curl -s --max-time 2 "http://localhost:${port}" > /dev/null 2>&1; then
            success "${name} (localhost:${port}) 已就绪"
            return 0
        fi
        echo -ne "  等待 ${name} (localhost:${port}) ... ${i}/${max}\r"
        sleep 2
    done
    echo ""
    warn "${name} 在 $((max * 2)) 秒内未响应，继续执行..."
}

wait_for_port 10305 "前端(Vite)"
wait_for_port 10304 "后端(FastAPI)"

# 后端健康检查（带 /api/v1 前缀）
for i in {1..30}; do
    HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:10304/api/v1/utils/health-check/ 2>/dev/null || echo "000")
    if [ "$HEALTH" = "200" ]; then
        success "后端 /health-check 返回 200"
        break
    fi
    echo -ne "  等待后端健康检查... ${i}/30\r"
    sleep 2
done
echo ""

# ── 最终验证：前端页面可访问 ───────────────────────────────────────────────────
info "验证前端页面..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://localhost:10305" 2>/dev/null || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    success "前端页面可访问 (HTTP 200)"
else
    warn "前端返回 HTTP $FRONTEND_STATUS，尝试重启前端..."
    docker compose restart frontend
    sleep 5
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://localhost:10305" 2>/dev/null || echo "000")
    if [ "$FRONTEND_STATUS" = "200" ]; then
        success "前端重启后可访问"
    else
        error "前端仍无法访问 (HTTP $FRONTEND_STATUS)，请检查日志: docker logs project-management-board-frontend-1"
    fi
fi

# ── 验证公网可达性 ─────────────────────────────────────────────────────────────
header "验证公网可达性"

info "等待 10 秒让 DNS 生效..."
sleep 10

TUNNEL_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "${URL}/api/v1/utils/health-check/" 2>/dev/null || echo "000")
if [ "$TUNNEL_HEALTH" = "200" ]; then
    success "公网访问验证通过: ${URL}/api/v1/utils/health-check/ → HTTP 200"
else
    warn "公网验证返回 HTTP $TUNNEL_HEALTH（隧道可能还未完全就绪，稍后手动测试）"
fi

# ── 企业微信后台配置指引 ──────────────────────────────────────────────────────
header "企业微信后台配置指引"

CALLBACK_URI="${URL}/api/auth/wecom/callback"
ENCODED_CALLBACK=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${CALLBACK_URI}', safe=''))" 2>/dev/null || echo "$CALLBACK_URI")

CORP_ID="wwe221b9e0dafa804a"
AGENT_ID="1000003"
APP_HOME_URL="${URL}/"
OAUTH_URL="https://open.weixin.qq.com/connect/oauth2/authorize?appid=${CORP_ID}&redirect_uri=${ENCODED_CALLBACK}&response_type=code&scope=snsapi_base&agentid=${AGENT_ID}&state=STATE#wechat_redirect"
VERIFY_FILENAME="${WECOM_VERIFY_FILENAME:-$(find backend/app . -maxdepth 1 -name 'WW_verify_*.txt' -printf '%f\n' 2>/dev/null | head -1)}"
if [ -z "$VERIFY_FILENAME" ]; then
    VERIFY_FILENAME="WW_verify_<企业微信后台下载的文件名>.txt"
fi

echo ""
echo -e "${BOLD}请在企业微信管理后台（work.weixin.qq.com/wework_admin）完成以下配置：${NC}"
echo ""
echo -e "${YELLOW}① 应用 → 选择目标应用 → 网页授权及JS-SDK → 可信域名${NC}"
echo "   填入（不加 https://）："
echo -e "   ${GREEN}${HOST}${NC}"
echo ""
echo -e "${YELLOW}② 应用 → 选择目标应用 → 企业微信授权登录 → 授权回调域${NC}"
echo "   填入（不加 https://，不加路径）："
echo -e "   ${GREEN}${HOST}${NC}"
echo ""
echo -e "${YELLOW}③ 应用 → 选择目标应用 → 应用主页${NC}"
echo "   设置为（员工在企业微信工作台点击应用进入的URL）："
echo -e "   ${GREEN}${APP_HOME_URL}${NC}"
echo ""
echo -e "${YELLOW}④ 域名校验文件（如已配置可跳过）${NC}"
echo "   验证地址已内置，访问可验证："
echo -e "   ${GREEN}${URL}/${VERIFY_FILENAME}${NC}"
echo ""
echo -e "${YELLOW}⑤ 手动测试 OAuth 登录流程${NC}"
echo "   在手机企业微信中打开以下链接，或让开发工具生成 QR 码："
echo -e "   ${GREEN}${OAUTH_URL}${NC}"
echo ""
echo -e "${YELLOW}⑥ PC 端调试登录（浏览器直接访问）${NC}"
echo -e "   ${GREEN}${URL}/api/auth/wecom/login${NC}"
echo ""
echo -e "${BOLD}本地服务地址：${NC}"
echo -e "  前端:    ${GREEN}http://localhost:10305${NC}"
echo -e "  后端:    ${GREEN}http://localhost:10304${NC}"
echo -e "  Swagger: ${GREEN}http://localhost:10304/api/v1/docs${NC}"
echo -e "  Adminer: ${GREEN}http://localhost:10303${NC}  (DB 管理)"
echo -e "  ChartDB: ${GREEN}http://localhost:10306${NC}  (导入 docs/chartdb/schema.json)"
echo -e "  邮件:    ${GREEN}http://localhost:10307${NC}   (MailCatcher)"
echo ""
echo -e "${BOLD}公网隧道地址：${NC}"
echo -e "  ${GREEN}${URL}${NC}"
echo ""
echo -e "${RED}注意：临时隧道每次重启域名都会变化，需重新配置企业微信后台！${NC}"
echo -e "${YELLOW}按 Ctrl+C 停止隧道${NC}"
echo ""

# ── 等待隧道结束 ──────────────────────────────────────────────────────────────
wait "$TUNNEL_PID"
rm -f "$TMPFILE"
echo ""
info "隧道已关闭"

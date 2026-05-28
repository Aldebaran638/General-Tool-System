#!/bin/bash
# dev-start.sh — 一键开发环境启动脚本
#
# 功能：
#   1. 启动 docker compose 服务（若已运行则跳过）
#   2. 等待前端(8000)和后端(8001)就绪
#   3. 启动 Cloudflare 临时隧道（指向前端 localhost:8000）
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
    occupant=$(docker ps --format '{{.Names}}\t{{.Ports}}' 2>/dev/null | grep ":${port}->" | grep -v "course-training-assessment" | head -1)
    if [ -n "$occupant" ]; then
        local cname=$(echo "$occupant" | cut -f1)
        error "端口 ${port} 被其他容器占用: ${cname}"
        error "请先停止: docker stop ${cname}"
        return 1
    fi
    return 0
}

PORT_CONFLICT=0
check_port 8001 "后端" || PORT_CONFLICT=1
check_port 8000 "前端" || PORT_CONFLICT=1
check_port 15432 "数据库" || PORT_CONFLICT=1

if [ "$PORT_CONFLICT" -eq 1 ]; then
    error "存在端口冲突，请解决后重新运行"
    exit 1
fi
success "端口检查通过"

# ── 启动 Docker Compose ───────────────────────────────────────────────────────
header "启动 Docker Compose 服务"

BACKEND_RUNNING=$(docker ps --filter "name=course-training-assessment-backend" --filter "status=running" -q)
DB_RUNNING=$(docker ps --filter "name=course-training-assessment-db" --filter "status=running" -q)

if [ -n "$BACKEND_RUNNING" ]; then
    success "后端容器已在运行，跳过启动"
else
    info "正在启动所有开发服务（db, backend, frontend, adminer, mailcatcher）..."
    docker compose up -d --force-recreate
    success "docker compose 已启动"
fi

# 确保 db 容器健康
if [ -z "$DB_RUNNING" ]; then
    info "等待数据库就绪..."
    for i in {1..30}; do
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' course-training-assessment-db-1 2>/dev/null || echo "unknown")
        if [ "$HEALTH" = "healthy" ]; then
            success "数据库已就绪"
            break
        fi
        echo -ne "  等待数据库健康检查... ${i}/30\r"
        sleep 2
    done
    echo ""
fi

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

wait_for_port 8000 "前端(Vite)"
wait_for_port 8001 "后端(FastAPI)"

# 后端健康检查（带 /api/v1 前缀）
for i in {1..30}; do
    HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/utils/health-check/ 2>/dev/null || echo "000")
    if [ "$HEALTH" = "200" ]; then
        success "后端 /health-check 返回 200"
        break
    fi
    echo -ne "  等待后端健康检查... ${i}/30\r"
    sleep 2
done
echo ""

# ── 清理旧 cloudflared 配置 ───────────────────────────────────────────────────
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

# ── 启动 Cloudflare 隧道 ──────────────────────────────────────────────────────
header "启动 Cloudflare 临时隧道"

# 隧道指向前端(Vite)，Vite proxy 负责转发 /api/* 到后端容器
TUNNEL_PORT=8000
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

# ── 更新配置文件 ──────────────────────────────────────────────────────────────
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
CORS_VALUE="${URL},http://localhost:8000,http://localhost:5173"

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

# ── 重建后端使新配置生效 ──────────────────────────────────────────────────────
header "重建后端（使新配置生效）"

# 必须 --force-recreate，restart 不会重新读取 .env 文件
docker compose up -d --force-recreate backend
info "等待后端重建..."
sleep 8

# 验证后端已恢复
for i in {1..20}; do
    HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/utils/health-check/ 2>/dev/null || echo "000")
    if [ "$HEALTH" = "200" ]; then
        success "后端重建完成"
        break
    fi
    sleep 2
done

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
echo -e "   ${GREEN}${URL}/WW_verify_HUz4rWBElVbwEoOX.txt${NC}"
echo ""
echo -e "${YELLOW}⑤ 手动测试 OAuth 登录流程${NC}"
echo "   在手机企业微信中打开以下链接，或让开发工具生成 QR 码："
echo -e "   ${GREEN}${OAUTH_URL}${NC}"
echo ""
echo -e "${YELLOW}⑥ PC 端调试登录（浏览器直接访问）${NC}"
echo -e "   ${GREEN}${URL}/api/auth/wecom/login${NC}"
echo ""
echo -e "${BOLD}本地服务地址：${NC}"
echo -e "  前端:    ${GREEN}http://localhost:8000${NC}"
echo -e "  后端:    ${GREEN}http://localhost:8001${NC}"
echo -e "  Swagger: ${GREEN}http://localhost:8001/api/v1/docs${NC}"
echo -e "  Adminer: ${GREEN}http://localhost:18081${NC}  (DB 管理)"
echo -e "  邮件:    ${GREEN}http://localhost:1180${NC}   (MailCatcher)"
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

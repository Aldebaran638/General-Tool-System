#!/bin/bash
# dev-tunnel.sh — 一键开发：启动容器 + Cloudflare 快速通道
#
# 用法：./dev-tunnel.sh
# 按 Ctrl+C 停止隧道，容器继续后台运行

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

# ── 检查 ──────────────────────────────────────────────────────────────────────
header "检查环境"

if ! command -v docker &> /dev/null; then
    error "未安装 docker"
    exit 1
fi
success "docker 已安装"

CLOUDFLARED="./bin/cloudflared"
if [ ! -x "$CLOUDFLARED" ]; then
    error "未找到本地 cloudflared: $CLOUDFLARED"
    error "请先运行: mkdir -p bin && curl -fsSL -o bin/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && chmod +x bin/cloudflared"
    exit 1
fi
success "本地 cloudflared 可用"

if [ ! -f ".env" ]; then
    error ".env 不存在，请先复制 .env.example 并配置"
    exit 1
fi
success ".env 存在"

# ── 启动容器 ──────────────────────────────────────────────────────────────────
header "启动 Docker 容器"

# 先创建外部网络（避免 compose 报错）
docker network inspect traefik-public &>/dev/null || docker network create traefik-public 2>/dev/null || true

# 如果容器已在运行，询问是否重启
RUNNING=$(docker ps --filter "name=project-management-board" --filter "status=running" -q | wc -l)
if [ "$RUNNING" -gt 0 ]; then
    warn "检测到已有 ${RUNNING} 个容器在运行"
    read -p "是否先停止再重新启动？(y/N): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        docker compose down
        info "已停止旧容器"
    fi
fi

# 启动基础设施 + 应用
info "启动所有服务..."
docker compose up -d --build db adminer mailcatcher chartdb backend frontend
success "容器已启动"

# 等待数据库健康
info "等待数据库就绪..."
for i in {1..30}; do
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' project-management-board-db-1 2>/dev/null || echo "unknown")
    if [ "$HEALTH" = "healthy" ]; then
        success "数据库已就绪"
        break
    fi
    echo -ne "  等待数据库... ${i}/30\r"
    sleep 2
done
echo ""

# 等待前后端端口
info "等待前后端服务就绪..."
for i in {1..60}; do
    FRONTEND_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:10116 2>/dev/null || echo "000")
    BACKEND_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:10105/api/v1/utils/health-check/ 2>/dev/null || echo "000")
    if [ "$FRONTEND_OK" = "200" ] && [ "$BACKEND_OK" = "200" ]; then
        success "前后端均已就绪"
        break
    fi
    echo -ne "  前端=${FRONTEND_OK} 后端=${BACKEND_OK} ... ${i}/60\r"
    sleep 2
done
echo ""

# ── 启动 Cloudflare 快速通道 ──────────────────────────────────────────────────
header "启动 Cloudflare 快速通道"

# 清理旧 cloudflared 配置（避免干扰 Quick Tunnel）
CLOUDFLARE_DIR="$HOME/.cloudflared"
if [ -f "$CLOUDFLARE_DIR/config.yml" ]; then
    mv "$CLOUDFLARE_DIR/config.yml" "$CLOUDFLARE_DIR/config.yml.backup.$(date +%s)"
    info "已备份旧 config.yml"
fi
for f in "$CLOUDFLARE_DIR"/*.json; do
    [ -e "$f" ] || continue
    mv "$f" "$CLOUDFLARE_DIR/$(basename "$f").backup.$(date +%s)"
    info "已备份旧凭证: $(basename "$f")"
done

# 启动 Quick Tunnel（指向前端 Vite dev server）
TUNNEL_PORT=10116
TMPFILE=$(mktemp)
info "正在建立隧道 → http://localhost:${TUNNEL_PORT} ..."

"$CLOUDFLARED" tunnel --url "http://localhost:${TUNNEL_PORT}" > "$TMPFILE" 2>&1 &
TUNNEL_PID=$!

# Ctrl+C 清理
cleanup() {
    echo ""
    info "正在关闭隧道..."
    kill "$TUNNEL_PID" 2>/dev/null || true
    rm -f "$TMPFILE"
    echo "隧道已关闭（容器仍在后台运行）"
    echo "如需停止容器: docker compose down"
    exit 0
}
trap cleanup SIGINT SIGTERM

# 等待获取域名
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
    error "隧道建立失败，日志如下:"
    cat "$TMPFILE"
    kill "$TUNNEL_PID" 2>/dev/null || true
    rm -f "$TMPFILE"
    exit 1
fi

HOST="${URL#https://}"
success "隧道已建立: $URL"

# ── 更新配置 ──────────────────────────────────────────────────────────────────
header "更新本地配置"

update_env() {
    local file=$1 key=$2 value=$3
    if [ ! -f "$file" ]; then touch "$file"; fi
    if grep -q "^${key}=" "$file" 2>/dev/null; then
        sed -i "s|^${key}=.*|${key}=${value}|" "$file"
    else
        echo "${key}=${value}" >> "$file"
    fi
}

CORS_VALUE="${URL},http://localhost:10116,http://localhost:5173"

update_env ".env"               "DOMAIN"               "$HOST"
update_env ".env"               "FRONTEND_HOST"        "$URL"
update_env ".env"               "BACKEND_CORS_ORIGINS" "$CORS_VALUE"
update_env "backend/.env"       "DOMAIN"               "$HOST"
update_env "backend/.env"       "FRONTEND_HOST"        "$URL"
update_env "backend/.env"       "BACKEND_CORS_ORIGINS" "$CORS_VALUE"
update_env "frontend/.env"      "VITE_API_URL"         "$URL"

info "已更新 .env / backend/.env / frontend/.env"

# 重启后端使新 CORS 生效
info "重启后端使 CORS 配置生效..."
docker compose restart backend
sleep 3

# ── 验证公网 ──────────────────────────────────────────────────────────────────
header "验证公网可达性"

info "等待 5 秒让 DNS 生效..."
sleep 5

TUNNEL_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "${URL}/api/v1/utils/health-check/" 2>/dev/null || echo "000")
if [ "$TUNNEL_HEALTH" = "200" ]; then
    success "公网验证通过: ${URL}/api/v1/utils/health-check/ → HTTP 200"
elif [ "$TUNNEL_HEALTH" = "000" ]; then
    warn "本地 curl 无法访问 trycloudflare.com（可能是本地 SSL/网络限制）"
    info "隧道大概率已正常工作，请用手机或其他网络测试: ${URL}"
else
    warn "公网验证返回 HTTP $TUNNEL_HEALTH（可能还在生效中，稍后手动测试）"
fi

# ── 输出总结 ──────────────────────────────────────────────────────────────────
header "🚀 开发环境已就绪"

echo ""
echo -e "${BOLD}本地访问地址：${NC}"
echo -e "  前端:    ${GREEN}http://localhost:10116${NC}"
echo -e "  后端:    ${GREEN}http://localhost:10105${NC}"
echo -e "  Swagger: ${GREEN}http://localhost:10105/api/v1/docs${NC}"
echo -e "  Adminer: ${GREEN}http://localhost:10104${NC}  (DB 管理)"
echo -e "  ChartDB: ${GREEN}http://localhost:10107${NC}"
echo -e "  邮件:    ${GREEN}http://localhost:10108${NC}   (MailCatcher)"
echo ""
echo -e "${BOLD}公网隧道地址：${NC}"
echo -e "  ${GREEN}${URL}${NC}"
echo ""
echo -e "${YELLOW}⚠️  注意：临时隧道每次重启域名都会变化！${NC}"
echo -e "${YELLOW}按 Ctrl+C 停止隧道（容器继续后台运行）${NC}"
echo ""

# 保持运行
wait "$TUNNEL_PID"
rm -f "$TMPFILE"
echo ""
info "隧道已关闭"

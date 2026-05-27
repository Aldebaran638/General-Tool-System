#!/bin/bash

set -e

# 切换到脚本所在目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  Cloudflare 临时隧道启动脚本"
echo "========================================"
echo ""

# 检查 cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "错误：未安装 cloudflared"
    echo "请先安装：https://github.com/cloudflare/cloudflared/releases"
    exit 1
fi

# 备份可能干扰临时隧道的旧配置
CLOUDFLARE_DIR="$HOME/.cloudflared"
if [ -f "$CLOUDFLARE_DIR/config.yml" ]; then
    BACKUP_NAME="config.yml.backup.$(date +%s)"
    mv "$CLOUDFLARE_DIR/config.yml" "$CLOUDFLARE_DIR/$BACKUP_NAME"
    echo "已备份旧配置：$CLOUDFLARE_DIR/$BACKUP_NAME"
fi
# 备份旧的 named tunnel 凭证文件（避免 cloudflared 自动加载）
for f in "$CLOUDFLARE_DIR"/*.json; do
    [ -e "$f" ] || continue
    BACKUP_NAME="$(basename "$f").backup.$(date +%s)"
    mv "$f" "$CLOUDFLARE_DIR/$BACKUP_NAME"
    echo "已备份旧凭证：$CLOUDFLARE_DIR/$BACKUP_NAME"
done

# 检查后端是否运行
if ! curl -s http://localhost:8000/api/v1/utils/health-check/ > /dev/null 2>&1; then
    echo "警告：localhost:8000 似乎没有响应"
    echo "请确保后端服务已启动（docker compose up backend 或 fastapi run）"
    echo ""
    read -p "仍要继续吗？(y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 启动 cloudflared，输出到临时文件
TMPFILE=$(mktemp)
echo "正在启动临时隧道（指向 localhost:8000）..."
cloudflared tunnel --url http://localhost:8000 > "$TMPFILE" 2>&1 &
PID=$!

# 等待并捕获域名
URL=""
for i in {1..30}; do
    URL=$(grep -oP 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' "$TMPFILE" | head -1)
    if [ -n "$URL" ]; then
        break
    fi
    sleep 1
    echo "  等待隧道建立... ($i/30)"
done

if [ -z "$URL" ]; then
    echo ""
    echo "错误：未能获取隧道域名"
    kill $PID 2>/dev/null
    rm "$TMPFILE"
    exit 1
fi

HOST="${URL#https://}"

echo ""
echo "隧道已启动：$URL"
echo ""

# 验证公网是否真正可达
echo "正在验证公网可达性..."
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${URL}/api/v1/utils/health-check/" 2>/dev/null || echo "000")
if [ "$HEALTH_CODE" != "200" ]; then
    echo ""
    echo "警告：公网验证返回 HTTP $HEALTH_CODE"
    echo "隧道域名可能尚未完全生效，或 ~/.cloudflared/ 下仍有旧配置干扰。"
    echo "建议："
    echo "  1. 等待 10-20 秒后手动 curl ${URL}/api/v1/utils/health-check/ 测试"
    echo "  2. 检查 ~/.cloudflared/ 目录并删除残留的旧 config.yml 或 *.json"
    echo ""
    read -p "仍要更新配置吗？(y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        kill $PID 2>/dev/null
        rm "$TMPFILE"
        exit 1
    fi
else
    echo "公网验证通过：HTTP 200"
fi

# ========== 修改项目配置 ==========

# 函数：替换或追加 env 变量
update_env() {
    local file=$1
    local key=$2
    local value=$3

    if [ ! -f "$file" ]; then
        touch "$file"
    fi

    if grep -q "^${key}=" "$file" 2>/dev/null; then
        sed -i "s|^${key}=.*|${key}=${value}|" "$file"
    else
        echo "${key}=${value}" >> "$file"
    fi
}

# 修改根目录 .env
update_env ".env" "DOMAIN" "$HOST"
update_env ".env" "FRONTEND_HOST" "$URL"
update_env ".env" "BACKEND_CORS_ORIGINS" "$URL"

# 创建/修改 frontend/.env
update_env "frontend/.env" "VITE_API_URL" "$URL"

echo "========== 配置已更新 =========="
echo "文件：.env"
echo "  DOMAIN=$HOST"
echo "  FRONTEND_HOST=$URL"
echo "  BACKEND_CORS_ORIGINS=$URL"
echo ""
echo "文件：frontend/.env"
echo "  VITE_API_URL=$URL"
echo ""

# ========== 输出企业微信配置 ==========

# URL encode 回调地址
REDIRECT_URI="${URL}/api/auth/wecom/callback"
ENCODED_URI=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$REDIRECT_URI', safe=''))" 2>/dev/null || echo "$REDIRECT_URI")

OAUTH_URL="https://open.weixin.qq.com/connect/oauth2/authorize?appid=wwe221b9e0dafa804a&redirect_uri=${ENCODED_URI}&response_type=code&scope=snsapi_base&agentid=1000003&state=STATE#wechat_redirect"

echo "========== 企业微信后台配置 =========="
echo ""
echo "1. 网页授权及 JS-SDK → 可信域名："
echo "   $HOST"
echo ""
echo "2. 应用主页（学员端入口）："
echo "   $OAUTH_URL"
echo ""
echo "3. 校验文件路由（稍后后端实现）："
echo "   GET /WWVerify_xxx.txt"
echo ""
echo "========== 重要提示 =========="
echo "此域名仅在 cloudflared 进程运行期间有效"
echo "进程退出后域名会改变，需要重新配置企业微信后台"
echo ""
echo "按 Ctrl+C 停止隧道"

# 等待进程
wait $PID

# 清理
rm -f "$TMPFILE"
echo ""
echo "隧道已关闭"

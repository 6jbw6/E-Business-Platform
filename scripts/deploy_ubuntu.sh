#!/usr/bin/env bash
# 公网 Ubuntu 服务器部署脚本（只用 uvicorn，不涉及 docker 与 nginx）
#
# 用法：
#   1) 把项目放到服务器目录，例如 /opt/ebusiness
#   2) 在项目根目录复制 .env.example 为 .env，填好 MySQL 与 JWT 配置
#   3) bash scripts/deploy_ubuntu.sh [端口]      # 端口默认 8000
#
# 脚本是幂等的，重复执行只会更新依赖并重启服务。
set -euo pipefail

PORT="${1:-8000}"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

echo "==> 项目目录：$APP_DIR"
echo "==> 监听端口：$PORT"

if ! command -v python3 >/dev/null 2>&1; then
    echo "缺少 python3，请先执行：sudo apt-get install -y python3 python3-venv python3-pip" >&2
    exit 1
fi

if [ ! -d .venv ]; then
    echo "==> 创建虚拟环境"
    python3 -m venv .venv
fi

echo "==> 安装依赖（使用清华镜像加速）"
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "==> 建库建表并播种演示数据"
.venv/bin/python -m scripts.init_db

echo "==> 停掉占用 $PORT 的旧进程"
pkill -f "uvicorn backend.app.main:app --port $PORT" 2>/dev/null || true
sleep 1

echo "==> 后台启动 uvicorn"
mkdir -p logs
nohup .venv/bin/uvicorn backend.app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers 1 \
    >> logs/uvicorn.log 2>&1 &

sleep 3
if curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null; then
    echo "==> 部署成功，健康检查通过"
    echo "    接口文档： http://<公网IP>:$PORT/docs"
    echo "    日志文件： $APP_DIR/logs/uvicorn.log"
else
    echo "==> 健康检查失败，请查看日志：tail -n 50 $APP_DIR/logs/uvicorn.log" >&2
    exit 1
fi

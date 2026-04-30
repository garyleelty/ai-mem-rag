#!/bin/bash

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

BACKEND_PORT="${PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-8080}"

echo "========================================"
echo "  ChromaDB 文档管理器 - 一键启动"
echo "========================================"
echo ""

# 检查 Python
echo "[1/4] 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3，请先安装 Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "      Python 版本: $PYTHON_VERSION"

# 检查依赖
echo ""
echo "[2/4] 检查后端依赖..."
cd "$BACKEND_DIR"

if ! python3 -c "import fastapi, chromadb, sentence_transformers, pypdf, docx" 2>/dev/null; then
    echo "      依赖未安装，正在安装..."
    pip install -r requirements.txt
else
    echo "      依赖已安装"
fi

# 启动后端
echo ""
echo "[3/4] 启动后端服务 (端口: $BACKEND_PORT)..."
nohup python3 main.py > "$PROJECT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "      后端 PID: $BACKEND_PID"

# 等待后端就绪
echo "      等待后端启动..."
for i in {1..30}; do
    if curl -s "http://localhost:$BACKEND_PORT/api/v1/collections" > /dev/null 2>&1; then
        echo "      后端已就绪"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "      警告: 后端启动超时，请检查 backend.log"
    fi
done

# 启动前端
echo ""
echo "[4/4] 启动前端服务 (端口: $FRONTEND_PORT)..."
cd "$FRONTEND_DIR"
nohup python3 -m http.server "$FRONTEND_PORT" > "$PROJECT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "      前端 PID: $FRONTEND_PID"

sleep 1

echo ""
echo "========================================"
echo "  启动完成!"
echo "========================================"
echo "  前端地址: http://localhost:$FRONTEND_PORT"
echo "  后端地址: http://localhost:$BACKEND_PORT"
echo "  后端日志: $PROJECT_DIR/backend.log"
echo "  前端日志: $PROJECT_DIR/frontend.log"
echo ""
echo "  停止命令:"
echo "    kill $BACKEND_PID $FRONTEND_PID"
echo "========================================"

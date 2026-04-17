#!/bin/bash
# PaddleOCR Linux 服务器启动脚本
# 运行方式: bash scripts/start_server_linux.sh

set -e

# 默认配置
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8765}"

echo "=========================================="
echo "PaddleOCR 服务器启动"
echo "=========================================="
echo "监听地址: $HOST:$PORT"
echo ""

# 使用 venv 中的 Python（HPI 需要 Python 3.12）
PYTHON_CMD=".venv/bin/python"

# 检查 PaddlePaddle 版本
$PYTHON_CMD -c "import paddle; print(f'PaddlePaddle: {paddle.__version__}')"
$PYTHON_CMD -c "import platform; print(f'Platform: {platform.system()}')"
echo ""

# 启动服务
echo "启动 OCR API 服务..."
exec $PYTHON_CMD -m src.server --host "$HOST" --port "$PORT"

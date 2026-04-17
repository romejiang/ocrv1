#!/bin/bash
# PaddleOCR Linux 环境安装脚本
# 运行方式: bash scripts/install_linux.sh

set -e

echo "=========================================="
echo "PaddleOCR Linux 环境安装脚本"
echo "=========================================="

# 检查是否为 Linux 系统
if [ "$(uname)" != "Linux" ]; then
    echo "错误: 此脚本仅适用于 Linux 系统"
    exit 1
fi

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "错误: uv 未安装"
    echo "请先安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "使用 uv 安装依赖..."

# 使用 Python 3.12
echo "创建 Python 3.12 虚拟环境..."
rm -rf .venv
uv venv --python 3.12

# 安装 pip（install_hpi_deps 需要）
echo "安装 pip..."
uv pip install pip

# 安装 PaddlePaddle 3.3.0 (CPU 版本)
echo "安装 PaddlePaddle 3.3.0..."
uv pip install paddlepaddle==3.3.0

# 安装 PaddleOCR
echo "安装 PaddleOCR..."
uv pip install paddleocr

# 安装其他依赖
echo "安装其他依赖..."
uv pip install -r requirements.txt

echo ""
echo "=========================================="
echo "安装完成!"
echo "=========================================="
echo ""
echo "验证安装:"
uv run python -c "import paddle; print(f'PaddlePaddle: {paddle.__version__}')"
uv run python -c "import paddleocr; print('PaddleOCR: OK')"
echo ""
echo "启动服务: bash scripts/start_server_linux.sh"

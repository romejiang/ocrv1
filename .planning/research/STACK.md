# Technology Stack

**Project:** 足彩彩票票面 OCR 批量扫描工具
**Researched:** 2026-04-16
**Confidence:** HIGH

## Recommended Stack

### Core OCR Engine

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| **PaddlePaddle (CPU)** | `3.2.0` | 深度学习框架 | 百度开源，3.2.0 为最新 stable 版本，CPU 推理稳定 |
| **PaddleOCR** | `pip install paddleocr` (latest) | OCR 工具库 | 官方维护，支持 80+ 语言，提供预训练模型，无需训练 |
| **OpenCV** | `4.x` (latest) | 图像预处理 | BGR→RGB 转换、灰度化、透视变换、去噪 |
| **Pillow** | `10.x` (latest) | 图像读写 | 通用图像处理，JPEG/PNG 支持 |
| **NumPy** | `1.x` (latest) | 数组操作 | 图像数据流转为 NumPy 数组 |

### CLI 安装命令

```bash
# 1. PaddlePaddle CPU 版本（必须先装）
python -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/

# 2. PaddleOCR
python -m pip install paddleocr

# 3. 高性能推理依赖（CPU 优化）
paddleocr install_hpi_deps cpu

# 4. 图像预处理
python -m pip install opencv-python-headless pillow numpy
```

### Python 版本要求

- **支持范围:** Python 3.8–3.12 (Linux x86-64)
- **推荐:** Python 3.10 或 3.11（macOS/Ubuntu 通吃，库兼容性最好）

### CPU 推理优化配置

```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_angle_cls=True,
    lang='ch',                    # 中文识别
    use_mp=True,                  # 多进程加速
    total_process_num=4,          # 进程数
    enable_mkldnn=True,           # MKL-DNN 加速（Intel CPU）
    cpu_threads=8,                # CPU 线程数
    precision='fp32',             # CPU 下 fp32 更稳定
    show_log=True                 # 输出日志
)
```

### 图像预处理流水线

| 步骤 | 工具 | 说明 |
|------|------|------|
| 读取 | Pillow (`Image.open`) | 统一读取入口，macOS 兼容性最好 |
| 格式转换 | OpenCV (`cv2.cvtColor`) | RGBA→RGB，BGR→RGB |
| 去噪 | OpenCV (`cv2.fastNlMeansDenoising`) | 印刷品噪点去除 |
| 二值化 | OpenCV (`cv2.threshold`) | 全局/自适应阈值 |
| 透视矫正 | OpenCV (`cv2.warpPerspective`) | 票据歪斜矫正 |
| 缩放 | OpenCV (`cv2.resize`) | 保持宽高比，归一化尺寸 |

### 项目结构依赖

```
requirements.txt:
  paddlepaddle==3.2.0      # CPU inference
  paddleocr>=3.0           # Latest stable
  opencv-python-headless>=4.10  # 无 GUI 依赖
  pillow>=10.0
  numpy>=1.24
  PyYAML>=6.0              # PaddleOCR 配置解析
  tqdm>=4.0                # 进度条
  requests>=2.31           # HTTP 接口（如需 MCP server）
```

### macOS 开发环境注意事项

- **使用 `opencv-python-headless`**，非 `opencv-python`（避免 Qt/GUI 依赖）
- **Apple Silicon (M1/M2/M3):** PaddlePaddle 3.2.0 支持 macOS ARM，但建议通过 Rosetta 2 运行 x86_64 版以获得更好兼容性
- **Homebrew 安装 OpenCV:** `brew install opencv` 可作为系统级补充，但 pip 版本优先

### Ubuntu 服务器环境注意事项

- **glibc 版本:** Ubuntu 20.04+，`glibc 2.31+`
- **MKL-DNN:** `paddleocr install_hpi_deps cpu` 会安装 MKL-DNN，Intel CPU 推理提升显著
- **内存:** 建议 ≥8GB RAM，单张 1080p 图片推理约 1-3GB 内存
- **容器支持:** 官方 Docker 镜像 `registry.cn-hangzhou.aliyuncs.com/paddlepaddle/paddle:3.2.0` 可用

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| OCR Engine | PaddleOCR | Tesseract | Tesseract 中文识别率低（~70% vs PaddleOCR ~90%+），需要大量后处理 |
| OCR Engine | PaddleOCR | EasyOCR | EasyOCR 推理慢（无 MKL-DNN 优化），中文支持弱于 PaddleOCR |
| Image Lib | opencv-python-headless | scikit-image | OpenCV 更广泛使用，与 PaddleOCR 集成更好 |
| Deployment | 原生 pip | Docker 容器 | macOS 开发环境直接装更方便；Docker 仅用于服务器一致性部署 |
| Parallel | multiprocessing | threading | PaddleOCR 推理为 CPU-bound，GIL 影响小，多进程更高效 |

## Anti-Patterns

- **不要** 用 `opencv-python`（带 GUI 依赖）在服务器环境 — 浪费资源
- **不要** 用 `paddlepaddle-gpu` 在纯 CPU 环境 — 安装失败或浪费
- **不要** 用 Python 2.x — PaddlePaddle 3.x 已不支持
- **不要** 在 macOS 上用 `paddleocr install_hpi_deps cpu` — 该命令仅适用 Linux x86-64

## Sources

- [PaddleOCR GitHub - Installation](https://github.com/paddlepaddle/paddleocr/blob/main/docs/version3.x/installation.en.md) — **HIGH confidence** (官方文档)
- [PaddleOCR - High Performance Inference](https://github.com/paddlepaddle/paddleocr/blob/main/docs/version3.x/deployment/high_performance_inference.en.md) — **HIGH confidence** (官方文档)
- [PaddleOCR - Inference Optimization Config](https://github.com/paddlepaddle/paddleocr/blob/main/docs/version3.x/pipeline_usage/PaddleOCR-VL.en.md) — **HIGH confidence** (官方文档)
- [PaddleOCR MCP Server](https://github.com/paddlepaddle/paddleocr/blob/main/docs/version3.x/deployment/mcp_server.en.md) — **HIGH confidence** (官方文档)

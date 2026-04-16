<!-- GSD:project-start source:PROJECT.md -->
## Project

**足彩彩票票面扫描工具**

批量扫描足彩彩票票面，使用 PaddleOCR 识别票面信息（投注内容、期号、金额等），支持 macOS 本地开发和 Ubuntu 服务器部署。

**Core Value:** 快速、准确地将足彩彩票票面转化为结构化数据，替代人工录入。

### Constraints

- **Tech Stack**: Python 3.x + PaddleOCR (CPU) — 跨平台兼容
- **Deployment**: Ubuntu Linux 服务器，CPU 推理
- **Performance**: 单张图片处理 < 5 秒
- **Output**: JSON/CSV 结构化数据，便于后续处理
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core OCR Engine
| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| **PaddlePaddle (CPU)** | `3.3.0` | 深度学习框架 | 百度开源，3.3.0 为最新 stable 版本，支持 HPI 高性能推理 |
| **Python** | `3.13` | Python 版本 | PaddlePaddle 3.3.0 支持 Python 3.9-3.13，推荐 3.13 |
| **PaddleOCR** | `pip install paddleocr` (latest) | OCR 工具库 | 官方维护，支持 80+ 语言，提供预训练模型，无需训练 |
| **OpenCV** | `4.x` (latest) | 图像预处理 | BGR→RGB 转换、灰度化、透视变换、去噪 |
| **Pillow** | `10.x` (latest) | 图像读写 | 通用图像处理，JPEG/PNG 支持 |
| **NumPy** | `1.x` (latest) | 数组操作 | 图像数据流转为 NumPy 数组 |
### CLI 安装命令
# 1. PaddlePaddle CPU 版本（必须先装）
# 2. PaddleOCR
# 3. 高性能推理依赖（CPU 优化）
# 4. 图像预处理
### Python 版本要求
- **支持范围:** Python 3.8–3.12 (Linux x86-64)
- **推荐:** Python 3.10 或 3.11（macOS/Ubuntu 通吃，库兼容性最好）
### CPU 推理优化配置
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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

- **包管理**: 必须使用 `uv` 管理 Python 依赖，禁止使用 `pip` 或 `pip3`
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

# Phase 1: Foundation - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

单张彩票图片端到端 OCR 处理：图像预处理 → PaddleOCR 检测 → 识别 → 结构化输出。验证 CPU 推理性能 < 5 秒/张。

</domain>

<decisions>
## Implementation Decisions

### 技术栈
- **D-01:** PaddlePaddle 3.2.0 CPU 版本（非 GPU 版本）
- **D-02:** PaddleOCR latest（pip install paddleocr）
- **D-03:** opencv-python-headless 4.x（非 opencv-python，避免 GUI 依赖）
- **D-04:** Python 3.10 或 3.11

### CPU 推理配置
- **D-05:** enable_mkldnn=True — MKL-DNN 加速（Intel CPU）
- **D-06:** cpu_threads=8 — CPU 线程数
- **D-07:** use_mp=True, total_process_num=4 — 多进程加速
- **D-08:** precision='fp32' — CPU 下 fp32 更稳定

### 图像预处理流水线
- **D-09:** Pillow (Image.open) 读取图片 — macOS 兼容性最好
- **D-10:** OpenCV cvtColor 格式转换（RGBA→RGB, BGR→RGB）
- **D-11:** OpenCV fastNlMeansDenoising 去噪
- **D-12:** OpenCV threshold 二值化（全局/自适应阈值）
- **D-13:** OpenCV warpPerspective 透视矫正
- **D-14:** OpenCV resize 缩放（保持宽高比）

### 安装命令（macOS 本地）
- **D-15:** `python -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/`
- **D-16:** `python -m pip install paddleocr`
- **D-17:** `python -m pip install opencv-python-headless pillow numpy`
- **D-18:** 注意：不要在 macOS 上运行 `paddleocr install_hpi_deps cpu`（该命令仅适用 Linux）

### 安装命令（Ubuntu 服务器）
- **D-19:** 同上 + `paddleocr install_hpi_deps cpu`（安装 MKL-DNN）

### the agent's Discretion
- 预处理参数具体数值（阈值、去噪强度）— 需根据实际图片调整
- 单张处理的具体代码结构

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Stack
- `.planning/research/STACK.md` — 完整技术栈配置和安装命令
- `.planning/research/ARCHITECTURE.md` — PaddleOCR pipeline 架构

### Anti-Patterns
- `.planning/research/STACK.md` §Anti-Patterns — 明确不要使用的技术组合

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- 无已有代码（greenfield 项目）

### Established Patterns
- PaddleOCR 官方推荐 pipeline 架构：预处理 → 检测 → 识别 → 输出

### Integration Points
- 后续 Phase 2 批量处理将在此基础上扩展

</code_context>

<specifics>
## Specific Ideas

- 单张处理验证成功后，再扩展到批量处理
- 性能目标：< 5 秒/张

</specifics>

<deferred>
## Deferred Ideas

None — Phase 1 聚焦基础架构

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-04-16*

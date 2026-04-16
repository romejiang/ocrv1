# Phase 1: Foundation - Research

**Phase:** 1
**Goal:** 单张图片端到端 OCR 处理，预处理 → 识别 → 结构化输出
**Requirements:** ENV-01, ENV-02, ENV-03, ENV-04, OCR-01, OCR-02, OCR-03, OCR-04, OCR-05
**Generated:** 2026-04-16

---

## Research Questions

### Q1: 如何在 macOS 上正确安装 PaddlePaddle CPU 版本？

**Finding:**
- PaddlePaddle 3.2.0 支持 macOS ARM (Apple Silicon) 和 x86_64
- macOS 上不要运行 `paddleocr install_hpi_deps cpu`（仅适用 Linux）
- 推荐通过 Rosetta 2 运行 x86_64 版本以获得更好兼容性
- 安装顺序：先装 paddlepaddle，再装 paddleocr，最后装 opencv-python-headless

**Source:** `.planning/research/STACK.md` §macOS 开发环境注意事项

### Q2: PaddleOCR CPU 推理最优配置参数？

**Finding:**
```python
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='ch',
    use_mp=True,                  # 多进程加速
    total_process_num=4,           # 进程数
    enable_mkldnn=True,          # MKL-DNN 加速（Intel CPU）
    cpu_threads=8,               # CPU 线程数
    precision='fp32',             # CPU 下 fp32 更稳定
    show_log=True
)
```

**Source:** `.planning/research/STACK.md` §CPU 推理优化配置

### Q3: 图像预处理流水线的具体实现步骤？

**Finding:**
| 步骤 | 工具 | 代码 |
|------|------|------|
| 读取 | Pillow | `Image.open(img_path).convert('RGB')` |
| 格式转换 | OpenCV | `cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)` |
| 去噪 | OpenCV | `cv2.fastNlMeansDenoisingColored()` |
| 二值化 | OpenCV | `cv2.threshold灰度, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)` |
| 透视矫正 | OpenCV | `cv2.warpPerspective` (需要4点定位) |
| 缩放 | OpenCV | `cv2.resize` (保持宽高比) |

**Source:** `.planning/research/STACK.md` §图像预处理流水线, `.planning/research/ARCHITECTURE.md` §Core Pipeline Architecture

### Q4: PaddleOCR PP-OCRv5 Server 模型选择？

**Finding:**
- PP-OCRv5 Server 模型：准确率优先，适合票面识别
- 模型会在首次使用时自动下载（约 100MB）
- 验证命令：`python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(); print('Model loaded')"`

**Source:** `.planning/research/ARCHITECTURE.md` §Stage 2 & 3

### Q5: 单张处理 < 5 秒性能目标如何达成？

**Finding:**
- CPU 优化三要素：enable_mkldnn=True, cpu_threads=8, use_mp=True
- 预处理参数：检测 `det_limit_side_len=640`，识别 `rec_batch_num=6`
- 禁用不必要的预处理器：`use_doc_orientation_classify=False`, `use_doc_unwarping=False`
- 关键：预加载 OCR 实例，不要每次调用重新加载

**Source:** `.planning/research/ARCHITECTURE.md` §Performance Considerations, §Anti-Patterns

### Q6: 验证安装成功的标准流程？

**Finding:**
1. `python -c "import paddlepaddle; print(paddlepaddle.__version__)"` → 3.2.0
2. `python -c "from paddleocr import PaddleOCR; print('PaddleOCR OK')"` → 无报错
3. `python -c "import cv2; print(cv2.__version__)"` → 4.x
4. 运行测试脚本验证实际推理时间

**Source:** `.planning/research/STACK.md` §Anti-Patterns

---

## Validation Architecture

### How to Validate Each Requirement

| Requirement | Validation Method | Expected Result |
|-------------|-------------------|-----------------|
| ENV-01 | `python --version` | 3.10 or 3.11 |
| ENV-02 | `import paddlepaddle; print(paddlepaddle.__version__)` | 3.2.0 |
| ENV-03 | `from paddleocr import PaddleOCR; ocr = PaddleOCR()` | 无报错 |
| ENV-04 | Ubuntu 上运行相同代码 | 同 macOS 结果 |
| OCR-01 | 处理测试图片，检查输出结构 | 包含文字、位置、置信度 |
| OCR-02 | 传入倾斜/噪点图片，验证输出改善 | 预处理前后对比 |
| OCR-03 | `ocr = PaddleOCR()` 打印 model path | 含 server 模型 |
| OCR-04 | 检查代码中 enable_mkldnn=True | 配置正确 |
| OCR-05 | `time python process_single.py` | < 5 秒 |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Apple Silicon 兼容性 | Medium | High | 使用 Rosetta 2 或通过 Docker 运行 |
| 模型下载失败 | Low | High | 预先下载，验证 SHA256 |
| MKL-DNN 在非 Intel CPU 无效 | Low | Low | 自动降级，不报错 |

---

## Plans Needing This Research

- **01-01**: 开发环境配置 — 直接使用 STACK.md 安装命令
- **01-02**: 单张 OCR 流水线 — 使用 ARCHITECTURE.md Pipeline 模式
- **01-03**: CPU 推理优化 — 使用 ARCHITECTURE.md 性能参数

---

*Research complete: 2026-04-16*
*Status: READY FOR PLANNING*
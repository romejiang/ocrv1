# Project Research Summary

**Project:** 足彩彩票票面 OCR 批量扫描工具
**Domain:** 批量 OCR 处理工具 (Batch OCR Processing)
**Researched:** 2026-04-16
**Confidence:** HIGH

## Executive Summary

彩票票面 OCR 识别是一个垂直领域的批量图像处理产品，核心需求是从彩票图片中提取结构化投注信息（期号、投注内容、赔率、金额）。基于 PaddleOCR 3.x 的 PP-OCRv5 模型，技术路线已经成熟：使用 PaddlePaddle 3.2.0 + PaddleOCR CPU 版本，配合 OpenCV 图像预处理，在 8 核 CPU 上可达 100 张/分钟的处理速度。

推荐技术方案：**PaddleOCR CPU 版**（非 mobile）+ **Multiprocessing 批量处理** + **PP-OCRv5_server 模型**。关键技术风险是图像预处理质量——彩票票面图像质量参差不齐（反光、折叠、污渍），不做预处理会导致识别率大幅下降。Phase 1 必须包含完整的图像预处理流水线，后续所有功能都依赖其输出质量。

架构模式已验证：采用模块化流水线（preprocessing → detection → recognition → structured output），通过 multiprocessing Queue 分配任务，每个 Worker 独立加载 PaddleOCR 实例。批量处理必须使用 `ocr.predict(dir)` 而非循环调用。

## Key Findings

### Recommended Stack

PaddleOCR 体系已成为中文 OCR 的事实标准，百度维护，PP-OCRv5 在中文识别率上显著领先 Tesseract（~90%+ vs ~70%）。CPU 推理需配合 MKL-DNN 加速，启用后性能可提升 3-5 倍。

**Core technologies:**
- **PaddlePaddle 3.2.0 (CPU)**: 深度学习框架，官方 stable 版本，pip 安装
- **PaddleOCR (latest)**: OCR 工具库，支持 80+ 语言，默认下载 server 模型
- **OpenCV 4.x (opencv-python-headless)**: 图像预处理，BGR 转换、去噪、透视矫正
- **Pillow 10.x**: 图像读写，macOS 兼容性最好
- **NumPy 1.x**: 数组操作，图像数据流转
- **Python 3.10/3.11**: 推荐版本，macOS/Ubuntu 库兼容性最好

### Expected Features

**Must have (table stakes):**
- 批量图片导入（文件夹、ZIP 压缩包）
- 基础文字识别（OCR）— PaddleOCR 已解决
- JSON/CSV 导出
- 多格式图片支持（jpg, png, webp, bmp, tiff）
- 命令行/脚本接口
- 进度展示（处理张数/总张数，成功/失败统计）

**Should have (competitive):**
- 彩票版面自动解析（期号区、金额区、投注区定位）
- 投注内容语义理解（"主胜 1.85" → {选项:"胜", 赔率:1.85}）
- 赔率数值提取（结构化数值）
- 错误图片自动标记
- 断点续传（大批量处理）

**Defer (v2+):**
- 实时摄像头扫描（与批量核心价值矛盾）
- OCR 模型训练/微调（资源消耗大，预训练模型已够用）
- 彩票真伪验证（需联网数据库）
- 数据库存储（增加复杂度，与轻量导出冲突）
- PDF 内嵌图片 OCR

### Architecture Approach

PaddleOCR batch processing 采用模块化流水线架构，分为三个核心阶段：preprocessing → text detection → text recognition → structured output。CPU 批量处理推荐使用 Python multiprocessing + shared task queue 模式，每个 Worker 进程独立加载 OCR pipeline。

**Major components:**
1. **Batch Orchestrator** — 主进程：文件发现、任务分发、结果聚合
2. **Worker Process** — OCR pipeline 实例，按 batch 处理图片
3. **Result Parser** — 从 OCR 结果中提取彩票专属字段（期号、金额、投注内容）
4. **Output Exporter** — JSON/CSV 导出

### Critical Pitfalls

1. **图像预处理缺失** — 彩票票面质量参差不齐，不做预处理识别率极低。必须包含灰度化、对比度增强、去噪、二值化流程。
2. **选错模型（mobile vs server）** — server 模型准确率 0.8401，mobile 仅 0.8015。批量处理必须用 server 模型。
3. **batch_size=1 逐张处理** — 100 张图片处理时间可能是批量处理的 5-10 倍。必须用 `ocr.predict(dir)` 批量接口。
4. **未启用 MKL-DNN** — CPU 模式下不启用 MKL-DNN 加速，单张处理时间从 1 秒变成 5+ 秒。
5. **未处理旋转票据** — 启用 `use_angle_cls=True`，批量扫描无法保证图片方向。

## Implications for Roadmap

基于研究，建议采用 5 阶段交付结构。关键依赖：**Phase 2 依赖 Phase 1 的 OCR 输出格式，Phase 4 依赖 Phase 3 的解析结果**。

### Phase 1: 核心 OCR 流水线
**Rationale:** 所有后续功能依赖 OCR 输出质量，且图像预处理参数需用真实样本调优
**Delivers:** 单张图片端到端处理，预处理 → OCR → JSON 输出
**Avoids:** Pitfall 1（预处理缺失）、Pitfall 2（模型选择错误）、Pitfall 5（尺寸限制）、Pitfall 6（旋转处理）
**Uses:** PaddlePaddle 3.2.0 + PaddleOCR，PP-OCRv5_server 模型，OpenCV 预处理

### Phase 2: 批量处理架构
**Rationale:** 批量处理是核心价值，需尽早验证多进程模式和内存稳定性
**Delivers:** 多进程批量处理、文件夹/ZIP 导入、错误处理、进度展示
**Avoids:** Pitfall 3（逐张处理）、Pitfall 7（文件类型处理）、Pitfall 8（内存泄漏）
**Uses:** multiprocessing.Queue，batch_size=6-8，enable_mkldnn=True

### Phase 3: 彩票结构化解析
**Rationale:** 差异化核心，从 OCR 文字中提取期号、金额、投注内容、赔率
**Delivers:** 字段提取模块、每注独立解析、赔率数值化
**Addresses:** 彩票专属字段解析（FEATURES.md Table Stakes — 彩票专属）

### Phase 4: 输出与 CLI
**Rationale:** 用户最终交付物，JSON/CSV schema 需在 Phase 1 就设计好
**Delivers:** JSON/CSV 导出、CLI 接口、结果合并、断点续传
**Avoids:** Pitfall 11（输出格式不合理）

### Phase 5: 质量与稳定性
**Rationale:** 面向生产环境，需要参数调优和监控
**Delivers:** 阈值参数调优（box_thresh, thresh）、日志系统、监控指标
**Avoids:** Pitfall 9（阈值未调优）、Pitfall 10（错误处理缺失）

### Phase Ordering Rationale

- **Phase 1 → 2**: OCR 流水线是基础，批量处理在其上扩展
- **Phase 2 → 3**: 批量处理验证后，才能有效测试解析逻辑
- **Phase 3 → 4**: 解析模块完成，输出格式才能定义
- **Phase 4 → 5**: 端到端流程打通后，优化质量和稳定性

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3:** 彩票版面解析 — 无直接竞品参照，解析逻辑需基于领域知识设计，需要真实彩票样本验证

Phases with standard patterns (skip research-phase):
- **Phase 1:** PaddleOCR 官方文档完善，PP-OCRv5 pipeline 已验证
- **Phase 2:** multiprocessing 批量处理是成熟模式，官方有 parallel_inference 文档

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | 基于 PaddleOCR 官方文档，75.7k stars，文档完善 |
| Features | MEDIUM-HIGH | 基础功能已验证，彩票专属解析无直接竞品参照 |
| Architecture | HIGH | 官方 parallel_inference 文档验证，PP-StructureV3 pipeline 架构明确 |
| Pitfalls | MEDIUM-HIGH | 基于官方文档和常见问题，12 个 pitfalls 有明确预防方案 |

**Overall confidence:** HIGH

### Gaps to Address

- **彩票版面解析逻辑**: 无直接竞品参照，Phase 3 需用真实样本反复验证
- **图像预处理参数**: 灰度化阈值、对比度增强倍数等需用真实彩票样本调优
- **阈值参数 (box_thresh, thresh)**: 默认值基于通用文档，彩票场景需实测调整

## Sources

### Primary (HIGH confidence)
- [PaddleOCR GitHub](https://github.com/paddlepaddle/paddleocr) — 官方文档，75.7k stars
- [PaddleOCR Parallel Inference](https://github.com/paddlepaddle/paddleocr/blob/main/docs/version3.x/pipeline_usage/instructions/parallel_inference.en.md) — 批量处理模式
- [PaddleOCR High Performance Inference](https://github.com/paddlepaddle/paddleocr/blob/main/docs/version3.x/deployment/high_performance_inference.en.md) — CPU 优化配置

### Secondary (MEDIUM-HIGH confidence)
- [Umi-OCR](https://github.com/hiroi-sora/Umi-OCR) — 43.4k stars，开源批量 OCR 软件验证
- [PP-StructureV3 Pipeline Architecture](https://github.com/paddlepaddle/paddleocr/blob/main/docs/version3.x/pipeline_usage/PP-StructureV3.en.md) — 文档结构化解析

---

*Research completed: 2026-04-16*
*Ready for roadmap: yes*

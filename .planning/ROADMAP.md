# Roadmap: 足彩彩票票面扫描工具

## Overview

从批量彩票图片中识别票面信息（期号、投注内容、赔率、金额），导出结构化数据。Phase 1 建立 OCR 流水线，Phase 2 实现批量处理，Phase 3 解析彩票专属字段，Phase 4 完成导出和 CLI 接口。

## Phases

- [x] **Phase 1: Foundation** - OCR 流水线完整端到端
- [ ] **Phase 2: Batch Processing** - 多进程批量处理
- [ ] **Phase 3: Lottery Parsing** - 彩票结构化解析
- [ ] **Phase 4: Output & CLI** - JSON/CSV 导出与命令行接口

## Phase Details

### Phase 1: Foundation
**Goal**: 单张图片端到端 OCR 处理，预处理 → 识别 → 结构化输出
**Depends on**: Nothing (first phase)
**Requirements**: ENV-01, ENV-02, ENV-03, ENV-04, OCR-01, OCR-02, OCR-03, OCR-04, OCR-05
**Success Criteria** (what must be TRUE):
  1. 单张彩票图片传入后返回完整 OCR 结果（文字、位置、置信度）
  2. 图像预处理流水线正常工作（去噪、二值化、透视矫正）
  3. CPU 推理优化已启用（enable_mkldnn、cpu_threads）
  4. 单张处理时间 < 5 秒
  5. PaddleOCR PP-OCRv5 server 模型下载并验证成功
**Plans**: 3 plans

Plans:
- [x] 01-01: 开发环境配置（Python 3.10+, PaddlePaddle CPU, PaddleOCR）
- [x] 01-02: 单张 OCR 流水线实现（预处理 → 检测 → 识别 → 输出）
- [x] 01-03: CPU 推理优化与性能验证

### Phase 2: Batch Processing
**Goal**: 多进程批量处理图片，支持文件夹/ZIP 导入，容错处理
**Depends on**: Phase 1
**Requirements**: BATCH-01, BATCH-02, BATCH-03, BATCH-04, BATCH-05, BATCH-06
**Success Criteria** (what must be TRUE):
  1. 文件夹导入能处理目录内所有支持的图片格式（jpg, png, webp, bmp, tiff）
  2. ZIP 压缩包导入能提取并处理其中所有图片
  3. multiprocessing 多进程并发处理，启用 MKL-DNN 加速
  4. 进度展示显示已处理/总数量，支持成功/失败统计
  5. 错误图片自动标记并记录日志，不中断整批处理
  6. 单张图片崩溃不影响其他图片处理
**Plans**: 2 plans

Plans:
- [ ] 02-01: 批量导入（文件夹、ZIP）与多进程架构
- [ ] 02-02: 进度展示、错误处理与容错机制

### Phase 3: Lottery Parsing
**Goal**: 从 OCR 文字中提取彩票专属字段（期号、投注内容、赔率、金额）
**Depends on**: Phase 1
**Requirements**: LOT-01, LOT-02, LOT-03, LOT-04, LOT-05, LOT-06
**Success Criteria** (what must be TRUE):
  1. 期号识别与提取正确
  2. 投注时间识别与提取正确
  3. 投注金额识别与提取正确
  4. 投注内容（比赛、选项）解析正确
  5. 赔率数字识别与提取正确
  6. 单张票面多注投注能独立识别
**Plans**: 2 plans

Plans:
- [ ] 03-01: 基础字段提取（期号、时间、金额）
- [ ] 03-02: 投注内容与赔率解析、多注识别

### Phase 4: Output & CLI
**Goal**: JSON/CSV 结构化导出，CLI 命令行接口
**Depends on**: Phase 3
**Requirements**: OUT-01, OUT-02, OUT-03, OUT-04
**Success Criteria** (what must be TRUE):
  1. JSON 导出包含完整字段结构，格式合法
  2. CSV 导出表格格式正确，可被 Excel 正常打开
  3. CLI 命令 `ocr-scan` 能处理单张图片并输出结果
  4. 导出结果与原始图片文件名正确映射
**Plans**: 2 plans

Plans:
- [ ] 04-01: JSON/CSV 导出实现
- [ ] 04-02: CLI 命令行接口

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | Complete | 2026-04-16 |
| 2. Batch Processing | 0/2 | Ready to plan | - |
| 3. Lottery Parsing | 0/2 | Not started | - |
| 4. Output & CLI | 0/2 | Not started | - |

## Coverage

**v1 Requirements:** 25 total
- ENV-01, ENV-02, ENV-03, ENV-04 → Phase 1
- OCR-01, OCR-02, OCR-03, OCR-04, OCR-05 → Phase 1
- BATCH-01, BATCH-02, BATCH-03, BATCH-04, BATCH-05, BATCH-06 → Phase 2
- LOT-01, LOT-02, LOT-03, LOT-04, LOT-05, LOT-06 → Phase 3
- OUT-01, OUT-02, OUT-03, OUT-04 → Phase 4

**Mapped:** 25/25 ✓
**Unmapped:** 0 ✓
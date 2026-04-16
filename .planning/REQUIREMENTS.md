# Requirements: 足彩彩票票面扫描工具

**Defined:** 2026-04-16
**Core Value:** 快速、准确地将足彩彩票票面转化为结构化数据，替代人工录入

## v1 Requirements

### 环境配置

- [ ] **ENV-01**: Python 3.10+ 环境支持 macOS 本地开发
- [ ] **ENV-02**: PaddlePaddle 3.2.0 CPU 版本安装
- [ ] **ENV-03**: PaddleOCR 安装与验证
- [ ] **ENV-04**: Ubuntu 服务器部署验证

### 核心 OCR

- [ ] **OCR-01**: 单张图片 OCR 识别完整流程（预处理 → 检测 → 识别 → 输出）
- [ ] **OCR-02**: 图像预处理流水线（去噪、二值化、透视矫正）
- [ ] **OCR-03**: PaddleOCR Server 模型配置（准确率优先）
- [ ] **OCR-04**: CPU 推理优化（enable_mkldnn、cpu_threads、rec_batch_num）
- [ ] **OCR-05**: 单张处理 < 5 秒性能目标

### 批量处理

- [ ] **BATCH-01**: 文件夹批量导入图片
- [ ] **BATCH-02**: ZIP 压缩包批量导入
- [ ] **BATCH-03**: multiprocessing 多进程批量处理
- [ ] **BATCH-04**: 进度展示（已处理/总数）
- [ ] **BATCH-05**: 错误图片标记与日志记录
- [ ] **BATCH-06**: 单张崩溃不影响整批（容错处理）

### 彩票结构化解析

- [ ] **LOT-01**: 期号识别与提取
- [ ] **LOT-02**: 投注时间识别与提取
- [ ] **LOT-03**: 投注金额识别与提取
- [ ] **LOT-04**: 投注内容解析（比赛、选项）
- [ ] **LOT-05**: 赔率数字识别与提取
- [ ] **LOT-06**: 多注识别（单张票面多个投注）

### 输出与接口

- [ ] **OUT-01**: JSON 结构化数据导出
- [ ] **OUT-02**: CSV 表格数据导出
- [ ] **OUT-03**: CLI 命令行接口
- [ ] **OUT-04**: 处理结果与原始图片关联（文件名映射）

## v2 Requirements

### 增强功能

- **ENH-01**: 断点续传（处理中断后恢复）
- **ENH-02**: 图片质量评估与过滤
- **ENH-03**: 票面区域自动定位（版面分析）
- **ENH-04**: 批量处理参数调优（根据硬件配置）

## Out of Scope

| Feature | Reason |
|---------|--------|
| OCR 模型训练/微调 | 使用官方预训练模型 |
| 实时摄像头扫描 | 批量图片处理场景 |
| 彩票真伪验证 | 仅识别票面内容 |
| 数据库存储 | 导出文件即可集成 |
| Windows 支持 | macOS/Ubuntu only |
| 图形用户界面 | CLI 优先，轻量级部署 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENV-01 | Phase 1 | Pending |
| ENV-02 | Phase 1 | Pending |
| ENV-03 | Phase 1 | Pending |
| ENV-04 | Phase 1 | Pending |
| OCR-01 | Phase 1 | Pending |
| OCR-02 | Phase 1 | Pending |
| OCR-03 | Phase 1 | Pending |
| OCR-04 | Phase 1 | Pending |
| OCR-05 | Phase 1 | Pending |
| BATCH-01 | Phase 2 | Pending |
| BATCH-02 | Phase 2 | Pending |
| BATCH-03 | Phase 2 | Pending |
| BATCH-04 | Phase 2 | Pending |
| BATCH-05 | Phase 2 | Pending |
| BATCH-06 | Phase 2 | Pending |
| LOT-01 | Phase 3 | Pending |
| LOT-02 | Phase 3 | Pending |
| LOT-03 | Phase 3 | Pending |
| LOT-04 | Phase 3 | Pending |
| LOT-05 | Phase 3 | Pending |
| LOT-06 | Phase 3 | Pending |
| OUT-01 | Phase 4 | Pending |
| OUT-02 | Phase 4 | Pending |
| OUT-03 | Phase 4 | Pending |
| OUT-04 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-16*
*Last updated: 2026-04-16 after initial definition*

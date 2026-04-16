# 足彩彩票票面扫描工具

## What This Is

批量扫描足彩彩票票面，使用 PaddleOCR 识别票面信息（投注内容、期号、金额等），支持 macOS 本地开发和 Ubuntu 服务器部署。

## Core Value

快速、准确地将足彩彩票票面转化为结构化数据，替代人工录入。

## Requirements

### Validated

- ✓ PaddleOCR CPU 模式识别票面文字 — Phase 1
- ✓ 图像预处理流水线（去噪、二值化、透视矫正）— Phase 1
- ✓ CPU 推理优化（MKL-DNN, cpu_threads）— Phase 1
- ✓ macOS 本地开发环境配置 — Phase 1
- ✓ 批量导入彩票图片（文件夹、ZIP）— Phase 2
- ✓ 多进程批量处理 — Phase 2
- ✓ 期号、投注时间、金额提取 — Phase 3
- ✓ 投注内容（比赛、选项、赔率）解析 — Phase 3
- ✓ 多注识别 — Phase 3

### Active

- [ ] 导出结构化数据（JSON/CSV）
- [ ] Ubuntu 服务器部署支持

### Out of Scope

- [ ] OCR 模型训练/微调 — 使用官方预训练模型
- [ ] 实时摄像头扫描 — 批量图片处理
- [ ] 彩票真伪验证 — 仅识别票面内容
- [ ] 数据库存储 — 导出文件即可
- [ ] Windows 支持 — macOS/Ubuntu only

## Context

- **PaddleOCR**: 百度开源 OCR 库，支持多种语言和端侧部署
- **足彩彩票**: 中国体育彩票足球彩票，包含胜平负、比分等多种投注类型
- **CPU 优先**: 服务器环境有限，选择 CPU 推理
- **macOS 开发**: 本地测试方便，文件路径处理需兼容 Unix

## Constraints

- **Tech Stack**: Python 3.x + PaddleOCR (CPU) — 跨平台兼容
- **Deployment**: Ubuntu Linux 服务器，CPU 推理
- **Performance**: 单张图片处理 < 5 秒
- **Output**: JSON/CSV 结构化数据，便于后续处理

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| PaddleOCR 而非 Tesseract | 中文识别率高，预训练模型丰富 | ✓ Phase 1 完成 |
| CPU 推理 | 服务器无 GPU，降低成本 | ✓ MKL-DNN 启用，性能 1.02s/张 |
| 批量处理优先 | 替代人工录入，效率优先 | ✓ Phase 2 完成 |
| 文件导出而非数据库 | 轻量级集成，灵活对接 | Phase 4 待做 |
| PaddlePaddle 3.x 使用 'paddle' import | 3.x 版本 API 变更 | ✓ 已验证 |
| opencv-python-headless 替代 opencv-python | 服务器环境无 GUI 依赖 | ✓ 已验证 |
| PaddleOCR v3 API | 重大版本更新，API 变化 | ✓ 已适配 |
| 正则表达式解析彩票字段 | 票面格式固定，模式匹配高效 | ✓ Phase 3 完成 |
| 多注按比赛数量识别 | 每场比赛视为独立投注 | ✓ Phase 3 完成 |

---

*Last updated: 2026-04-16 after Phase 3*

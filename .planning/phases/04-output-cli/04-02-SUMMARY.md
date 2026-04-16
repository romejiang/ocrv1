# Summary 04-02: CLI Command Line Interface

**Phase:** 4 - Output & CLI
**Plan:** 04-02
**Status:** Complete ✓
**Completed:** 2026-04-16

## Deliverables

### 核心模块: `src/cli.py`

统一的 CLI 命令行接口，包含三个子命令。

### Entry Point

```bash
ocr-ticket [command] [options]
```

## Commands

### 1. `single` - 处理单张图片

```bash
ocr-ticket single <image> [-o OUTPUT] [--no-preprocess] [--no-mkldnn] [--threads N]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `image` | 图片路径 | (required) |
| `-o, --output` | 输出 JSON 路径 | stdout |
| `--no-preprocess` | 跳过预处理 | False |
| `--no-mkldnn` | 禁用 MKL-DNN | False |
| `--threads N` | CPU 线程数 | 8 |

### 2. `batch` - 批量处理

```bash
ocr-ticket batch <input> [-o OUTPUT_DIR] [--workers N] [--no-preprocess] [--no-progress] [--csv]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `input` | 图片文件夹或 ZIP 路径 | (required) |
| `-o, --output-dir` | 输出目录 | output |
| `--workers N` | 并行进程数 | CPU count - 1 |
| `--no-preprocess` | 跳过预处理 | False |
| `--no-progress` | 隐藏进度条 | False |
| `--csv` | 同时导出 CSV | False |
| `--log-dir` | 日志目录 | logs |
| `--error-dir` | 错误图片目录 | errors |

### 3. `export` - 导出已有结果

```bash
ocr-ticket export <input> [-o OUTPUT_DIR] [-f FORMAT] [--include-raw]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `input` | 批量处理结果 JSON 路径 | (required) |
| `-o, --output-dir` | 输出目录 | export |
| `-f, --format` | 导出格式 | both |
| `--include-raw` | 包含原始 OCR 数据 | False |

## Requirements Coverage

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| OUT-03: CLI 命令行接口 | ✓ | `src/cli.py` with subcommands |

## pyproject.toml Entry Point

```toml
[project.scripts]
ocr-ticket = "src.cli:main"
```

## Usage Examples

```bash
# 查看帮助
ocr-ticket --help

# 处理单张图片
ocr-ticket single ticket.jpg -o result.json

# 批量处理文件夹
ocr-ticket batch ./tickets/ -o output --csv

# 导出已有结果
ocr-ticket export results.json -f both
```

## Architecture

```
cli.py
├── create_parser()     # 创建 ArgumentParser
├── cmd_single()        # 单张处理
├── cmd_batch()         # 批量处理
├── cmd_export()        # 结果导出
└── main()              # 入口函数

Dependencies:
├── src/pipeline.py     # OCRPipeline
├── src/batch.py        # BatchProcessor
├── src/parser.py       # LotteryParser
└── src/exporter.py     # Exporter
```

## Transition

**Complete:** Phase 4 - Output & CLI

Phase 4 全部完成，所有 v1.0 需求已实现。

---
*Plan 04-02 complete: 2026-04-16*
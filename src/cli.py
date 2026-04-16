"""统一 CLI 接口 - 足彩彩票票面扫描工具"""

import os
import sys
import argparse
import warnings
import logging
from pathlib import Path
from typing import Optional

# 禁用所有 warnings
warnings.filterwarnings("ignore")

# 禁用 PaddleOCR 和相关库的日志输出
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
os.environ.setdefault("GLOG_v", "0")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

# 设置日志级别为 ERROR，抑制 WARNING 和 INFO
for logger_name in ["ppocr", "paddle", "paddleocr", "urllib3", "PIL", "cv2"]:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.ERROR)
    logger.disabled = True

from src.pipeline import OCRPipeline
from src.batch import BatchProcessor, BatchResult
from src.parser import LotteryParser
from src.exporter import Exporter


def cmd_single(args):
    pipeline = OCRPipeline(
        enable_mkldnn=not args.no_mkldnn,
        cpu_threads=args.threads,
    )

    result = pipeline.process(
        args.image,
        preprocess=not args.no_preprocess,
        save_preprocessed=args.save_preprocessed,
    )

    parser = LotteryParser()
    ticket = parser.parse(result)

    if args.output:
        Exporter().export_to_json(
            [Exporter().ocr_result_to_record(args.image, result, "success")],
            args.output,
        )
        print(f"结果已保存到: {args.output}")
    else:
        import json

        print(json.dumps(ticket.to_dict(), ensure_ascii=False, indent=2))


def cmd_batch(args):
    processor = BatchProcessor(
        max_workers=args.workers,
        log_dir=args.log_dir,
        error_mark_dir=args.error_dir,
    )

    print(f"开始处理: {args.input}")

    batch_result = processor.process(
        args.input,
        use_preprocess=not args.no_preprocess,
        show_progress=not args.no_progress,
    )

    exporter = Exporter()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "results.json"
    exporter.export_batch_result(
        batch_result,
        output_json=str(json_path),
        output_csv=None,
        include_raw=False,
    )

    if args.csv:
        csv_path = output_dir / "results.csv"
        exporter.export_batch_result(
            batch_result,
            output_json=None,
            output_csv=str(csv_path),
        )

    print(f"\n处理完成!")
    print(f"总计: {batch_result.total}")
    print(f"成功: {batch_result.success}")
    print(f"失败: {batch_result.failed}")
    print(f"JSON: {json_path}")
    if args.csv:
        print(f"CSV: {csv_path}")


def cmd_export(args):
    if not Path(args.input).exists():
        print(f"错误: 文件不存在 {args.input}")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        import json

        batch_data = json.load(f)

    exporter = Exporter()

    records = []
    for item in batch_data.get("results", []):
        record = exporter.ocr_result_to_record(
            item.get("path", ""),
            item.get("data", {}) if item.get("status") == "success" else {},
            item.get("status", "unknown"),
            item.get("error"),
        )
        records.append(record)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.format == "json" or args.format == "both":
        json_path = output_dir / "results.json"
        exporter.export_to_json(records, str(json_path), args.include_raw)
        print(f"JSON 已导出: {json_path}")

    if args.format == "csv" or args.format == "both":
        csv_path = output_dir / "results.csv"
        exporter.export_to_csv(records, str(csv_path))
        print(f"CSV 已导出: {csv_path}")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="足彩彩票票面扫描工具 - PaddleOCR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  uv run python -m src.cli single ./tickets/1.jpg -o result.json
  uv run python -m src.cli batch ./tickets/ -o results/ --csv

提示: 如需抑制 PaddleOCR 初始化日志，可添加 2>/dev/null:
  uv run python -m src.cli single ./tickets/1.jpg -o result.json 2>/dev/null
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    single_parser = subparsers.add_parser("single", help="处理单张图片")
    single_parser.add_argument("image", help="图片路径")
    single_parser.add_argument("-o", "--output", help="输出 JSON 路径")
    single_parser.add_argument(
        "--no-preprocess", action="store_true", help="跳过预处理"
    )
    single_parser.add_argument(
        "--no-mkldnn", action="store_true", help="禁用 MKL-DNN 加速"
    )
    single_parser.add_argument("--threads", type=int, default=8, help="CPU 线程数")
    single_parser.add_argument(
        "--save-preprocessed", action="store_true", help="保存预处理后的图片"
    )

    batch_parser = subparsers.add_parser("batch", help="批量处理图片")
    batch_parser.add_argument("input", help="图片文件夹或 ZIP 文件路径")
    batch_parser.add_argument("-o", "--output-dir", default="output", help="输出目录")
    batch_parser.add_argument("--workers", type=int, default=None, help="并行进程数")
    batch_parser.add_argument("--no-preprocess", action="store_true", help="跳过预处理")
    batch_parser.add_argument("--no-progress", action="store_true", help="隐藏进度条")
    batch_parser.add_argument("--csv", action="store_true", help="同时导出 CSV")
    batch_parser.add_argument("--log-dir", default="logs", help="日志目录")
    batch_parser.add_argument("--error-dir", default="errors", help="错误图片目录")

    export_parser = subparsers.add_parser("export", help="导出已有结果")
    export_parser.add_argument("input", help="批量处理结果 JSON 文件路径")
    export_parser.add_argument("-o", "--output-dir", default="export", help="输出目录")
    export_parser.add_argument(
        "-f",
        "--format",
        choices=["json", "csv", "both"],
        default="both",
        help="导出格式",
    )
    export_parser.add_argument(
        "--include-raw", action="store_true", help="JSON 中包含原始 OCR 数据"
    )

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "single":
        cmd_single(args)
    elif args.command == "batch":
        cmd_batch(args)
    elif args.command == "export":
        cmd_export(args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""性能基准测试脚本"""

import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pipeline import OCRPipeline


def benchmark(image_path: str, runs: int = 5) -> dict:
    """对单张图片进行多次推理并统计性能

    Args:
        image_path: 测试图片路径
        runs: 运行次数

    Returns:
        包含平均时间、最大时间、最小时间的字典
    """
    pipeline = OCRPipeline()

    times = []
    for i in range(runs):
        start = time.perf_counter()
        result = pipeline.process(image_path, preprocess=True)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i + 1}: {elapsed:.3f}s")

    return {
        "avg": sum(times) / len(times),
        "min": min(times),
        "max": max(times),
        "all": times,
    }


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="OCR 性能基准测试")
    parser.add_argument("image_path", help="测试图片路径")
    parser.add_argument("-n", "--runs", type=int, default=5, help="运行次数")
    parser.add_argument("--target", type=float, default=5.0, help="目标时间（秒）")
    args = parser.parse_args()

    print(f"开始性能测试: {args.image_path}")
    print(f"目标时间: < {args.target}s")
    print(f"运行次数: {args.runs}\n")

    stats = benchmark(args.image_path, args.runs)

    print(f"\n性能统计:")
    print(f"  平均: {stats['avg']:.3f}s")
    print(f"  最快: {stats['min']:.3f}s")
    print(f"  最慢: {stats['max']:.3f}s")

    if stats["avg"] < args.target:
        print(f"\n✓ 性能达标！平均时间 {stats['avg']:.3f}s < {args.target}s")
        return 0
    else:
        print(f"\n✗ 性能未达标！平均时间 {stats['avg']:.3f}s >= {args.target}s")
        return 1


if __name__ == "__main__":
    sys.exit(main())

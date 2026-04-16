#!/usr/bin/env python3
"""预下载并验证 PaddleOCR 模型"""

from paddleocr import PaddleOCR
from pathlib import Path
import sys


def download_and_verify():
    """下载并验证 PP-OCRv5 Server 模型"""
    print("正在初始化 PaddleOCR（首次会下载模型，约 100MB）...")
    print("这可能需要几分钟时间，请耐心等待...\n")

    try:
        ocr = PaddleOCR(
            use_angle_cls=True,
            lang="ch",
            enable_mkldnn=True,
            cpu_threads=8,
        )
        print("\n✓ PaddleOCR 初始化成功")
        print(f"  模型路径: {getattr(ocr, 'model_path', 'default')}")

        det_model = getattr(ocr, "det_model", None)
        rec_model = getattr(ocr, "rec_model", None)
        cls_model = getattr(ocr, "cls_model", None)

        print(f"\n✓ 检测模型: {'已加载' if det_model else '未单独加载'}")
        print(f"✓ 识别模型: {'已加载' if rec_model else '未单独加载'}")
        print(f"✓ 方向分类: {'已加载' if cls_model else '未单独加载'}")

        return True

    except Exception as e:
        print(f"\n✗ PaddleOCR 初始化失败: {e}")
        return False


if __name__ == "__main__":
    success = download_and_verify()
    sys.exit(0 if success else 1)

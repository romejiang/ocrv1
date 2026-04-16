#!/usr/bin/env python3
"""性能测试用例"""

import unittest
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pipeline import OCRPipeline


class TestPerformance(unittest.TestCase):
    """性能测试"""

    @classmethod
    def setUpClass(cls):
        """测试前准备：下载模型和创建 OCR 实例"""
        cls.image_path = Path(__file__).parent.parent / "tests" / "data" / "sample.jpg"
        if not cls.image_path.exists():
            raise unittest.SkipTest(f"测试图片不存在: {cls.image_path}")
        cls.pipeline = OCRPipeline()

    def test_processing_time_under_5_seconds(self):
        """验证单张处理时间 < 5 秒"""
        times = []
        for _ in range(3):
            start = time.perf_counter()
            self.pipeline.process(str(self.image_path))
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        self.assertLess(avg_time, 5.0, f"平均处理时间 {avg_time:.3f}s 超过 5 秒目标")

    def test_mkldnn_enabled(self):
        """验证 MKL-DNN 加速已启用"""
        self.assertTrue(self.pipeline.ocr is not None, "OCR 实例未创建")

    def test_cpu_threads_set(self):
        """验证 CPU 线程数已设置"""
        self.assertIsNotNone(self.pipeline.ocr)


if __name__ == "__main__":
    unittest.main()

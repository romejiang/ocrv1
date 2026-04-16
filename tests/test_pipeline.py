#!/usr/bin/env python3
"""OCR Pipeline Tests"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import OCRPipeline
from src.preprocessing import (
    load_image,
    convert_to_grayscale,
    denoise,
    binarize,
    correct_perspective,
    resize_keep_aspect,
    preprocess_pipeline,
)


class TestPreprocessing(unittest.TestCase):
    """图像预处理测试"""

    def test_load_image_missing_file(self):
        """验证 load_image 处理不存在的文件"""
        with self.assertRaises(FileNotFoundError):
            load_image("nonexistent_image.jpg")

    def test_convert_to_grayscale(self):
        """验证灰度转换"""
        import numpy as np

        rgb_img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        gray = convert_to_grayscale(rgb_img)
        self.assertEqual(gray.shape, (100, 100))

    def test_denoise(self):
        """验证去噪函数"""
        import numpy as np

        img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        denoised = denoise(img)
        self.assertEqual(denoised.shape, img.shape)

    def test_resize_keep_aspect_small(self):
        """验证小于目标尺寸的图片不缩放"""
        import numpy as np

        img = np.ones((100, 100, 3), dtype=np.uint8)
        resized = resize_keep_aspect(img, target_size=1280)
        self.assertEqual(resized.shape, img.shape)

    def test_resize_keep_aspect_large(self):
        """验证大于目标尺寸的图片等比缩放"""
        import numpy as np

        img = np.ones((2000, 3000, 3), dtype=np.uint8)
        resized = resize_keep_aspect(img, target_size=1280)
        self.assertLessEqual(max(resized.shape[:2]), 1280)


class TestOCRPipeline(unittest.TestCase):
    """OCR Pipeline 测试"""

    def test_pipeline_init(self):
        """验证 OCRPipeline 初始化"""
        pipeline = OCRPipeline()
        self.assertIsNotNone(pipeline.ocr)

    def test_pipeline_init_mkldnn(self):
        """验证 OCRPipeline 启用 MKL-DNN"""
        pipeline = OCRPipeline(enable_mkldnn=True, cpu_threads=8)
        self.assertIsNotNone(pipeline.ocr)

    def test_parse_result_empty(self):
        """验证空结果解析"""
        pipeline = OCRPipeline()
        result = pipeline._parse_result([])
        self.assertEqual(result["words"], [])
        self.assertEqual(result["full_text"], "")
        self.assertEqual(result["regions"], [])

    def test_parse_result_none(self):
        """验证 None 结果解析"""
        pipeline = OCRPipeline()
        result = pipeline._parse_result(None)
        self.assertEqual(result["words"], [])
        self.assertEqual(result["full_text"], "")


if __name__ == "__main__":
    unittest.main()

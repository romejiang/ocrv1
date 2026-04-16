#!/usr/bin/env python3
"""Batch Processing Tests"""

import unittest
import sys
import tempfile
import shutil
import zipfile
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.batch import (
    BatchProcessor,
    BatchResult,
    SUPPORTED_FORMATS,
)


class TestBatchResult(unittest.TestCase):
    """BatchResult 数据类测试"""

    def test_batch_result_init(self):
        result = BatchResult(total=10)
        self.assertEqual(result.total, 10)
        self.assertEqual(result.success, 0)
        self.assertEqual(result.failed, 0)

    def test_add_success(self):
        result = BatchResult(total=2)
        result.add_success("/path/to/image.jpg", {"text": "test"})
        self.assertEqual(result.success, 1)
        self.assertEqual(result.failed, 0)
        self.assertEqual(len(result.results), 1)

    def test_add_failure(self):
        result = BatchResult(total=2)
        result.add_failure("/path/to/image.jpg", "error message")
        self.assertEqual(result.success, 0)
        self.assertEqual(result.failed, 1)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(len(result.errors), 1)


class TestSupportedFormats(unittest.TestCase):
    """支持的图片格式测试"""

    def test_supported_formats_contain_common(self):
        self.assertIn(".jpg", SUPPORTED_FORMATS)
        self.assertIn(".jpeg", SUPPORTED_FORMATS)
        self.assertIn(".png", SUPPORTED_FORMATS)
        self.assertIn(".bmp", SUPPORTED_FORMATS)
        self.assertIn(".tiff", SUPPORTED_FORMATS)
        self.assertIn(".tif", SUPPORTED_FORMATS)
        self.assertIn(".webp", SUPPORTED_FORMATS)


class TestBatchProcessor(unittest.TestCase):
    """BatchProcessor 测试"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.processor = BatchProcessor(
            max_workers=2,
            log_dir=tempfile.mkdtemp(),
            error_mark_dir=tempfile.mkdtemp(),
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_is_image(self):
        self.assertTrue(self.processor._is_image(Path("test.jpg")))
        self.assertTrue(self.processor._is_image(Path("test.PNG")))
        self.assertTrue(self.processor._is_image(Path("test.jpeg")))
        self.assertFalse(self.processor._is_image(Path("test.txt")))
        self.assertFalse(self.processor._is_image(Path("test.pdf")))

    def test_collect_images_from_folder_empty(self):
        folder = Path(self.temp_dir) / "empty"
        folder.mkdir()
        images = self.processor._collect_images_from_folder(str(folder))
        self.assertEqual(len(images), 0)

    def test_collect_images_from_folder_with_images(self):
        folder = Path(self.temp_dir) / "images"
        folder.mkdir()

        (folder / "image1.jpg").touch()
        (folder / "image2.png").touch()
        (folder / "document.txt").touch()

        images = self.processor._collect_images_from_folder(str(folder))
        self.assertEqual(len(images), 2)

    def test_collect_images_from_folder_nested(self):
        folder = Path(self.temp_dir) / "nested"
        folder.mkdir()
        subfolder = folder / "sub"
        subfolder.mkdir()

        (folder / "image1.jpg").touch()
        (subfolder / "image2.png").touch()

        images = self.processor._collect_images_from_folder(str(folder))
        self.assertEqual(len(images), 2)

    def test_collect_images_from_folder_nonexistent(self):
        with self.assertRaises(ValueError):
            self.processor._collect_images_from_folder("/nonexistent/folder")

    def test_collect_images_from_zip(self):
        zip_path = Path(self.temp_dir) / "test.zip"
        extract_dir = Path(self.temp_dir) / "extracted"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("image1.jpg", b"fake image data")
            zf.writestr("image2.png", b"fake image data")
            zf.writestr("document.txt", b"not an image")

        images, extracted = self.processor._collect_images_from_zip(
            str(zip_path), str(extract_dir)
        )
        self.assertEqual(len(images), 2)

    def test_collect_images_from_zip_nonexistent(self):
        with self.assertRaises(ValueError):
            self.processor._collect_images_from_zip("/nonexistent.zip")

    def test_collect_inputs_folder(self):
        folder = Path(self.temp_dir) / "input_folder"
        folder.mkdir()
        (folder / "test.jpg").touch()

        images = self.processor.collect_inputs(str(folder))
        self.assertEqual(len(images), 1)

    def test_collect_inputs_zip(self):
        zip_path = Path(self.temp_dir) / "input.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.jpg", b"fake")

        images = self.processor.collect_inputs(str(zip_path))
        self.assertEqual(len(images), 1)

    def test_collect_inputs_single_image(self):
        image_path = Path(self.temp_dir) / "single.jpg"
        image_path.touch()

        images = self.processor.collect_inputs(str(image_path))
        self.assertEqual(len(images), 1)

    def test_collect_inputs_invalid_format(self):
        file_path = Path(self.temp_dir) / "invalid.pdf"
        file_path.touch()

        with self.assertRaises(ValueError):
            self.processor.collect_inputs(str(file_path))

    def test_collect_inputs_nonexistent(self):
        with self.assertRaises(ValueError):
            self.processor.collect_inputs("/nonexistent/path")

    def test_process_empty_input(self):
        empty_folder = Path(self.temp_dir) / "empty"
        empty_folder.mkdir()

        result = self.processor.process(str(empty_folder), show_progress=False)
        self.assertEqual(result.total, 0)
        self.assertEqual(result.success, 0)
        self.assertEqual(result.failed, 0)


class TestBatchProcessorProcessBatch(unittest.TestCase):
    """process_batch 集成测试"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.processor = BatchProcessor(
            max_workers=2,
            log_dir=tempfile.mkdtemp(),
            error_mark_dir=tempfile.mkdtemp(),
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_process_batch_nonexistent_images(self):
        nonexistent_paths = [
            Path("/nonexistent/image1.jpg"),
            Path("/nonexistent/image2.jpg"),
        ]
        result = self.processor.process_batch(nonexistent_paths, show_progress=False)

        self.assertEqual(result.total, 2)
        self.assertEqual(result.success, 0)
        self.assertEqual(result.failed, 2)


if __name__ == "__main__":
    unittest.main()

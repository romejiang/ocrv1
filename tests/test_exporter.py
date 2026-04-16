#!/usr/bin/env python3
"""数据导出模块测试 - OUT-01, OUT-02, OUT-04"""

import unittest
import sys
import tempfile
import json
import csv
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.exporter import Exporter, ExportRecord
from src.parser import LotteryParser


class TestExportRecord(unittest.TestCase):
    """ExportRecord 数据类测试"""

    def test_to_dict(self):
        record = ExportRecord(
            source_file="/path/to/image.jpg",
            source_filename="image.jpg",
            issue_number="25042",
            bet_time="2026-04-16",
            total_amount=66.0,
            bets_count=2,
            bet_details="阿根廷 vs 巴西 胜@1.85; 中国 vs 日本 胜@2.10",
            status="success",
        )

        result = record.to_dict()

        self.assertEqual(result["source_file"], "/path/to/image.jpg")
        self.assertEqual(result["source_filename"], "image.jpg")
        self.assertEqual(result["issue_number"], "25042")
        self.assertEqual(result["bet_time"], "2026-04-16")
        self.assertEqual(result["total_amount"], 66.0)
        self.assertEqual(result["bets_count"], 2)
        self.assertEqual(result["status"], "success")
        self.assertIsNone(result["error"])


class TestExporterOCRResultToRecord(unittest.TestCase):
    """ocr_result_to_record 测试"""

    def setUp(self):
        self.exporter = Exporter()

    def test_success_case(self):
        ocr_result = {
            "full_text": """
            第 25042 期
            2026-04-16
            投注金额：￥66
            阿根廷 vs 巴西
              胜:1.85  平:2.10  负:3.50
            """
        }

        record = self.exporter.ocr_result_to_record(
            "/path/to/ticket.jpg", ocr_result, "success"
        )

        self.assertEqual(record.source_file, "/path/to/ticket.jpg")
        self.assertEqual(record.source_filename, "ticket.jpg")
        self.assertEqual(record.issue_number, "25042")
        self.assertEqual(record.bet_time, "2026-04-16")
        self.assertEqual(record.total_amount, 66.0)
        self.assertGreater(record.bets_count, 0)
        self.assertEqual(record.status, "success")

    def test_failed_case(self):
        record = self.exporter.ocr_result_to_record(
            "/path/to/failed.jpg", {}, "failed", "OCR processing error"
        )

        self.assertEqual(record.source_file, "/path/to/failed.jpg")
        self.assertEqual(record.source_filename, "failed.jpg")
        self.assertIsNone(record.issue_number)
        self.assertEqual(record.status, "failed")
        self.assertEqual(record.error, "OCR processing error")
        self.assertEqual(record.bets_count, 0)


class TestExporterJSONExport(unittest.TestCase):
    """JSON 导出测试 (OUT-01, OUT-04)"""

    def setUp(self):
        self.exporter = Exporter()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_to_json(self):
        records = [
            ExportRecord(
                source_file="/path/to/image1.jpg",
                source_filename="image1.jpg",
                issue_number="25042",
                bet_time="2026-04-16",
                total_amount=66.0,
                bets_count=1,
                bet_details="阿根廷 vs 巴西 胜@1.85",
                status="success",
            ),
            ExportRecord(
                source_file="/path/to/image2.jpg",
                source_filename="image2.jpg",
                issue_number=None,
                bet_time=None,
                total_amount=None,
                bets_count=0,
                bet_details="",
                status="failed",
                error="Cannot read image",
            ),
        ]

        json_path = os.path.join(self.temp_dir, "results.json")
        self.exporter.export_to_json(records, json_path)

        self.assertTrue(os.path.exists(json_path))

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["total"], 2)
        self.assertEqual(data["success_count"], 1)
        self.assertEqual(data["failed_count"], 1)
        self.assertEqual(len(data["records"]), 2)

        self.assertEqual(data["records"][0]["source_filename"], "image1.jpg")
        self.assertEqual(data["records"][0]["issue_number"], "25042")
        self.assertEqual(data["records"][1]["source_filename"], "image2.jpg")
        self.assertEqual(data["records"][1]["status"], "failed")

    def test_json_includes_filename_mapping(self):
        records = [
            ExportRecord(
                source_file="/home/user/tickets/2026/image.jpg",
                source_filename="image.jpg",
                issue_number="25042",
                bet_time=None,
                total_amount=None,
                bets_count=0,
                bet_details="",
                status="success",
            ),
        ]

        json_path = os.path.join(self.temp_dir, "mapping_test.json")
        self.exporter.export_to_json(records, json_path)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(
            data["records"][0]["source_file"], "/home/user/tickets/2026/image.jpg"
        )
        self.assertEqual(data["records"][0]["source_filename"], "image.jpg")


class TestExporterCSVExport(unittest.TestCase):
    """CSV 导出测试 (OUT-02, OUT-04)"""

    def setUp(self):
        self.exporter = Exporter()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_to_csv(self):
        records = [
            ExportRecord(
                source_file="/path/to/image1.jpg",
                source_filename="image1.jpg",
                issue_number="25042",
                bet_time="2026-04-16",
                total_amount=66.0,
                bets_count=2,
                bet_details="阿根廷 vs 巴西 胜@1.85",
                status="success",
            ),
            ExportRecord(
                source_file="/path/to/image2.jpg",
                source_filename="image2.jpg",
                issue_number=None,
                bet_time=None,
                total_amount=None,
                bets_count=0,
                bet_details="",
                status="failed",
                error="Cannot read image",
            ),
        ]

        csv_path = os.path.join(self.temp_dir, "results.csv")
        self.exporter.export_to_csv(records, csv_path)

        self.assertTrue(os.path.exists(csv_path))

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 2)

        self.assertEqual(rows[0]["source_filename"], "image1.jpg")
        self.assertEqual(rows[0]["issue_number"], "25042")
        self.assertEqual(rows[0]["total_amount"], "66.0")
        self.assertEqual(rows[0]["status"], "success")

        self.assertEqual(rows[1]["source_filename"], "image2.jpg")
        self.assertEqual(rows[1]["status"], "failed")
        self.assertEqual(rows[1]["error"], "Cannot read image")

    def test_csv_includes_filename_mapping(self):
        records = [
            ExportRecord(
                source_file="/home/user/tickets/2026/image.jpg",
                source_filename="image.jpg",
                issue_number="25042",
                bet_time=None,
                total_amount=None,
                bets_count=0,
                bet_details="",
                status="success",
            ),
        ]

        csv_path = os.path.join(self.temp_dir, "mapping_test.csv")
        self.exporter.export_to_csv(records, csv_path)

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(rows[0]["source_file"], "/home/user/tickets/2026/image.jpg")
        self.assertEqual(rows[0]["source_filename"], "image.jpg")


class TestExporterBatchResultExport(unittest.TestCase):
    """export_batch_result 集成测试 (OUT-01, OUT-02, OUT-04)"""

    def setUp(self):
        self.exporter = Exporter()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_batch_result_json_only(self):
        from src.batch import BatchResult

        batch_result = BatchResult(total=2)
        batch_result.add_success(
            "/path/to/image1.jpg",
            {"full_text": "第 25042 期\n2026-04-16\n投注金额：￥66"},
        )
        batch_result.add_failure("/path/to/image2.jpg", "Read error")

        json_path = os.path.join(self.temp_dir, "results.json")
        output_paths = self.exporter.export_batch_result(
            batch_result,
            output_json=json_path,
            output_csv=None,
        )

        self.assertIn("json", output_paths)
        self.assertTrue(os.path.exists(json_path))

    def test_export_batch_result_csv_only(self):
        from src.batch import BatchResult

        batch_result = BatchResult(total=2)
        batch_result.add_success(
            "/path/to/image1.jpg",
            {"full_text": "第 25042 期\n2026-04-16\n投注金额：￥66"},
        )
        batch_result.add_failure("/path/to/image2.jpg", "Read error")

        csv_path = os.path.join(self.temp_dir, "results.csv")
        output_paths = self.exporter.export_batch_result(
            batch_result,
            output_json=None,
            output_csv=csv_path,
        )

        self.assertIn("csv", output_paths)
        self.assertTrue(os.path.exists(csv_path))

    def test_export_batch_result_both_formats(self):
        from src.batch import BatchResult

        batch_result = BatchResult(total=2)
        batch_result.add_success(
            "/path/to/image1.jpg",
            {"full_text": "第 25042 期\n2026-04-16\n投注金额：￥66"},
        )
        batch_result.add_failure("/path/to/image2.jpg", "Read error")

        json_path = os.path.join(self.temp_dir, "results.json")
        csv_path = os.path.join(self.temp_dir, "results.csv")
        output_paths = self.exporter.export_batch_result(
            batch_result,
            output_json=json_path,
            output_csv=csv_path,
        )

        self.assertIn("json", output_paths)
        self.assertIn("csv", output_paths)
        self.assertTrue(os.path.exists(json_path))
        self.assertTrue(os.path.exists(csv_path))


if __name__ == "__main__":
    unittest.main()

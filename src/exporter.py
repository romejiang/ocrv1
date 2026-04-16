"""数据导出模块 - JSON/CSV 结构化数据导出"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict

from src.parser import LotteryTicket, LotteryParser


@dataclass
class ExportRecord:
    source_file: str
    source_filename: str
    issue_number: Optional[str]
    bet_time: Optional[str]
    total_amount: Optional[float]
    bets_count: int
    bet_details: str
    status: str
    error: Optional[str] = None
    full_text: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "source_file": self.source_file,
            "source_filename": self.source_filename,
            "issue_number": self.issue_number,
            "bet_time": self.bet_time,
            "total_amount": self.total_amount,
            "bets_count": self.bets_count,
            "bet_details": self.bet_details,
            "status": self.status,
            "error": self.error,
            "full_text": self.full_text,
        }


class Exporter:
    def __init__(self, parser: Optional[LotteryParser] = None):
        self.parser = parser or LotteryParser()

    def ocr_result_to_record(
        self,
        image_path: str,
        ocr_result: Union[Dict, str],
        status: str = "success",
        error: Optional[str] = None,
    ) -> ExportRecord:
        source_file = str(image_path)
        source_filename = Path(image_path).name

        if status == "failed" or not isinstance(ocr_result, dict):
            return ExportRecord(
                source_file=source_file,
                source_filename=source_filename,
                issue_number=None,
                bet_time=None,
                total_amount=None,
                bets_count=0,
                bet_details="",
                status=status,
                error=str(error) if error else None,
                full_text=None,
            )

        ticket = self.parser.parse(ocr_result)
        bet_details = (
            "; ".join(f"{b.match} {b.option}@{b.odds}" for b in ticket.bets)
            if ticket.bets
            else ""
        )

        return ExportRecord(
            source_file=source_file,
            source_filename=source_filename,
            issue_number=ticket.issue_number,
            bet_time=ticket.bet_time,
            total_amount=ticket.total_amount,
            bets_count=len(ticket.bets),
            bet_details=bet_details,
            status=status,
            error=None,
            full_text=ocr_result.get("full_text", ""),
        )

    def export_to_json(
        self,
        records: List[ExportRecord],
        output_path: str,
        include_raw: bool = False,
        raw_data: Optional[Dict] = None,
    ) -> None:
        output = {
            "total": len(records),
            "success_count": sum(1 for r in records if r.status == "success"),
            "failed_count": sum(1 for r in records if r.status == "failed"),
            "records": [r.to_dict() for r in records],
        }

        if include_raw and raw_data:
            output["raw_results"] = raw_data

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

    def export_to_csv(
        self,
        records: List[ExportRecord],
        output_path: str,
    ) -> None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "source_file",
            "source_filename",
            "issue_number",
            "bet_time",
            "total_amount",
            "bets_count",
            "bet_details",
            "status",
            "error",
        ]

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                writer.writerow(record.to_dict())

    def export_batch_result(
        self,
        batch_result,
        output_json: Optional[str] = None,
        output_csv: Optional[str] = None,
        include_raw: bool = False,
    ) -> Dict[str, str]:
        records = []
        raw_data = {}

        for item in batch_result.results:
            image_path = item.get("path", "")
            status = item.get("status", "unknown")
            ocr_result = item.get("data", {}) if status == "success" else None
            error = item.get("error") if status == "failed" else None

            record = self.ocr_result_to_record(
                image_path, ocr_result or {}, status, error
            )
            records.append(record)

            if include_raw and status == "success" and ocr_result:
                raw_data[image_path] = ocr_result

        output_paths = {}

        if output_json:
            self.export_to_json(
                records, output_json, include_raw, raw_data if include_raw else None
            )
            output_paths["json"] = output_json

        if output_csv:
            self.export_to_csv(records, output_csv)
            output_paths["csv"] = output_csv

        return output_paths


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="导出 OCR 批量处理结果")
    parser.add_argument("input_json", help="批量处理结果 JSON 文件路径")
    parser.add_argument("-o", "--output-dir", default="export", help="输出目录")
    parser.add_argument("--json", action="store_true", help="导出 JSON 格式")
    parser.add_argument("--csv", action="store_true", help="导出 CSV 格式")
    parser.add_argument("--both", action="store_true", help="同时导出 JSON 和 CSV")
    parser.add_argument(
        "--include-raw", action="store_true", help="JSON 中包含原始 OCR 数据"
    )

    args = parser.parse_args()

    with open(args.input_json, "r", encoding="utf-8") as f:
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

    json_path = None
    csv_path = None

    if args.json or args.both:
        json_path = str(output_dir / "results.json")
        raw_data = None
        if args.include_raw:
            raw_data = {r.source_file: r for r in records if r.status == "success"}
        exporter.export_to_json(records, json_path, args.include_raw, raw_data)
        print(f"JSON 已导出: {json_path}")

    if args.csv or args.both:
        csv_path = str(output_dir / "results.csv")
        exporter.export_to_csv(records, csv_path)
        print(f"CSV 已导出: {csv_path}")

    if not (args.json or args.csv or args.both):
        print("请指定 --json, --csv 或 --both")
        sys.exit(1)


if __name__ == "__main__":
    main()

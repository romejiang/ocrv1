"""PaddleOCR Pipeline 封装"""

from paddleocr import PaddleOCR
from typing import Dict, List, Optional, Union
import json
from pathlib import Path


class OCRPipeline:
    """单张图片 OCR 处理流水线"""

    def __init__(
        self,
        use_angle_cls: bool = True,
        lang: str = "ch",
        enable_mkldnn: bool = True,
        cpu_threads: int = 8,
    ):
        """初始化 PaddleOCR

        Args:
            use_angle_cls: 是否启用方向分类
            lang: 语言，'ch' 表示中文
            enable_mkldnn: 启用 MKL-DNN 加速
            cpu_threads: CPU 线程数
        """
        self.ocr = PaddleOCR(
            use_angle_cls=use_angle_cls,
            lang=lang,
            enable_mkldnn=enable_mkldnn,
            cpu_threads=cpu_threads,
            rec_batch_num=6,
            det_limit_side_len=640,
            det_limit_type="max",
            show_log=False,
        )

    def process(self, image_path: str, preprocess: bool = True) -> Dict:
        """处理单张图片

        Args:
            image_path: 图片路径
            preprocess: 是否应用预处理

        Returns:
            包含文字、位置、置信度的结构化结果
        """
        from src.preprocessing import preprocess_pipeline

        if preprocess:
            try:
                processed_img = preprocess_pipeline(image_path)
                result = self.ocr.ocr(processed_img, cls=True)
            except ImportError:
                result = self.ocr.ocr(image_path, cls=True)
        else:
            result = self.ocr.ocr(image_path, cls=True)

        return self._parse_result(result)

    def _parse_result(self, ocr_result) -> Dict:
        """解析 OCR 输出为结构化数据"""
        structured = {"words": [], "full_text": "", "regions": []}

        if not ocr_result or not ocr_result[0]:
            return structured

        for line in ocr_result[0]:
            box = line[0]
            text = line[1][0]
            confidence = line[1][1]

            structured["words"].append({"text": text, "confidence": float(confidence)})
            structured["full_text"] += text + "\n"
            structured["regions"].append(
                {"bbox": box, "text": text, "confidence": float(confidence)}
            )

        structured["full_text"] = structured["full_text"].strip()
        return structured

    def process_to_json(
        self, image_path: str, output_path: str, preprocess: bool = True
    ) -> None:
        """处理图片并保存结果到 JSON 文件"""
        result = self.process(image_path, preprocess=preprocess)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="单张图片 OCR 处理")
    parser.add_argument("image_path", help="图片路径")
    parser.add_argument("-o", "--output", default="output.json", help="输出 JSON 路径")
    parser.add_argument("--no-preprocess", action="store_true", help="跳过预处理")
    args = parser.parse_args()

    pipeline = OCRPipeline()
    pipeline.process_to_json(
        args.image_path, args.output, preprocess=not args.no_preprocess
    )
    print(f"结果已保存到: {args.output}")


if __name__ == "__main__":
    main()

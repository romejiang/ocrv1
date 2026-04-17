"""PaddleOCR Pipeline 封装"""

from paddleocr import PaddleOCR
from typing import Dict, List, Optional, Union
import json
from pathlib import Path


class OCRPipeline:
    """单张图片 OCR 处理流水线"""

    def __init__(
        self,
        use_angle_cls: bool = False,
        lang: str = "ch",
        enable_mkldnn: bool = True,
        enable_hpi: bool = None,
        cpu_threads: int = 8,
        use_model: str = "server",
    ):
        """初始化 PaddleOCR

        Args:
            use_angle_cls: 是否启用方向分类（禁用可提升速度）
            lang: 语言，'ch' 表示中文
            enable_mkldnn: 启用 MKL-DNN 加速
            enable_hpi: 启用 HPI 高性能推理模式，为 None 时自动检测
            cpu_threads: CPU 线程数
            use_model: 模型类型，'mobile' 使用 PP-OCRv5_mobile（更快），'server' 使用 PP-OCRv5_server（更高精度）
        """
        import platform

        if enable_hpi is None:
            enable_hpi = False

        det_model_name = f"PP-OCRv5_{use_model}_det"
        rec_model_name = f"PP-OCRv5_{use_model}_rec"

        self.ocr = PaddleOCR(
            use_angle_cls=use_angle_cls,
            lang=lang,
            enable_mkldnn=enable_mkldnn,
            enable_hpi=enable_hpi,
            cpu_threads=cpu_threads,
            rec_batch_num=6,
            det_limit_side_len=640,
            det_limit_type="max",
            text_detection_model_name=det_model_name,
            text_recognition_model_name=rec_model_name,
        )

    def process(
        self, image_path: str, preprocess: bool = True, save_preprocessed: bool = False
    ) -> tuple:
        """处理单张图片

        Args:
            image_path: 图片路径
            preprocess: 是否应用预处理
            save_preprocessed: 是否保存预处理后的图片

        Returns:
            tuple: (结果字典, 预处理时间, OCR时间, 解析时间)
        """
        import time
        from src.preprocessing import preprocess_pipeline, load_image

        t0 = time.time()
        if preprocess:
            processed_img = preprocess_pipeline(
                image_path, save_preprocessed=save_preprocessed
            )
        else:
            # 不预处理时，直接加载原图
            processed_img = load_image(image_path)
        preprocess_time = time.time() - t0

        t1 = time.time()
        result = self.ocr.ocr(processed_img)
        ocr_time = time.time() - t1

        t2 = time.time()
        parsed = self._parse_result(result)
        parse_time = time.time() - t2

        return parsed, preprocess_time, ocr_time, parse_time

    def _parse_result(self, ocr_result) -> Dict:
        """解析 OCR 输出为结构化数据"""
        structured = {"words": [], "full_text": "", "regions": []}

        if not ocr_result or not ocr_result[0]:
            return structured

        page_data = ocr_result[0]
        rec_texts = page_data.get("rec_texts", [])
        rec_scores = page_data.get("rec_scores", [])
        rec_polys = page_data.get("rec_polys", [])

        for i, text in enumerate(rec_texts):
            confidence = rec_scores[i] if i < len(rec_scores) else 0.0
            poly = rec_polys[i] if i < len(rec_polys) else []

            word_id = f"w{i}"
            structured["words"].append(
                {
                    "id": word_id,
                    "text": text,
                    "confidence": float(confidence),
                }
            )
            structured["full_text"] += text + "\n"
            structured["regions"].append(
                {
                    "id": word_id,
                    "bbox": poly.tolist() if hasattr(poly, "tolist") else poly,
                    "text": text,
                    "confidence": float(confidence),
                }
            )

        structured["full_text"] = structured["full_text"].strip()
        return structured

    def process_to_json(
        self, image_path: str, output_path: str, preprocess: bool = True
    ) -> Dict:
        """处理图片并保存结果到 JSON 文件

        Returns:
            结构化结果字典
        """
        result = self.process(image_path, preprocess=preprocess)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return result


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="单张图片 OCR 处理")
    parser.add_argument("image_path", help="图片路径")
    parser.add_argument("-o", "--output", default="output.json", help="输出 JSON 路径")
    parser.add_argument("--no-preprocess", action="store_true", help="跳过预处理")
    args = parser.parse_args()

    pipeline = OCRPipeline()
    result = pipeline.process_to_json(
        args.image_path, args.output, preprocess=not args.no_preprocess
    )
    print(f"结果已保存到: {args.output}")
    print(f"识别文字: {result.get('full_text', '')[:200]}...")


if __name__ == "__main__":
    main()

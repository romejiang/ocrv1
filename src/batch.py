"""批量处理模块 - 支持文件夹/ZIP导入、多进程处理、进度展示"""

import os
import zipfile
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import tempfile
import shutil

from tqdm import tqdm


SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

_pipeline_instance = None


def _init_worker():
    global _pipeline_instance
    from src.pipeline import OCRPipeline

    _pipeline_instance = OCRPipeline(use_model="server")


def _process_single_worker(args: Tuple[str, bool]) -> Tuple[str, bool, Dict]:
    image_path, use_preprocess = args
    try:
        result = _pipeline_instance.process(image_path, preprocess=use_preprocess)
        return image_path, True, result
    except Exception as e:
        return image_path, False, str(e)


@dataclass
class BatchResult:
    total: int = 0
    success: int = 0
    failed: int = 0
    results: List[Dict] = field(default_factory=list)
    errors: List[Dict] = field(default_factory=list)

    def add_success(self, image_path: str, result: Dict):
        self.success += 1
        self.results.append({"path": image_path, "status": "success", "data": result})

    def add_failure(self, image_path: str, error: str):
        self.failed += 1
        self.errors.append({"path": image_path, "status": "failed", "error": error})
        self.results.append({"path": image_path, "status": "failed", "error": error})


class BatchProcessor:
    def __init__(
        self,
        max_workers: Optional[int] = None,
        log_dir: str = "logs",
        error_mark_dir: str = "errors",
    ):
        self.max_workers = max_workers or max(1, cpu_count() - 1)
        self.log_dir = Path(log_dir)
        self.error_mark_dir = Path(error_mark_dir)
        self._setup_logging()

    def _setup_logging(self):
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.error_mark_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger("batch_processor")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            fh = logging.FileHandler(self.log_dir / "batch_process.log")
            fh.setLevel(logging.INFO)
            ch = logging.StreamHandler()
            ch.setLevel(logging.WARNING)
            fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            fh.setFormatter(fmt)
            ch.setFormatter(fmt)
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)

    def _is_image(self, path: Path) -> bool:
        return path.suffix.lower() in SUPPORTED_FORMATS

    def _collect_images_from_folder(self, folder_path: str) -> List[Path]:
        folder = Path(folder_path)
        if not folder.is_dir():
            raise ValueError(f"文件夹不存在: {folder_path}")

        images = []
        for ext in SUPPORTED_FORMATS:
            images.extend(folder.rglob(f"*{ext}"))
            images.extend(folder.rglob(f"*{ext.upper()}"))
        return sorted(set(images))

    def _collect_images_from_zip(
        self, zip_path: str, extract_dir: Optional[str] = None
    ) -> Tuple[List[Path], str]:
        zip_path = Path(zip_path)
        if not zip_path.is_file():
            raise ValueError(f"ZIP文件不存在: {zip_path}")

        if extract_dir is None:
            extract_dir = tempfile.mkdtemp(prefix="ocr_batch_")

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        images = []
        extract_path = Path(extract_dir)
        for ext in SUPPORTED_FORMATS:
            images.extend(extract_path.rglob(f"*{ext}"))
            images.extend(extract_path.rglob(f"*{ext.upper()}"))
        return sorted(set(images)), extract_dir

    def _mark_error_image(self, image_path: str, error: str):
        try:
            img_path = Path(image_path)
            if img_path.exists():
                error_dir = self.error_mark_dir / "failed_images"
                error_dir.mkdir(parents=True, exist_ok=True)
                error_file = error_dir / f"{img_path.stem}_error{img_path.suffix}"
                shutil.copy2(img_path, error_file)

                error_info = error_dir / f"{img_path.stem}_error.txt"
                with open(error_info, "w", encoding="utf-8") as f:
                    f.write(f"Original: {image_path}\nError: {error}\n")
        except Exception as e:
            self.logger.warning(f"标记错误图片失败 {image_path}: {e}")

    def collect_inputs(self, input_path: str) -> List[Path]:
        path = Path(input_path)

        if path.is_file():
            if path.suffix.lower() == ".zip":
                images, _ = self._collect_images_from_zip(str(path))
                return images
            elif self._is_image(path):
                return [path]
            else:
                raise ValueError(f"不支持的文件格式: {path.suffix}")
        elif path.is_dir():
            return self._collect_images_from_folder(str(path))
        else:
            raise ValueError(f"路径不存在: {input_path}")

    def process_single(self, args: Tuple[str, bool]) -> Tuple[str, bool, Dict]:
        image_path, use_preprocess = args
        try:
            from src.pipeline import OCRPipeline

            pipeline = OCRPipeline()
            result = pipeline.process(image_path, preprocess=use_preprocess)
            return image_path, True, result
        except Exception as e:
            return image_path, False, str(e)

    def process_batch(
        self,
        image_paths: List[Path],
        use_preprocess: bool = True,
        show_progress: bool = True,
    ) -> BatchResult:
        total = len(image_paths)
        result = BatchResult(total=total)

        if total == 0:
            return result

        self.logger.info(
            f"开始批量处理: {total} 张图片, 使用 {self.max_workers} 个进程"
        )

        args_list = [(str(p), use_preprocess) for p in image_paths]

        with ProcessPoolExecutor(
            max_workers=self.max_workers,
            initializer=_init_worker,
        ) as executor:
            futures = {
                executor.submit(_process_single_worker, args): args
                for args in args_list
            }

            if show_progress:
                pbar = tqdm(total=total, desc="处理中", unit="张")

            for future in as_completed(futures):
                image_path, success, data = future.result()
                if success:
                    result.add_success(image_path, data)
                    self.logger.info(f"成功: {image_path}")
                else:
                    result.add_failure(image_path, data)
                    self._mark_error_image(image_path, data)
                    self.logger.error(f"失败: {image_path} - {data}")
                    if show_progress:
                        pbar.write(f"错误 [{image_path}]: {data}")

                if show_progress:
                    pbar.update(1)

            if show_progress:
                pbar.close()

        self.logger.info(
            f"批量处理完成: 成功 {result.success}/{total}, 失败 {result.failed}/{total}"
        )
        return result

    def process(
        self,
        input_path: str,
        use_preprocess: bool = True,
        show_progress: bool = True,
    ) -> BatchResult:
        try:
            image_paths = self.collect_inputs(input_path)
            return self.process_batch(image_paths, use_preprocess, show_progress)
        except Exception as e:
            result = BatchResult()
            result.add_failure(input_path, str(e))
            return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="批量OCR处理")
    parser.add_argument("input", help="图片文件夹或ZIP文件路径")
    parser.add_argument(
        "-o", "--output", default="batch_results.json", help="输出JSON路径"
    )
    parser.add_argument("--csv", help="同时导出 CSV 路径")
    parser.add_argument("--workers", type=int, default=None, help="并行进程数")
    parser.add_argument("--no-preprocess", action="store_true", help="跳过预处理")
    parser.add_argument("--log-dir", default="logs", help="日志目录")
    parser.add_argument("--error-dir", default="errors", help="错误图片目录")
    args = parser.parse_args()

    processor = BatchProcessor(
        max_workers=args.workers,
        log_dir=args.log_dir,
        error_mark_dir=args.error_dir,
    )

    print(f"开始处理: {args.input}")
    batch_result = processor.process(
        args.input,
        use_preprocess=not args.no_preprocess,
        show_progress=True,
    )

    from src.exporter import Exporter

    exporter = Exporter()

    output_paths = exporter.export_batch_result(
        batch_result,
        output_json=args.output,
        output_csv=args.csv,
        include_raw=False,
    )

    print(f"\n处理完成!")
    print(f"总计: {batch_result.total}")
    print(f"成功: {batch_result.success}")
    print(f"失败: {batch_result.failed}")
    for fmt, path in output_paths.items():
        print(f"{fmt.upper()}: {path}")


if __name__ == "__main__":
    main()

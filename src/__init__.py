"""足彩彩票票面扫描工具"""

__version__ = "0.1.0"

__all__ = [
    "OCRPipeline",
    "load_image",
    "convert_to_grayscale",
    "denoise",
    "binarize",
    "correct_perspective",
    "resize_keep_aspect",
    "preprocess_pipeline",
    "BatchProcessor",
    "BatchResult",
    "SUPPORTED_FORMATS",
    "LotteryParser",
    "LotteryTicket",
    "Bet",
]


def __getattr__(name):
    if name == "OCRPipeline":
        from src.pipeline import OCRPipeline

        return OCRPipeline
    if name == "BatchProcessor":
        from src.batch import BatchProcessor

        return BatchProcessor
    if name == "BatchResult":
        from src.batch import BatchResult

        return BatchResult
    if name == "SUPPORTED_FORMATS":
        from src.batch import SUPPORTED_FORMATS

        return SUPPORTED_FORMATS
    if name in {
        "load_image",
        "convert_to_grayscale",
        "denoise",
        "binarize",
        "correct_perspective",
        "resize_keep_aspect",
        "preprocess_pipeline",
    }:
        from src import preprocessing

        return getattr(preprocessing, name)
    if name in {"LotteryParser", "LotteryTicket", "Bet"}:
        from src import parser

        return getattr(parser, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

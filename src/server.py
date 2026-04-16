"""OCR API Server - HTTP 服务接口

模型启动时加载一次，之后复用，提高处理效率。
"""

import os
import sys
import warnings
import logging
from pathlib import Path
from typing import Optional

# 抑制所有 warnings 和日志
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
os.environ.setdefault("GLOG_v", "0")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

warnings.filterwarnings("ignore")
for logger_name in [
    "ppocr",
    "paddle",
    "paddleocr",
    "urllib3",
    "PIL",
    "cv2",
    "fastapi",
    "uvicorn",
]:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.ERROR)
    logger.disabled = True

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import time

# 全局 OCR Pipeline 实例（服务启动时加载）
ocr_pipeline = None


class OCRRequest(BaseModel):
    image_path: str
    preprocess: bool = True
    save_preprocessed: bool = False


class OCRResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    process_time: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    """服务启动/关闭时的生命周期管理"""
    global ocr_pipeline
    print("正在加载 OCR 模型...", file=sys.stderr)
    start = time.time()
    from src.pipeline import OCRPipeline

    ocr_pipeline = OCRPipeline()
    load_time = time.time() - start
    print(f"OCR 模型加载完成 ({load_time:.1f}s)", file=sys.stderr)
    yield
    print("关闭 OCR 服务...", file=sys.stderr)


app = FastAPI(
    title="足彩彩票票面 OCR API",
    description="批量扫描足彩彩票票面，提取投注内容、期号、金额等结构化数据",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "model_loaded": ocr_pipeline is not None}


@app.post("/ocr", response_model=OCRResponse)
async def ocr_image(request: OCRRequest):
    """OCR 处理接口

    接收图片路径，返回识别结果。
    """
    global ocr_pipeline

    if ocr_pipeline is None:
        raise HTTPException(status_code=503, detail="OCR 模型未加载")

    if not Path(request.image_path).exists():
        raise HTTPException(status_code=400, detail=f"图片不存在: {request.image_path}")

    start = time.time()
    preprocess_time = 0
    ocr_time = 0
    parse_time = 0

    try:
        t0 = time.time()
        result, preprocess_time, ocr_time, parse_time = ocr_pipeline.process(
            request.image_path,
            preprocess=request.preprocess,
            save_preprocessed=request.save_preprocessed,
        )
        process_time = time.time() - start

        print(
            f"[OCR] total={process_time:.3f}s preprocess={preprocess_time:.3f}s ocr={ocr_time:.3f}s parse={parse_time:.3f}s path={request.image_path}",
            file=sys.stderr,
        )

        return OCRResponse(
            success=True,
            data=result,
            process_time=process_time,
        )
    except Exception as e:
        process_time = time.time() - start
        print(f"[OCR] ERROR: {e} total={process_time:.3f}s", file=sys.stderr)
        return OCRResponse(
            success=False,
            error=str(e),
            process_time=process_time,
        )


@app.get("/ocr/batch")
async def ocr_batch_status():
    """批量处理状态（预留）"""
    return {"status": "not_implemented", "message": "批量处理接口开发中"}


def main():
    """启动 API 服务"""
    import argparse

    parser = argparse.ArgumentParser(description="足彩彩票 OCR API 服务器")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=8765, help="监听端口")
    args = parser.parse_args()

    print(f"启动 OCR API 服务: http://{args.host}:{args.port}", file=sys.stderr)
    print(f"API 文档: http://{args.host}:{args.port}/docs", file=sys.stderr)

    import uvicorn

    uvicorn.run(
        "src.server:app",
        host=args.host,
        port=args.port,
        reload=False,
        log_level="error",
    )


if __name__ == "__main__":
    main()

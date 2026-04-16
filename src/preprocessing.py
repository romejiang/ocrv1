"""图像预处理模块"""

import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional


def load_image(path: str) -> np.ndarray:
    """使用 Pillow 读取图片并转换为 RGB numpy array"""
    img = Image.open(path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return np.array(img)


def convert_to_grayscale(img: np.ndarray) -> np.ndarray:
    """转换为灰度图"""
    return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)


def denoise(img: np.ndarray, strength: int = 10) -> np.ndarray:
    """去噪 - 印刷品噪点去除"""
    return cv2.fastNlMeansDenoisingColored(img, None, strength, strength, 7, 21)


def binarize(img: np.ndarray, method: str = "otsu") -> np.ndarray:
    """二值化 - 全局/自适应阈值"""
    if len(img.shape) == 3:
        img = convert_to_grayscale(img)
    if method == "otsu":
        _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        binary = cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
    return binary


def correct_perspective(
    img: np.ndarray, points: Optional[np.ndarray] = None
) -> np.ndarray:
    """透视矫正 - 如果提供4点坐标则进行矫正"""
    if points is None or len(points) != 4:
        return img
    rect = np.zeros((4, 2), dtype=np.float32)
    pts = points.reshape(4, 2)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    width = int(
        max(np.linalg.norm(rect[0] - rect[1]), np.linalg.norm(rect[2] - rect[3]))
    )
    height = int(
        max(np.linalg.norm(rect[0] - rect[3]), np.linalg.norm(rect[1] - rect[2]))
    )
    dst = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(img, M, (width, height))


def resize_keep_aspect(img: np.ndarray, target_size: int = 1280) -> np.ndarray:
    """保持宽高比缩放"""
    h, w = img.shape[:2]
    if max(h, w) <= target_size:
        return img
    scale = target_size / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def preprocess_pipeline(
    image_path: str,
    apply_denoise: bool = True,
    apply_perspective: bool = False,
    perspective_points: Optional[np.ndarray] = None,
) -> np.ndarray:
    """完整预处理流水线"""
    img = load_image(image_path)
    if apply_denoise:
        img = denoise(img)
    if apply_perspective and perspective_points is not None:
        img = correct_perspective(img, perspective_points)
    img = resize_keep_aspect(img)
    return img

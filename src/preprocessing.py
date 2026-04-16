"""图像预处理模块"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
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


def should_enhance_contrast(img: np.ndarray) -> bool:
    """判断图片是否需要增强对比度

    通过分析图片的直方图和亮度分布来判断：
    - 如果图片太暗或太亮（平均亮度偏离中值太远），需要增强
    - 如果图片对比度已经很好（直方图分布广泛），不需要增强
    """
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # 计算平均亮度
    mean_brightness = np.mean(gray)

    # 计算亮度标准差（反映对比度）
    std_brightness = np.std(gray)

    # 计算直方图分布
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist.flatten() / hist.sum()

    # 计算直方图熵（反映内容丰富程度）
    hist_nonzero = hist[hist > 0]
    entropy = -np.sum(hist_nonzero * np.log2(hist_nonzero))

    # 判断条件
    # 1. 平均亮度不在合适范围 (60-200)
    # 2. 或者对比度太低 (std < 30)
    # 3. 或者内容太单调 (熵 < 4)
    needs_enhancement = (
        mean_brightness < 60
        or mean_brightness > 200
        or std_brightness < 30
        or entropy < 4
    )

    return needs_enhancement


def enhance_contrast(img: np.ndarray, factor: float = 1.25) -> np.ndarray:
    """增强对比度（仅在需要时应用）

    Args:
        img: 输入图片 (RGB)
        factor: 对比度因子，1.25 表示 +25%
    """
    if not should_enhance_contrast(img):
        return img

    # 转换为 LAB 色彩空间
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)

    # 对 L 通道应用直方图均衡化增强对比度
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)

    # 合并通道并转回 RGB
    lab_enhanced = cv2.merge([l_enhanced, a, b])
    enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2RGB)

    # 应用对比度因子
    enhanced = np.clip(enhanced * factor, 0, 255).astype(np.uint8)
    return enhanced


def compress_image(
    img: np.ndarray, target_width: int = 1440, quality: int = 85
) -> np.ndarray:
    """压缩图片尺寸和质量

    Args:
        img: 输入图片 (RGB numpy array)
        target_width: 目标宽度
        quality: JPEG 质量 (1-100)
    """
    h, w = img.shape[:2]

    # 如果宽度小于目标宽度，不缩放
    if w <= target_width:
        return img

    # 计算缩放比例
    scale = target_width / w
    new_height = int(h * scale)

    # 缩放图片
    resized = cv2.resize(img, (target_width, new_height), interpolation=cv2.INTER_AREA)

    # JPEG 压缩模拟（通过 Pillow 保存再读取来模拟 JPEG 压缩效果）
    # 注意：这里直接返回缩放后的图片，真实 JPEG 压缩在实际保存时进行
    return resized


def preprocess_pipeline(
    image_path: str,
    apply_denoise: bool = True,
    apply_grayscale: bool = True,
    apply_contrast: bool = True,
    apply_compress: bool = True,
    apply_perspective: bool = False,
    perspective_points: Optional[np.ndarray] = None,
    target_width: int = 1440,
    quality: int = 85,
    save_preprocessed: bool = False,
) -> np.ndarray:
    """完整预处理流水线

    Args:
        image_path: 图片路径
        apply_denoise: 是否去噪
        apply_grayscale: 是否灰度化
        apply_contrast: 是否增强对比度
        apply_compress: 是否压缩尺寸
        apply_perspective: 是否透视矫正
        perspective_points: 透视矫正的4点坐标
        target_width: 压缩目标宽度
        quality: JPEG 质量
        save_preprocessed: 是否保存预处理后的图片
    """
    img = load_image(image_path)

    # 对比度增强 +25%（仅在需要时）
    if apply_contrast:
        if should_enhance_contrast(img):
            img = enhance_contrast(img, factor=1.25)
            print(f"[预处理] 图片对比度已增强")
        else:
            print(f"[预处理] 跳过对比度增强（图片质量已足够）")

    # 灰度化 - 减少文件大小，去除颜色干扰
    if apply_grayscale:
        gray = convert_to_grayscale(img)
        # 灰度图转回 RGB（某些预处理函数需要 RGB 输入）
        img = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

    # 去噪
    if apply_denoise:
        img = denoise(img)

    # 透视矫正
    if apply_perspective and perspective_points is not None:
        img = correct_perspective(img, perspective_points)

    # 尺寸压缩 - 宽度 1440px
    if apply_compress:
        img = compress_image(img, target_width=target_width)

    # 保存预处理后的图片
    if save_preprocessed:
        input_path = Path(image_path)
        output_path = input_path.parent / f"{input_path.stem}_processed.png"
        Image.fromarray(img).save(output_path)
        print(f"预处理后的图片已保存: {output_path}")

    return img

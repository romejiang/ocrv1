# PITFALLS.md — 彩票票面 OCR 识别项目

**Domain:** PaddleOCR 批量图像处理
**Researched:** 2026-04-16
**Confidence:** MEDIUM-HIGH (基于 PaddleOCR 官方文档和常见问题)

---

## Critical Pitfalls

### Pitfall 1: 不做图像预处理导致识别率低

**What goes wrong:** 彩票票面图像质量参差不齐（反光、折叠、褶皱、污渍），直接送入 OCR 识别率极低。常见表现：文字识别错误、漏识别、置信度普遍低于 0.7。

**Why it happens:** 忽略图像质量对 OCR 的决定性影响。PaddleOCR 官方文档明确指出："Blurry or low-contrast images can significantly hinder OCR performance"（模糊或低对比度图像会严重阻碍 OCR 性能）。

**Consequences:**
- 大量误识别（如 "3" 识别成 "8"，"负" 识别成 "贞"）
- 关键字段（金额、期号）提取错误
- 后期数据清洗成本高

**Prevention:** Phase 1 必须包含图像预处理模块：
```python
# 建议的预处理流程
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

def preprocess_lottery_image(image_path):
    img = Image.open(image_path)
    # 灰度化
    img = img.convert('L')
    # 对比度增强
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    # 去噪
    img = img.filter(ImageFilter.MedianFilter(size=3))
    # 二值化（Otsu's method）
    img_array = np.array(img)
    _, img_binary = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(img_binary)
```

**Detection:** 监控单张图片 OCR 结果的平均置信度，若 < 0.85 应触发预处理重试。

**Phase:** Phase 1/2（图像预处理）— 这是基础，不做好后面全废。

---

### Pitfall 2: 错误使用 mobile 模型做批量识别

**What goes wrong:** 为了"轻量"选择 PP-OCRv5_mobile 模型处理批量任务，速度慢且识别率低。官方数据显示 mobile 模型准确率 0.8015，server 模型 0.8401，差距明显。

**Why it happens:** 混淆了"轻量部署"和"批量处理"的场景。mobile 模型适合移动端实时处理，不适合批量服务器场景。

**Consequences:**
- 批量处理时间成倍增加（mobile 模型虽小但未针对批量优化）
- 识别率低导致的后续人工核对成本
- 需多次重跑浪费计算资源

**Prevention:**
- CPU 批量处理使用 `PP-OCRv5_server` 系列模型
- 官方建议："For batch processing, use PP-OCRv5_server series for high accuracy"

```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_angle_cls=True,
    lang='ch',
    use_gpu=False,
    enable_mkldnn=True,  # CPU 加速
    cpu_threads=8        # 多线程
    # 不指定 det_model_dir 和 rec_model_dir 则默认下载 server 模型
)
```

**Phase:** Phase 1（基础架构）— 模型选择应在早期确定，更换成本高。

---

### Pitfall 3: batch_size=1 导致批量处理效率极低

**What goes wrong:** 逐张处理图片，未利用 PaddleOCR 的批量处理能力。100 张图片处理时间可能是批量处理的 5-10 倍。

**Why it happens:** 不理解 `predict()` 方法支持目录批量输入。官方文档明确指出："Pass the directory path directly to the predict method... is recommended for maximizing processing efficiency compared to iterating and predicting files one by one."

**Consequences:**
- 100 张图片用 1 小时而非 10 分钟
- CPU 利用率低（单线程）
- 内存使用不稳定

**Prevention:** 使用目录批量处理：
```python
# 错误方式（逐张处理）
for file in file_list:
    result = ocr.ocr(file)

# 正确方式（批量处理）
results = ocr.predict("path/to/images/", batch_size=8)
```

**Phase:** Phase 1（批量处理架构）— 这是性能关键。

---

### Pitfall 4: 未配置 MKL-DNN 和 CPU 线程优化

**What goes wrong:** CPU 模式下未启用 MKL-DNN 加速，推理速度极慢。官方文档指出 MKL-DNN 可显著提升 CPU 推理性能。

**Why it happens:** 使用默认配置，忽略了 CPU 优化参数。

**Consequences:**
- 单张图片处理时间从 1 秒变成 5+ 秒
- 1000 张图片可能需要 2 小时而非 20 分钟

**Prevention:**
```python
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='ch',
    use_gpu=False,
    enable_mkldnn=True,        # 启用 MKL-DNN 加速
    cpu_threads=8,              # 根据 CPU 核心数设置
    mkldnn_cache_capacity=10485760  # 10MB 缓存
)
```

**Phase:** Phase 1（性能优化）— 尽早配置，便于性能基准测试。

---

### Pitfall 5: 图像尺寸限制参数理解错误

**What goes wrong:** `det_limit_side_len` 参数设置不当导致大图截断或小图放大失真。彩票票面通常是固定比例，切割会丢失信息。

**Why it happens:** 不理解 limit_type 的 min/max 区别：
- `max`: 最长边限制在指定值内（保持比例）
- `min`: 最短边至少达到指定值

**Consequences:**
- 票面内容被截断（如底部金额被切掉）
- 赔率数字被压缩导致误识别
- 宽高比扭曲

**Prevention:**
```python
ocr = PaddleOCR(
    limit_type='max',      # 保持比例
    max_side_limit=1920,   # 适当提高限制，彩票票面需要清晰
    det_limit_side_len=960,  # 检测模型的输入尺寸
)
```

**Phase:** Phase 1（参数调优）— 需要用真实彩票样本测试。

---

### Pitfall 6: 未启用角度分类器处理旋转票据

**What goes wrong:** 彩票扫描时可能旋转（90°、180°、270°），未启用角度分类导致整页识别失败或识别顺序混乱。

**Why it happens:** 认为"我的图片都是正向的"——但批量扫描无法保证，且 use_angle_cls=True 会有轻微性能损失。

**Consequences:**
- 旋转 90° 的图片识别出乱序文字
- 180° 旋转的文字被识别为乱码
- 需要人工核对

**Prevention:**
```python
ocr = PaddleOCR(use_angle_cls=True, lang='ch')  # 必须启用
```

**Phase:** Phase 1（基础配置）— 应该默认启用，不要为了性能省这点。

---

### Pitfall 7: 未处理 PDF 文件和目录遍历

**What goes wrong:** 用户传入 ZIP 压缩包或 PDF 文件时报错停止。或者目录中有隐藏文件、非图像文件导致程序崩溃。

**Why it happens:** 
- 官方文档明确指出："PDF files in directories are not supported; PDF files must be specified by file path"
- 未过滤 `.DS_Store`、`Thumbs.db` 等系统文件

**Consequences:**
- 批量处理因单张报错中断
- ZIP 包无法直接处理
- 部分图片失败导致整批重跑

**Prevention:**
```python
import os
from pathlib import Path
from PIL import Image

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}

def get_valid_image_files(directory):
    """递归获取目录中所有有效图像文件，跳过隐藏文件和子目录"""
    valid_files = []
    for root, dirs, files in os.walk(directory):
        # 跳过隐藏目录
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.startswith('.'):
                continue
            ext = Path(file).suffix.lower()
            if ext in ALLOWED_EXTENSIONS:
                valid_files.append(os.path.join(root, file))
    return valid_files

def process_zip(zip_path, output_dir):
    """处理 ZIP 包"""
    import zipfile
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(output_dir)
    return get_valid_image_files(output_dir)
```

**Phase:** Phase 2（批量导入）— 用户交互的关键路径。

---

### Pitfall 8: 内存泄漏导致批量处理崩溃

**What goes wrong:** 处理大批量图片时内存持续增长，最终 OOM 崩溃。常见于处理 500+ 张图片时。

**Why it happens:** PaddleOCR 内部有内存缓存机制，未配置 `enable_memory_optim` 且未清理中间结果。

**Prevention:**
```python
# 每次处理后清理
import gc

def process_batch(image_paths, batch_size=8):
    all_results = []
    for i in range(0, len(image_paths), batch_size):
        batch = image_paths[i:i+batch_size]
        results = ocr.predict(batch)
        all_results.extend(results)
        # 定期清理
        if i % 100 == 0:
            gc.collect()
    return all_results
```

```python
# 初始化时启用内存优化
ocr = PaddleOCR(
    enable_memory_optim=True,  # 启用内存优化
    gpu_mem=200,              # 限制 GPU 内存（即使使用 CPU）
)
```

**Phase:** Phase 1（稳定性）— 批量处理必须能稳定运行。

---

## Moderate Pitfalls

### Pitfall 9: 阈值参数未针对彩票场景调优

**What goes wrong:** 使用默认 `box_thresh=0.5`、`thresh=0.3`，导致票据上小字（赔率）漏检或背景噪点误检。

**Why it happens:** 默认阈值基于通用文档，彩票票面有独特的文字大小和间距。

**Prevention:** 用真实样本测试并调整：
```python
ocr = PaddleOCR(
    thresh=0.25,       # 降低以检测浅色文字
    box_thresh=0.45,   # 降低以检测小字
    unclip_ratio=1.8, # 适当扩大检测框
)
```

**Phase:** Phase 2（参数调优）— 需要真实样本反馈。

---

### Pitfall 10: 忽略错误处理和日志

**What goes wrong:** 单张图片失败导致整批中断，没有错误日志记录哪些图片失败及原因。

**Why it happens:** 开发时用小批量测试，路径都是英文，文件都是完整的。

**Consequences:**
- 1000 张图片处理到第 999 张失败，不知哪些成功
- 损坏图片（如 JPEG 截断）静默跳过
- 难以复现和调试问题

**Prevention:**
```python
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_with_error_handling(image_path):
    try:
        result = ocr.ocr(image_path)
        return {"path": image_path, "success": True, "result": result}
    except Exception as e:
        logger.error(f"Failed to process {image_path}: {e}")
        return {"path": image_path, "success": False, "error": str(e)}
```

**Phase:** Phase 2（稳定性）— 批量处理必须有容错能力。

---

## Minor Pitfalls

### Pitfall 11: 输出格式设计不合理

**What goes wrong:** OCR 结果平铺存储，丢失空间关系（如赔率属于哪场比赛）。

**Why it happens:** 只关注文字内容，未考虑数据结构化需求。

**Prevention:** 阶段一就设计好输出 schema：
```json
{
  "image": "path/to/ticket.jpg",
  "period": "2024-001",
  "bet_time": "2024-01-15 10:30",
  "total_amount": "50.00",
  "matches": [
    {
      "id": 1,
      "teams": "曼联 vs 切尔西",
      "bet_type": "胜平负",
      "option": "主胜",
      "odds": "1.85"
    }
  ]
}
```

**Phase:** Phase 1（数据模型）— 好的数据结构让后续处理简单。

---

### Pitfall 12: 未验证模型对彩票文字的覆盖

**What goes wrong:** 模型训练数据不包含彩票特有字符（如特定符号、"胜"、"平"、"负"的特殊写法），导致识别失败。

**Why it happens:** 彩票票面使用印刷体，但具体字体可能与训练数据不同。

**Prevention:** 用 5-10 张真实彩票测试：
```python
test_samples = load_test_images("tests/fixtures/lottery_tickets/")
for img_path in test_samples:
    result = ocr.ocr(img_path)
    assert has_keywords(result, ["胜", "平", "负", "SP"]), f"Missing expected keywords in {img_path}"
```

**Phase:** Phase 1（验证）— 用真实数据验证可行性。

---

## Phase-Specific Warnings

| Phase | Topic | Likely Pitfall | Mitigation |
|-------|-------|----------------|------------|
| Phase 1 | 图像预处理 | 预处理参数不对导致过度处理 | 用样本对比原图和预处理后效果 |
| Phase 1 | 模型选择 | 选错 mobile vs server | Batch 处理用 server，参考官方性能数据 |
| Phase 1 | 批量架构 | 逐张处理效率低 | 用 predict(dir) 而非循环 |
| Phase 2 | 参数调优 | 阈值不适合彩票 | 用真实样本反复测试 |
| Phase 2 | 错误处理 | 单张失败导致中断 | try-catch + 日志 + 继续处理 |
| Phase 3 | 数据导出 | 结构化不完整 | 先定义 schema 再实现导出 |

---

## Sources

- [PaddleOCR Official Documentation](https://github.com/paddlepaddle/paddleocr) — HIGH confidence
- [PaddleOCR Batch Processing](https://github.com/paddlepaddle/paddleocr/blob/main/docs/version3.x/pipeline_usage/PaddleOCR-VL.en.md) — HIGH confidence
- [PaddleOCR CPU Optimization](https://github.com/paddlepaddle/paddleocr/blob/main/docs/version3.x/module_usage/text_detection.en.md) — HIGH confidence
- [PaddleOCR Model Selection FAQ](https://github.com/paddlepaddle/paddleocr/blob/main/docs/FAQ.en.md) — HIGH confidence
- [PaddleOCR PP-OCRv5 Performance](https://github.com/paddlepaddle/paddleocr/blob/main/docs/version3.x/algorithm/PP-OCRv5/PP-OCRv5.en.md) — HIGH confidence

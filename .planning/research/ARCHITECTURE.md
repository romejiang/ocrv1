# Architecture Patterns: PaddleOCR Batch Processing

**Domain:** Lottery ticket OCR batch processing
**Project:** 足彩彩票票面扫描工具
**Researched:** 2026-04-16
**Confidence:** HIGH (verified via official documentation)

## Executive Summary

PaddleOCR batch processing systems follow a modular pipeline architecture with three core stages: **preprocessing** → **text detection** → **text recognition**. For CPU-only batch processing, the recommended pattern uses Python multiprocessing with a shared task queue to distribute work across worker processes, each running its own OCR pipeline instance.

## Core Pipeline Architecture

PaddleOCR's PP-OCRv5 pipeline consists of these sequential stages:

```
Image Input → Preprocessing → Text Detection → Text Recognition → Structured Output
```

### Stage 1: Preprocessing (Optional)

| Module | Purpose | Enabled By |
|--------|---------|------------|
| DocOrientationClassify | Detect image rotation | `use_doc_orientation_classify=True` |
| DocUnwarping | Correct image distortion | `use_doc_unwarping=True` |
| TextLineOrientation | Detect text direction | `use_textline_orientation=True` |

**Recommendation for lottery tickets:** Disable all preprocessing modules to reduce inference overhead. Lottery tickets are typically scanned upright with minimal distortion.

### Stage 2: Text Detection

Detects bounding boxes around text regions.

| Parameter | Default | Recommendation |
|-----------|---------|----------------|
| `det_limit_side_len` | 960 | 640 (lottery tickets have small text) |
| `det_limit_type` | max | max |
| `thresh` | 0.3 | 0.3-0.5 (higher = fewer false positives) |
| `box_thresh` | 0.6 | 0.6-0.8 |

### Stage 3: Text Recognition

Recognizes text content within detected bounding boxes.

| Parameter | Default | Recommendation |
|-----------|---------|----------------|
| `text_recognition_batch_size` | 6 | 6 (CPU) |
| `rec_batch_num` | 1 | 1-6 |
| `score_thresh` | 0.0 | 0.5 (filter low-confidence results) |

## Component Boundaries

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Batch Orchestrator                            │
│  (main process: task queue, file discovery, result aggregation)     │
└─────────────────────────────────────────────────────────────────────┘
         │                                           ▲
         ▼                                           │
┌─────────────────┐     ┌─────────────────┐     ┌─────────────┐
│  Worker Process │────▶│  PaddleOCR      │────▶│   Output    │
│  (OCR Pipeline)│     │  Pipeline       │     │   JSON/CSV  │
└─────────────────┘     │  - Detection    │     └─────────────┘
                        │  - Recognition  │
                        └─────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Boundaries |
|-----------|---------------|-----------|
| **Batch Orchestrator** | File discovery, task distribution, result aggregation | Talks to workers via multiprocessing.Queue |
| **Worker Process** | Loads OCR pipeline, processes batches, saves results | One pipeline per worker; stateless to orchestrator |
| **PaddleOCR Pipeline** | Text detection + recognition | Configured at init; processes batch of images |
| **Result Handler** | Parses OCR output, structures data | Input from workers; output to file |

## Data Flow

```
1. INPUT DISCOVERY
   Source dir/ZIP → File list → Task Queue (Manager.Queue)

2. WORKER DISTRIBUTION
   Main process spawns N workers → Each worker has own PaddleOCR instance
   Workers pull from shared task queue

3. BATCH PROCESSING (per worker)
   Images[] → PaddleOCR.predict() → OCR Results[]

4. RESULT AGGREGATION
   Worker saves JSON → Main process monitors completion
   Final aggregation → Combined JSON/CSV export
```

### Worker Loop Pattern

```python
def worker(task_queue, batch_size, output_dir):
    ocr = PaddleOCR(use_doc_orientation_classify=False,
                     use_doc_unwarping=False,
                     use_textline_orientation=False)
    
    batch = []
    while True:
        try:
            img_path = task_queue.get_nowait()
            batch.append(img_path)
        except Empty:
            break
            
        if len(batch) == batch_size or no_more_tasks:
            results = ocr.predict(batch)
            for result in results:
                result.save_to_json(output_dir)
            batch.clear()
```

## Batch Processing Patterns

### Pattern 1: Single Process Sequential (Development/Debugging)

```python
ocr = PaddleOCR()
for img_path in image_dir.glob("*.jpg"):
    result = ocr.predict(str(img_path))
```

**Use when:** Debugging, small batches (<10 images), accuracy testing

### Pattern 2: Multiprocess Queue (Production Batch)

```python
from multiprocessing import Manager, Process
from queue import Empty

def worker(task_queue, batch_size, output_dir):
    ocr = PaddleOCR()
    batch = []
    while True:
        try:
            batch.append(task_queue.get_nowait())
        except Empty:
            break
        if len(batch) == batch_size:
            ocr.predict(batch)
            batch.clear()
```

**Use when:** Production batch processing, multiple CPU cores available

### Pattern 3: Pipeline-Specific (Advanced)

For custom pipelines (e.g., PP-Structure for documents):

```python
from paddleocr import PaddleOCR

# Use specific pipeline class
ocr = PaddleOCR(pipeline='PP-Structure')
result = ocr.predict(image)
```

## Architecture for Lottery Ticket OCR

### Recommended Component Structure

```
ocr_batch_processor/
├── src/
│   ├── __init__.py
│   ├── pipeline.py          # PaddleOCR wrapper
│   ├── batch_orchestrator.py # Task queue, worker management
│   ├── result_parser.py      # Extract lottery fields from OCR results
│   └── output_exporter.py    # JSON/CSV export
├── models/                  # PaddleOCR models (downloaded at init)
├── output/                  # Processing results
└── main.py                  # Entry point
```

### Component Details

| Component | Input | Output | Dependencies |
|-----------|-------|--------|--------------|
| `pipeline.py` | Image path(s) | OCR result objects | PaddleOCR |
| `batch_orchestrator.py` | Image directory/ZIP | Task queue, worker processes | multiprocessing |
| `result_parser.py` | OCR result objects | Structured dict | None |
| `output_exporter.py` | Structured dict | JSON/CSV files | json, csv |

### Data Flow: Lottery Ticket Processing

```
1. File Discovery
   ZIP/directory → Extract to temp → Image list → Task queue

2. Batch OCR
   Image batch → PaddleOCR.predict() → Raw OCR results

3. Result Parsing
   Raw OCR results → Extract fields:
     - 期号 (draw number)
     - 投注时间 (bet time)
     - 投注内容 (bet content: 比赛, 选项, 赔率)
     - 金额 (amount)

4. Export
   Structured results → JSON/CSV file
```

## Build Order Implications

### Phase 1: Core OCR Pipeline
**Goal:** Single image processing working
**Dependencies:** None
**Key files:** `pipeline.py`

### Phase 2: Batch Orchestration
**Goal:** Multiple images processed in parallel
**Dependencies:** Phase 1
**Key files:** `batch_orchestrator.py`

### Phase 3: Result Parsing
**Goal:** Extract lottery-specific fields from OCR text
**Dependencies:** Phase 1
**Key files:** `result_parser.py`

### Phase 4: Output Export
**Goal:** Generate JSON/CSV output files
**Dependencies:** Phase 3
**Key files:** `output_exporter.py`

### Phase 5: Integration & CLI
**Goal:** End-to-end batch processing with file discovery
**Dependencies:** Phases 1-4
**Key files:** `main.py`

## Performance Considerations

| Concern | At 100 images | At 1K images | At 10K images |
|---------|----------------|---------------|---------------|
| CPU threads | 4 | 8 | 8-16 |
| Batch size | 6 | 6 | 6-12 |
| Workers | 2 | 4 | 4-8 |
| Memory | <2GB | <4GB | <8GB |
| Est. time | ~5 min | ~50 min | ~8 hours |

### CPU Optimization Parameters

```python
ocr = PaddleOCR(
    enable_mkldnn=True,        # Enable MKL-DNN acceleration
    cpu_threads=8,             # Match CPU core count
    rec_batch_num=6,           # Recognition batch size
)
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Loading Model Per Image
```python
# BAD - Model loading overhead per image
for img in images:
    ocr = PaddleOCR()  # Reload every time!
    result = ocr.predict(img)
```
**Instead:** Load once, predict many

### Anti-Pattern 2: Single Image Per predict() Call
```python
# BAD - Inefficient for batch processing
for img in images:
    result = ocr.predict([img])  # Batching is faster
```
**Instead:** Batch images when possible

### Anti-Pattern 3: Enabling Unused Preprocessors
```python
# BAD - Unnecessary overhead for lottery tickets
ocr = PaddleOCR(
    use_doc_orientation_classify=True,  # Not needed
    use_doc_unwarping=True,             # Not needed
)
```
**Instead:** Disable preprocessing for simple scanned documents

## Sources

- **HIGH:** [PaddleOCR Parallel Inference](https://github.com/paddlepaddle/paddleocr/blob/main/docs/version3.x/pipeline_usage/instructions/parallel_inference.en.md)
- **HIGH:** [PP-StructureV3 Pipeline Architecture](https://github.com/paddlepaddle/paddleocr/blob/main/docs/version3.x/pipeline_usage/PP-StructureV3.en.md)
- **HIGH:** [PaddleOCR Quick Start](https://github.com/paddlepaddle/paddleocr/blob/main/docs/quick_start.en.md)
- **HIGH:** [PP-DocTranslation OCR Pipeline](https://github.com/paddlepaddle/paddleocr/blob/main/docs/version3.x/pipeline_usage/PP-DocTranslation.en.md)
- **MEDIUM:** [Inference Optimization](https://github.com/paddlepaddle/paddleocr/blob/main/docs/version3.x/pipeline_usage/PaddleOCR-VL.en.md)

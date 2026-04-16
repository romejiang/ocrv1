# Plan 01-02 Summary: Single-Image OCR Pipeline

## Status: Completed

## Files Created/Modified

| File | Status | Changes |
|------|--------|---------|
| `src/preprocessing.py` | Created | 91 lines - Complete image preprocessing module |
| `src/pipeline.py` | Created | 105 lines - OCRPipeline class with CPU optimization |
| `src/__init__.py` | Created | 25 lines - Package exports |
| `tests/test_pipeline.py` | Created | 93 lines - Unit tests |

## Implementation Details

### `src/preprocessing.py`
Preprocessing functions implemented:
- `load_image(path)` - Load image via Pillow, convert to RGB
- `convert_to_grayscale(img)` - RGB to grayscale
- `denoise(img, strength=10)` - fastNlMeansDenoisingColored
- `binarize(img, method='otsu')` - Otsu or adaptive thresholding
- `correct_perspective(img, points)` - 4-point perspective transform
- `resize_keep_aspect(img, target_size=1280)` - Proportional scaling
- `preprocess_pipeline(image_path, ...)` - Full pipeline orchestrator

### `src/pipeline.py`
`OCRPipeline` class with:
- **CPU Optimization**: `enable_mkldnn=True`, `cpu_threads=8`
- **Detection**: `det_limit_side_len=640`, `det_limit_type='max'`
- **Recognition**: `rec_batch_num=6`
- `process(image_path, preprocess=True)` - Returns structured dict
- `process_to_json(image_path, output_path)` - Saves to JSON
- `main()` - CLI entry point

### Return Structure
```python
{
    'words': [{'text': str, 'confidence': float}, ...],
    'full_text': str,
    'regions': [{'bbox': [[x,y],...], 'text': str, 'confidence': float}, ...]
}
```

## Verification

```bash
# CLI usage
python -m src.pipeline <image_path> -o output.json

# Run tests
python -m pytest tests/test_pipeline.py -v
```

## Dependencies
- paddlepaddle (CPU)
- paddleocr
- opencv-python-headless
- pillow
- numpy

## Notes
- Uses `opencv-python-headless` (not opencv-python) for server compatibility
- MKL-DNN enabled for Intel CPU acceleration
- Multi-process mode (`use_mp`) not enabled at pipeline level (handled at batch level in Phase 2)
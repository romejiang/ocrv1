# Phase 3 Context: Lottery Parsing

**Phase:** 3 - Lottery Parsing
**Started:** 2026-04-16
**Status:** In Progress

## Phase Goal

从 OCR 文字中提取彩票专属字段（期号、投注内容、赔率、金额）

## Requirements Coverage

| Requirement | Description | Plan |
|-------------|-------------|------|
| LOT-01 | 期号识别与提取 | 03-01 |
| LOT-02 | 投注时间识别与提取 | 03-01 |
| LOT-03 | 投注金额识别与提取 | 03-01 |
| LOT-04 | 投注内容解析（比赛、选项） | 03-02 |
| LOT-05 | 赔率数字识别与提取 | 03-02 |
| LOT-06 | 多注识别（单张票面多个投注） | 03-02 |

## Input

Phase 3 输入是 `OCRPipeline.process()` 返回的结构化数据：

```python
{
    "words": [{"text": "...", "confidence": 0.95}, ...],
    "full_text": "第25042期\n2026-04-16\n投注金额：￥66\n...",
    "regions": [
        {"bbox": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]], "text": "...", "confidence": 0.95},
        ...
    ]
}
```

## Output

Phase 3 输出是彩票结构化数据：

```python
{
    "issue_number": "25042",      # LOT-01
    "bet_time": "2026-04-16",    # LOT-02
    "total_amount": 66.00,       # LOT-03
    "bets": [                    # LOT-04, LOT-05, LOT-06
        {
            "match": "阿根廷 vs 巴西",
            "option": "胜",
            "odds": 1.85
        },
        ...
    ]
}
```

## Key Decisions

### Pattern Matching Strategy

彩票票面文字有固定格式，采用正则表达式匹配：
- 期号: `第(\d+)期` 或 `期号[:：]?\s*(\d+)`
- 时间: `(\d{4}[-/]\d{2}[-/]\d{2})`
- 金额: `投注金额[:：]?\s*[￥$]?(\d+(?:\.\d{2})?)`
- 赔率: `(\d+\.\d{2})`

### 投注内容解析

彩票投注内容格式示例：
- `阿根廷 胜 1.85`
- `阿根廷 vs 巴西 主胜 1.85`
- `周一001 胜 1.85`

解析策略：
1. 先用正则提取赔率数值 (LOT-05)
2. 根据赔率位置推断选项和比赛
3. 比赛名称通常在赔率左侧
4. 选项（胜/平/负）在赔率附近

### 多注识别 (LOT-06)

单张彩票可能包含多注，识别策略：
1. 赔率数字出现多次 → 多注
2. 每注独立解析
3. 用位置信息区分不同注

## Dependencies

- Phase 1: `OCRPipeline` 提供 OCR 结果
- Phase 2: `BatchProcessor` 批量处理

## Risks

1. **版面变化**: 不同彩票公司格式不同，需支持多种格式
2. **文字识别错误**: OCR 置信度低时，正则匹配可能失败
3. **多注边界**: 多注之间边界可能不清晰

## Next Steps

1. 实现基础字段提取模块 (03-01)
2. 实现投注内容与赔率解析 (03-02)

---
*Context created: 2026-04-16*
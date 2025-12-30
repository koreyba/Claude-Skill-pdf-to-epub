---
title: Design - Structure Analyzer
description: Technical design for the structure detection engine (headings, footnotes, reading order).
priority: High
status: Draft
target_version: 1.0.0
---

# Design: Structure Analyzer

## 1. Architecture Overview

 The Structure Analyzer acts as a middleware between `PDFExtractor` (raw blocks) and `EPUBBuilder` (structured chapters). It operates on a stream of `TextBlocks` and progressively enriches them with semantic tagging.

### Data Flow
```mermaid
graph TD
    A[Raw TextBlocks] --> B[Reading Order Sorting]
    B --> C[Noise & Header/Footer Removal]
    C --> D[Heading Detection]
    D --> E[Semantic Tagging (Lists, Quotes)]
    E --> F[Footnote Extraction]
    F --> G[Hierarchical Tree Builder]
    G --> H[Structured EPUB Content]
```

## 2. Components

### 2.1 Reading Order (Sorter)
- **Input**: List of unsorted visual blocks.
- **Algorithms**:
    - **XY-Cut**: For complex/multi-column layouts (Recursive splitting).
    - **Top-Down Sort**: Simple Y-major sort for single column.
    - **Heuristic**: Detect dominant column boundaries to choose strategy.

### 2.2 Font Statistics Analyzer
- **Role**: Determine the "baseline" font (Body Text) by statistical frequency.
- **Output**: `style_map` (e.g., `{"Arial-12-Normal": "body", "Arial-16-Bold": "h1"}`).
- **Logic**: Most frequent font area = Body Text. Larger = Headings. Smaller = Footnotes.

### 2.3 Heading Detector
- **Logic**: Rule-based detection using `style_map`.
    - Group blocks by key `(font_size, font_name, is_bold)`.
    - Identify "outlier" fonts (larger/bolder than body text).
    - Assign levels (H1 = largest, H2 = second largest).
- **Config Interface**:
  ```json
  "heading_detection": {
    "overrides": {
        "h1": {"min_size": 18, "bold": true},
        "h2": {"min_size": 14, "bold": true}
    },
    "strategy": "statistical" // or "strict_rules"
  }
  ```

### 2.4 Footnote Processor
- **Detection**:
    - Look for superscripts or specific patterns (`[1]`, `*`) in body text.
    - Look for corresponding disconnected blocks at page bottom (or chapter end).
- **Linking**: Match markers. If ambiguous (two `*` on page), use geometric proximity (nearest Y).

## 3. Data Models

### SemanticBlock
```python
@dataclass
class SemanticBlock:
    raw_block: TextBlock
    role: str = "paragraph" # h1, h2, h3, footnote, list-item, quote
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict) # e.g., {"footnote_id": "fn-1"}
```

## 4. Key Algorithms

### Heading Hierarchy Construction
1. Identify all Potential Headings.
2. Sort them by visual weight (Size + Weight).
3. Map visual ranks to H1..H6.
4. Iterate through ordered blocks:
   - If Header found -> Start new Section.
   - Else -> Append to current Section.

## 5. Security & Performance
- **Performance**: Sorting is O(N log N). Classification is O(N). Extremely fast for <1000 pages.
- **Safety**: No external calls. Handle recursion depth limit for XY-Cut.

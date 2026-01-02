# Three-Layer Architecture

The PDF-to-EPUB converter uses a layered architecture that clearly separates code by modification policy.

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: FROZEN                                                │
│  ─────────────────────────────────────────────────────────────  │
│  Fixed specifications and deterministic algorithms.             │
│  NEVER modify these files.                                      │
│                                                                 │
│  Files:                                                         │
│  • core/epub_builder.py                                         │
│  • core/text_segmenter.py                                       │
│  • validation/*                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: CONFIGURABLE                                          │
│  ─────────────────────────────────────────────────────────────  │
│  Behavior controlled by configuration parameters.               │
│  ALWAYS try config changes first before touching code.          │
│                                                                 │
│  Parameters:                                                    │
│  • ConversionConfig                                             │
│  • HeadingConfig                                                │
│  • ImageOptimizationConfig                                      │
│  • etc.                                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: ADAPTABLE                                             │
│  ─────────────────────────────────────────────────────────────  │
│  Heuristics and strategies that may need tuning.                │
│  CAN modify if configuration doesn't solve the problem.         │
│                                                                 │
│  Files:                                                         │
│  • conversion/strategies/*                                      │
│  • detectors/structure_classifier.py                            │
│  • detectors/reading_order/*                                    │
│  • detectors/footnote_detector.py                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: FROZEN

### Why These Files Cannot Be Modified

| File | Reason |
|------|--------|
| `core/epub_builder.py` | Implements EPUB3 specification. The spec is external and fixed. Changing this breaks EPUB validity. |
| `core/text_segmenter.py` | Uses deterministic chunking (600 chars, 100 overlap). Validation depends on PDF and EPUB being segmented identically. Changing parameters breaks validation. |
| `validation/completeness_checker.py` | Calculates quality metrics. Changing the algorithm makes metrics incomparable across runs. |
| `validation/order_checker.py` | Uses LCS algorithm for order verification. Changing this invalidates historical comparisons. |
| `core/pdf_extractor.py` | PyMuPDF interface. Changes here affect all downstream processing. |

Note: `validation/validator.py` is an orchestration layer and can be modified without changing validation metrics.

### Exception Policy

Only modify FROZEN files if:
1. There's a **fundamental bug** (incorrect implementation of spec)
2. The **specification changes** (new EPUB version)
3. You have **explicit approval** and understand all downstream effects

### Code Markers

These files contain a comment at the top:

```python
# FROZEN: Do not modify - implements fixed specification
# See reference/architecture.md for explanation
```

---

## Layer 2: CONFIGURABLE

### Available Configuration Parameters

```python
@dataclass
class ConversionConfig:
    # Page selection
    page_ranges: PageRanges
    #   - skip: List[int] - pages to skip entirely (e.g., [1, 2] for title)
    #   - content: Tuple[int, int] - main content range (e.g., (3, -3))
    #   - endnotes: Tuple[int, int] - endnotes range (e.g., (-2, -1))

    # Region exclusion
    exclude_regions: ExcludeRegions
    #   - top: float - fraction of page height to exclude (0.05 = 5%)
    #   - bottom: float
    #   - left: float
    #   - right: float

    # Multi-column handling
    multi_column: MultiColumnConfig
    #   - enabled: bool
    #   - column_count: int (1, 2, or 3)
    #   - threshold: float - gap detection sensitivity (0.0-1.0)

    # Reading order algorithm
    reading_order_strategy: str  # "y_sort" or "xy_cut"

    # Heading detection
    heading_detection: HeadingConfig
    #   - font_size_threshold: float - multiplier vs body (1.2 = 20% larger)
    #   - max_heading_levels: int (1-6)

    # Footnote processing
    footnote_processing: FootnoteConfig
    #   - enabled: bool
    #   - patterns: List[str] - regex patterns to match
    #   - generate_backlinks: bool

    # Image handling
    image_optimization: ImageOptimizationConfig
    #   - enabled: bool
    #   - max_width: int (pixels)
    #   - max_height: int (pixels)
    #   - jpeg_quality: int (1-100)
    #   - convert_png_to_jpeg: bool

    # Book metadata
    metadata: BookMetadata
    #   - title: str
    #   - author: str
    #   - language: str (ISO 639-1, e.g., "en")
```

### When to Adjust Configuration

| Problem | Config Parameter | Suggested Change |
|---------|-----------------|------------------|
| Headers/footers in output | `exclude_regions.top/bottom` | Increase to 0.08 |
| Losing page numbers | `exclude_regions.bottom` | Decrease to 0.03 |
| Wrong column order | `reading_order_strategy` | Change to "xy_cut" |
| Columns not detected | `multi_column.threshold` | Decrease to 0.3 |
| Headings missed | `heading_detection.font_size_threshold` | Decrease to 1.1 |
| Images too large | `image_optimization.*` | Reduce max_width |
| Footnotes not linked | `footnote_processing.patterns` | Add custom pattern |

### How to Apply Configuration

```python
# From Python
config = ConversionConfig(
    reading_order_strategy="xy_cut",
    exclude_regions=ExcludeRegions(top=0.08),
    # ... other settings
)
converter.convert(pdf_path, epub_path, config)

# From JSON file
converter.convert(pdf_path, epub_path, config_path="config.json")
```

---

## Layer 3: ADAPTABLE

### Files That Can Be Modified

| File | What You Can Modify | When |
|------|---------------------|------|
| `conversion/strategies/simple_strategy.py` | Override methods for specific PDF types | Config doesn't handle edge case |
| `conversion/strategies/base_strategy.py` | Add new hook methods | Need new processing step |
| `detectors/structure_classifier.py` | Heading detection heuristics | Font patterns non-standard |
| `detectors/reading_order/y_sorter.py` | Sorting logic | Custom layout requirements |
| `detectors/reading_order/xy_cut_sorter.py` | Column detection | Complex multi-column |
| `detectors/footnote_detector.py` | Add patterns to PATTERNS dict | New footnote format |
| `detectors/endnote_formatter.py` | HTML output format | Custom styling needed |

### Code Markers

These files contain a comment at the top:

```python
# ADAPTABLE: Can be modified for specific PDF types
# See reference/code-adaptation.md for guidelines
```

### Modification Guidelines

1. **Create subclass when possible** - don't modify base class
2. **Add, don't replace** - add new patterns, don't remove existing
3. **Test after changes** - run `pytest tests/` to verify
4. **Document changes** - add comment explaining why

### Example: Adding Custom Strategy

```python
# In conversion/strategies/magazine_strategy.py (new file)

from .base_strategy import BaseStrategy

class MagazineStrategy(BaseStrategy):
    """Strategy for magazine-style PDFs with heavy image content."""

    def extract(self, pdf_path, config):
        # Custom extraction prioritizing images
        ...

    def order_blocks(self, blocks, config):
        # Always use xy_cut for magazines
        ...
```

Register in converter.py:
```python
STRATEGY_REGISTRY = {
    "simple": SimpleStrategy,
    "magazine": MagazineStrategy,  # Add this
}
```

---

## Decision Flow

When facing a conversion problem:

```
1. IDENTIFY the problem
   └─► Validation tells you: completeness? order? headings?

2. TRY CONFIGURATION (Layer 2)
   └─► Adjust relevant parameters
   └─► Re-run conversion
   └─► Re-validate
   └─► Repeat up to 2-3 times with different values

3. IF CONFIG FAILS → MODIFY CODE (Layer 3)
   └─► Identify which ADAPTABLE file to change
   └─► Make minimal change
   └─► Test thoroughly
   └─► Document the change

4. NEVER TOUCH FROZEN FILES (Layer 1)
   └─► If you think you need to, you're probably wrong
   └─► Ask for help instead
```

---

## Why This Architecture?

### Benefits

1. **Prevents breaking changes** - Core algorithms are protected
2. **Encourages configuration** - Most problems solvable without code
3. **Safe experimentation** - ADAPTABLE files are isolated
4. **Clear boundaries** - Easy to know what's safe to change
5. **Reproducible results** - FROZEN validation ensures consistency

### Trade-offs

1. **Some flexibility lost** - Can't customize core algorithms
2. **Learning curve** - Need to understand layer boundaries
3. **More files** - Separation adds complexity

The benefits outweigh the costs for a tool that needs to be reliable and maintainable.

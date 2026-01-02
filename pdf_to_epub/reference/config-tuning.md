# Configuration Tuning Guide

Complete reference for all configuration parameters.

## ConversionConfig Overview

```python
from conversion.models import (
    ConversionConfig,
    PageRanges,
    ExcludeRegions,
    MultiColumnConfig,
    HeadingConfig,
    FootnoteConfig,
    ImageOptimizationConfig,
    BookMetadata,
)

config = ConversionConfig(
    page_ranges=PageRanges(...),
    exclude_regions=ExcludeRegions(...),
    multi_column=MultiColumnConfig(...),
    reading_order_strategy="y_sort",
    heading_detection=HeadingConfig(...),
    footnote_processing=FootnoteConfig(...),
    image_optimization=ImageOptimizationConfig(...),
    metadata=BookMetadata(...),
)
```

---

## PageRanges

Controls which pages to process.

```python
@dataclass
class PageRanges:
    skip: List[int] = field(default_factory=list)
    content: Tuple[int, int] = (1, -1)
    endnotes: Optional[Tuple[int, int]] = None
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | List[int] | `[]` | Page numbers to skip entirely (1-indexed) |
| `content` | Tuple[int, int] | `(1, -1)` | Start and end pages for main content. Negative = from end. |
| `endnotes` | Tuple[int, int] or None | `None` | Page range for endnotes section |

### Examples

```python
# Skip title and copyright pages (1-2), content from 3 to third-from-last
PageRanges(
    skip=[1, 2],
    content=(3, -3),
    endnotes=(-2, -1)  # Last 2 pages are endnotes
)

# Process entire document
PageRanges(content=(1, -1))

# Skip specific pages (index, ads, etc.)
PageRanges(skip=[1, 2, 50, 51, 100])
```

---

## ExcludeRegions

Defines areas to exclude from each page (headers, footers, margins).

```python
@dataclass
class ExcludeRegions:
    top: float = 0.0
    bottom: float = 0.0
    left: float = 0.0
    right: float = 0.0
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `top` | float | `0.0` | Fraction of page height to exclude from top (0.05 = 5%) |
| `bottom` | float | `0.0` | Fraction of page height to exclude from bottom |
| `left` | float | `0.0` | Fraction of page width to exclude from left |
| `right` | float | `0.0` | Fraction of page width to exclude from right |

### Examples

```python
# Standard header/footer exclusion
ExcludeRegions(top=0.05, bottom=0.05)

# Aggressive exclusion for PDFs with large headers
ExcludeRegions(top=0.08, bottom=0.08)

# Side margins for bound books with gutter
ExcludeRegions(left=0.05, right=0.02)

# No exclusion (use all content)
ExcludeRegions()  # All zeros
```

### Tuning Tips

- Start with `0.05` (5%) for top/bottom
- If page numbers still appear → increase to `0.08`
- If content is cut off → decrease to `0.03`
- Visual inspection: Open PDF and measure header height as % of page

---

## MultiColumnConfig

Controls multi-column layout detection.

```python
@dataclass
class MultiColumnConfig:
    enabled: bool = False
    column_count: int = 1
    threshold: float = 0.4
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | bool | `False` | Enable column detection |
| `column_count` | int | `1` | Expected number of columns (1, 2, or 3) |
| `threshold` | float | `0.4` | Gap detection sensitivity (0.0-1.0). Lower = more sensitive. |

### Examples

```python
# Standard 2-column academic paper
MultiColumnConfig(enabled=True, column_count=2, threshold=0.4)

# Magazine with variable columns
MultiColumnConfig(enabled=True, threshold=0.3)

# Disable column detection (single column)
MultiColumnConfig(enabled=False)
```

### Tuning Tips

- If columns not detected: Lower threshold to `0.3`
- If false positives (seeing columns where there are none): Raise to `0.5`
- Set `column_count` if you know the exact layout

---

## reading_order_strategy

Selects the algorithm for ordering text blocks.

```python
reading_order_strategy: str = "y_sort"  # or "xy_cut"
```

### Options

| Value | Description | Use When |
|-------|-------------|----------|
| `"y_sort"` | Simple top-to-bottom, left-to-right | Single column documents |
| `"xy_cut"` | Recursive XY-cut algorithm | Multi-column, complex layouts |

### Examples

```python
# Fiction book (single column)
reading_order_strategy="y_sort"

# Academic paper (2 columns)
reading_order_strategy="xy_cut"

# Magazine with mixed layout
reading_order_strategy="xy_cut"
```

---

## HeadingConfig

Controls heading detection heuristics.

```python
@dataclass
class HeadingConfig:
    font_size_threshold: float = 1.2
    max_heading_levels: int = 3
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `font_size_threshold` | float | `1.2` | Font size multiplier vs body to consider as heading |
| `max_heading_levels` | int | `3` | Maximum heading depth (H1, H2, H3...) |

### Examples

```python
# Standard threshold (20% larger = heading)
HeadingConfig(font_size_threshold=1.2)

# Detect smaller headings (10% larger)
HeadingConfig(font_size_threshold=1.1)

# Only detect major headings (30% larger)
HeadingConfig(font_size_threshold=1.3)

# Limit to 2 heading levels
HeadingConfig(max_heading_levels=2)
```

### Tuning Tips

- If headings missed: Lower threshold to `1.1`
- If regular text marked as headings: Raise to `1.3`
- Check font size distribution in PDF to determine ideal threshold

---

## FootnoteConfig

Controls footnote/endnote processing.

```python
@dataclass
class FootnoteConfig:
    enabled: bool = False
    patterns: List[str] = field(default_factory=list)
    generate_backlinks: bool = True
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | bool | `False` | Enable footnote detection and linking |
| `patterns` | List[str] | `[]` | Additional regex patterns (beyond built-in) |
| `generate_backlinks` | bool | `True` | Generate links from endnotes back to references |

### Built-in Patterns

The detector automatically finds:
- `[1]`, `[12]` (bracket style)
- `(1)`, `(12)` (parenthesis style)
- `.1`, `.12` (period style)
- `word1`, `word12` (superscript-like)

### Examples

```python
# Enable with defaults
FootnoteConfig(enabled=True)

# Add custom pattern
FootnoteConfig(
    enabled=True,
    patterns=[r'\*(\d+)']  # Matches *1, *2, etc.
)

# No backlinks
FootnoteConfig(enabled=True, generate_backlinks=False)
```

---

## ImageOptimizationConfig

Controls image processing for EPUB.

```python
@dataclass
class ImageOptimizationConfig:
    enabled: bool = True
    max_width: int = 1200
    max_height: int = 1600
    jpeg_quality: int = 85
    convert_png_to_jpeg: bool = False
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | bool | `True` | Enable image optimization |
| `max_width` | int | `1200` | Maximum image width in pixels |
| `max_height` | int | `1600` | Maximum image height in pixels |
| `jpeg_quality` | int | `85` | JPEG compression quality (1-100) |
| `convert_png_to_jpeg` | bool | `False` | Convert PNG to JPEG (smaller files) |

### Examples

```python
# High quality (larger files)
ImageOptimizationConfig(
    max_width=1600,
    jpeg_quality=95
)

# Optimized for mobile (smaller files)
ImageOptimizationConfig(
    max_width=800,
    max_height=1000,
    jpeg_quality=75,
    convert_png_to_jpeg=True
)

# Disable optimization (keep original)
ImageOptimizationConfig(enabled=False)
```

### Tuning Tips

- E-reader screens are typically 1200x1600, larger images waste space
- JPEG quality 85 is visually lossless for most images
- `convert_png_to_jpeg=True` significantly reduces file size but loses transparency

---

## BookMetadata

Metadata for the EPUB file.

```python
@dataclass
class BookMetadata:
    title: Optional[str] = None
    author: Optional[str] = None
    language: str = "en"
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    description: Optional[str] = None
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | str or None | `None` | Book title. None = extract from PDF metadata. |
| `author` | str or None | `None` | Author name. None = extract from PDF. |
| `language` | str | `"en"` | ISO 639-1 language code |
| `publisher` | str or None | `None` | Publisher name |
| `isbn` | str or None | `None` | ISBN number |
| `description` | str or None | `None` | Book description |

### Examples

```python
# Auto-extract from PDF
BookMetadata()

# Override title and author
BookMetadata(
    title="My Book",
    author="John Doe"
)

# Full metadata
BookMetadata(
    title="Complete Guide",
    author="Jane Smith",
    language="en",
    publisher="Tech Books Inc",
    isbn="978-1234567890",
    description="A comprehensive guide to..."
)
```

---

## Complete Configuration Example

```python
config = ConversionConfig(
    page_ranges=PageRanges(
        skip=[1, 2],
        content=(3, -3),
        endnotes=(-2, -1)
    ),
    exclude_regions=ExcludeRegions(
        top=0.05,
        bottom=0.05
    ),
    multi_column=MultiColumnConfig(
        enabled=False
    ),
    reading_order_strategy="y_sort",
    heading_detection=HeadingConfig(
        font_size_threshold=1.2,
        max_heading_levels=3
    ),
    footnote_processing=FootnoteConfig(
        enabled=True,
        generate_backlinks=True
    ),
    image_optimization=ImageOptimizationConfig(
        enabled=True,
        max_width=1200,
        jpeg_quality=85
    ),
    metadata=BookMetadata(
        title="My Book",
        author="Author Name",
        language="en"
    )
)
```

---

## Loading from JSON

```json
{
  "page_ranges": {
    "skip": [1, 2],
    "content": [3, -3],
    "endnotes": [-2, -1]
  },
  "exclude_regions": {
    "top": 0.05,
    "bottom": 0.05
  },
  "reading_order_strategy": "y_sort",
  "heading_detection": {
    "font_size_threshold": 1.2
  },
  "image_optimization": {
    "enabled": true,
    "jpeg_quality": 85
  }
}
```

```python
import json
from conversion.models import ConversionConfig

with open("config.json") as f:
    data = json.load(f)
config = ConversionConfig(**data)
```

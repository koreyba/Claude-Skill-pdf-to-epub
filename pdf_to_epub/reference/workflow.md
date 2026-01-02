# PDF to EPUB Workflow

Complete guide for the 4-phase conversion process.

## Phase 1: Analyze PDF

### Goal
Understand the PDF structure before conversion to generate optimal configuration.

### Automated analysis (recommended)
Use the built-in analyzer to produce an analysis report and suggested config:

```bash
python -m scripts.analyze input.pdf --output analysis.json
```

```python
from conversion.pdf_analyzer import PDFAnalyzer

analyzer = PDFAnalyzer("input.pdf")
analysis = analyzer.analyze()
config = analyzer.generate_config()
```

### Steps

1. **Open PDF and get basic info**
```python
import fitz
doc = fitz.open("input.pdf")
print(f"Pages: {len(doc)}")
print(f"Title: {doc.metadata.get('title', 'Unknown')}")
print(f"Author: {doc.metadata.get('author', 'Unknown')}")
```

2. **Detect layout type**
```python
# Sample a few pages (e.g., pages 5, 10, 15)
for page_num in [5, 10, 15]:
    page = doc[page_num]
    blocks = page.get_text("dict")["blocks"]

    # Check x-coordinates of text blocks
    x_coords = [b["bbox"][0] for b in blocks if b["type"] == 0]

    # If blocks cluster at 2+ distinct x positions → multi-column
    if len(set(round(x/50)*50 for x in x_coords)) > 1:
        print(f"Page {page_num}: Multi-column detected")
```

3. **Check for images**
```python
total_images = 0
for page in doc:
    images = page.get_images()
    total_images += len(images)
print(f"Total images: {total_images}")
```

4. **Detect footnotes/endnotes**
```python
import re
# Look for patterns like [1], (1), superscript numbers
footnote_pattern = re.compile(r'\[\d{1,2}\]|\(\d{1,2}\)')
for page in doc:
    text = page.get_text()
    matches = footnote_pattern.findall(text)
    if matches:
        print(f"Footnote references found: {matches[:5]}")
        break
```

5. **Analyze font sizes**
```python
# Find dominant body font size
font_sizes = []
for page in doc[:10]:
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if block["type"] == 0:  # text block
            for line in block["lines"]:
                for span in line["spans"]:
                    font_sizes.append(span["size"])

from collections import Counter
body_size = Counter(font_sizes).most_common(1)[0][0]
print(f"Body font size: {body_size}")
```

### Output: Proposed Configuration

Based on analysis, generate a config:

```python
from conversion.models import (
    ConversionConfig, PageRanges, ExcludeRegions,
    HeadingConfig, ImageOptimizationConfig
)

config = ConversionConfig(
    page_ranges=PageRanges(
        skip=[1, 2],  # Skip title pages
        content=(3, -3),  # Main content
        endnotes=(-2, -1),  # Last 2 pages for endnotes
    ),
    exclude_regions=ExcludeRegions(
        top=0.05,  # 5% for headers
        bottom=0.05,  # 5% for footers/page numbers
    ),
    reading_order_strategy="y_sort",  # or "xy_cut" if multi-column
    heading_detection=HeadingConfig(
        font_size_threshold=1.2,  # 20% larger than body = heading
    ),
    image_optimization=ImageOptimizationConfig(
        enabled=True,
        max_width=1200,
        jpeg_quality=85,
    ),
)
```

### User Confirmation

Before proceeding, show the proposed config and ask:

> "I've analyzed the PDF. Here's my proposed configuration:
> - Reading order: Y-sort (single column)
> - Skip pages: 1-2 (title pages)
> - Image optimization: Enabled
>
> Does this look correct? Any adjustments needed?"

---

## Phase 2: Convert

### Goal
Apply configuration and build EPUB file.

### Steps

1. **Initialize converter**
```python
from conversion.converter import Converter

converter = Converter(strategy="simple")
```

2. **Run conversion**
```python
from pathlib import Path

result = converter.convert(
    pdf_path=Path("input.pdf"),
    output_path=Path("output.epub"),
    config=config
)
```

3. **Check result**
```python
print(f"Chapters: {len(result.content.chapters)}")
print(f"Images: {len(result.content.images)}")
print(f"Reading order confidence: {result.reading_order_confidence:.2f}")

# Warn if low confidence
if result.reading_order_confidence < 0.7:
    print("WARNING: Low confidence in reading order. Consider xy_cut strategy.")
```

### What Happens Internally

```
PDF → extract() → TextBlocks + Images + Metadata
                        ↓
        order_blocks() → OrderedBlocks + Confidence
                        ↓
        detect_structure() → Chapters
                        ↓
        EPUBBuilder.build() → EPUB File
```

---

## Phase 3: Validate

### Goal
Verify conversion quality meets thresholds.

### Steps

1. **Extract text from both files**
```python
from core.pdf_extractor import PDFExtractor
from core.epub_extractor import EPUBExtractor

pdf_text = PDFExtractor().extract_text(pdf_path)
epub_text = EPUBExtractor().extract_text(epub_path)
```

2. **Check completeness**
```python
from validation.completeness_checker import CompletenessChecker

checker = CompletenessChecker()
result = checker.check(pdf_text, epub_text)

print(f"Completeness: {result.score:.1%}")
print(f"PDF words: {result.source_word_count}")
print(f"EPUB words: {result.target_word_count}")
print(f"Loss: {result.loss_percentage:.1f}%")
```

3. **Check reading order**
```python
from validation.order_checker import OrderChecker
from core.text_segmenter import TextSegmenter

segmenter = TextSegmenter()
pdf_chunks = segmenter.segment(pdf_text)
epub_chunks = segmenter.segment(epub_text)

order_checker = OrderChecker()
result = order_checker.check(pdf_chunks, epub_chunks)

print(f"Order score: {result.score:.1%}")
```

### Quality Gates

| Metric | Threshold | Action if Failed |
|--------|-----------|------------------|
| Completeness | > 95% | Check exclude_regions, page_ranges |
| Order score | > 80% | Try xy_cut, check multi_column |
| Confidence | > 0.6 | Review warnings, may need manual check |

### Validation Report

```python
def print_validation_report(completeness, order, confidence):
    print("=" * 50)
    print("VALIDATION REPORT")
    print("=" * 50)

    # Completeness
    status = "PASS" if completeness.score > 0.95 else "FAIL"
    print(f"Completeness: {completeness.score:.1%} [{status}]")

    # Order
    status = "PASS" if order.score > 0.80 else "FAIL"
    print(f"Order score: {order.score:.1%} [{status}]")

    # Confidence
    status = "PASS" if confidence > 0.6 else "WARNING"
    print(f"Confidence: {confidence:.2f} [{status}]")

    print("=" * 50)
```

---

## Phase 4: Adapt (If Needed)

### Goal
Fix issues identified in validation.

### Decision Process

```
1. Identify the problem (completeness? order? headings?)
2. Try configuration change first (Layer 2)
3. If config doesn't help after 2-3 attempts → modify code (Layer 3)
4. Never modify FROZEN files (Layer 1)
```

### Example: Fixing Text Loss

```python
# Problem: 8% text loss (>5% threshold)

# Step 1: Check what's being cut
# Look at exclude_regions - maybe too aggressive?
config.exclude_regions.top = 0.03  # Reduce from 0.05

# Step 2: Re-run conversion
result = converter.convert(pdf_path, epub_path, config)

# Step 3: Re-validate
# If still failing, check page_ranges
config.page_ranges.skip = []  # Don't skip any pages

# Step 4: If still failing, investigate specific pages
# Use debug mode to see what's happening on each page
```

### Example: Fixing Reading Order

```python
# Problem: Order score 65% (<80% threshold)

# Step 1: Switch to xy_cut for column detection
config.reading_order_strategy = "xy_cut"

# Step 2: Re-run and validate
result = converter.convert(pdf_path, epub_path, config)

# Step 3: If still wrong, tune threshold
config.multi_column.threshold = 0.3  # More sensitive

# Step 4: If still failing, may need custom sorter
# See reference/code-adaptation.md
```

---

## Complete Example

```python
from pathlib import Path
from conversion.converter import Converter
from conversion.models import *
from validation.completeness_checker import CompletenessChecker
from validation.order_checker import OrderChecker

# Phase 1: Configure
config = ConversionConfig(
    page_ranges=PageRanges(skip=[1, 2], content=(3, -3)),
    exclude_regions=ExcludeRegions(top=0.05, bottom=0.05),
    reading_order_strategy="y_sort",
    image_optimization=ImageOptimizationConfig(enabled=True),
)

# Phase 2: Convert
converter = Converter(strategy="simple")
pdf_path = Path("book.pdf")
epub_path = Path("book.epub")

result = converter.convert(pdf_path, epub_path, config)
print(f"Confidence: {result.reading_order_confidence:.2f}")

# Phase 3: Validate
# ... (run completeness and order checks)

# Phase 4: Adapt if needed
if completeness.score < 0.95:
    config.exclude_regions.top = 0.03
    result = converter.convert(pdf_path, epub_path, config)
    # Re-validate...
```

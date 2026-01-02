# Troubleshooting Guide

Solutions for common PDF-to-EPUB conversion problems.

## Quick Reference Table

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| Text loss > 5% | Headers/footers cut | `exclude_regions.top: 0.03` |
| Wrong reading order | Multi-column PDF | `reading_order_strategy: "xy_cut"` |
| Headings as paragraphs | Font threshold too high | `heading_detection.font_size_threshold: 1.1` |
| Missing images | Images not extracted | Check PDF has embedded images |
| Huge EPUB file | Images not optimized | `image_optimization.enabled: true` |
| Footnotes not linked | Non-standard format | Add pattern to FootnoteDetector |
| Garbled text | PDF encoding issue | Check PDF quality |

---

## Text Loss Problems

### Symptom: Completeness < 95%

#### Cause 1: Aggressive header/footer exclusion

**Diagnosis:**
```python
# Check what's being excluded
config.exclude_regions.top = 0  # Disable temporarily
config.exclude_regions.bottom = 0
# Re-run and compare
```

**Fix:**
```python
# Reduce exclusion zone
exclude_regions=ExcludeRegions(
    top=0.03,   # Was 0.05
    bottom=0.03
)
```

#### Cause 2: Wrong page ranges

**Diagnosis:**
```python
# Are we skipping content pages?
print(f"Skipping pages: {config.page_ranges.skip}")
print(f"Content range: {config.page_ranges.content}")
```

**Fix:**
```python
# Don't skip any pages
page_ranges=PageRanges(
    skip=[],  # Empty - process all
    content=(1, -1)  # Full document
)
```

#### Cause 3: Text in images (scanned PDF)

**Diagnosis:**
```python
import fitz
doc = fitz.open("input.pdf")
page = doc[5]
text = page.get_text()
print(f"Text length: {len(text)}")  # If very short, PDF might be scanned
```

**Fix:**
This skill doesn't handle OCR. Use an OCR tool first to convert scanned PDF to searchable PDF.

---

## Reading Order Problems

### Symptom: Order score < 80%

#### Cause 1: Multi-column layout not detected

**Diagnosis:**
```python
# Check if PDF has multiple columns
import fitz
doc = fitz.open("input.pdf")
page = doc[5]
blocks = page.get_text("dict")["blocks"]
x_coords = [b["bbox"][0] for b in blocks if b["type"] == 0]
print(f"Unique X positions: {sorted(set(round(x/50)*50 for x in x_coords))}")
# If 2+ clusters → multi-column
```

**Fix:**
```python
# Enable column detection
reading_order_strategy="xy_cut",
multi_column=MultiColumnConfig(enabled=True, threshold=0.4)
```

#### Cause 2: Columns detected but wrong order

**Diagnosis:**
- Open the EPUB and check if left column is read before right
- If columns are read in wrong order, threshold might be wrong

**Fix:**
```python
# Make column detection more sensitive
multi_column=MultiColumnConfig(
    enabled=True,
    threshold=0.3  # Lower = more sensitive
)
```

#### Cause 3: Complex layout (sidebars, callouts)

**Diagnosis:**
- PDF has text boxes at various positions
- Not a clean column structure

**Fix:**
May need custom reading order algorithm. See [code-adaptation.md](code-adaptation.md).

---

## Heading Detection Problems

### Symptom: Headings rendered as regular paragraphs

#### Cause 1: Font size threshold too high

**Diagnosis:**
```python
# Check font sizes in PDF
import fitz
from collections import Counter

doc = fitz.open("input.pdf")
font_sizes = []
for page in doc[:10]:
    for block in page.get_text("dict")["blocks"]:
        if block["type"] == 0:
            for line in block["lines"]:
                for span in line["spans"]:
                    font_sizes.append(round(span["size"], 1))

counter = Counter(font_sizes)
print("Font sizes:", counter.most_common(10))
# Body is usually most common
# Headings should be 10-30% larger
```

**Fix:**
```python
# Lower threshold to detect smaller headings
heading_detection=HeadingConfig(
    font_size_threshold=1.1  # Was 1.2
)
```

#### Cause 2: Headings use different font, not size

**Diagnosis:**
- Headings are bold but same size as body
- Or headings use different font family

**Fix:**
Modify `structure_classifier.py` to consider font weight:

```python
# In _calculate_heading_score()
# Add check for bold flag
if block.flags & 16:  # Bold flag
    score += 0.3
    signals.append("bold +0.3")
```

---

## Image Problems

### Symptom: Missing images

**Diagnosis:**
```python
import fitz
doc = fitz.open("input.pdf")
for page_num, page in enumerate(doc):
    images = page.get_images()
    print(f"Page {page_num + 1}: {len(images)} images")
```

**Fix:**
If images exist in PDF but not in EPUB:
- Check if images are in excluded regions
- Verify extraction is working:

```python
from core.pdf_extractor import PDFExtractor
extractor = PDFExtractor()
_, images, _ = extractor.extract(pdf_path, config)
print(f"Extracted {len(images)} images")
```

### Symptom: EPUB file too large

**Fix:**
```python
image_optimization=ImageOptimizationConfig(
    enabled=True,
    max_width=800,      # Reduce from 1200
    max_height=1000,    # Reduce from 1600
    jpeg_quality=75,    # Reduce from 85
    convert_png_to_jpeg=True  # PNG → JPEG for photos
)
```

---

## Footnote Problems

### Symptom: Footnotes not converted to hyperlinks

#### Cause 1: Non-standard footnote format

**Diagnosis:**
```python
# Check what format is used
import fitz
doc = fitz.open("input.pdf")
text = doc[5].get_text()
print(text[:1000])
# Look for patterns: [1], (1), .1, word1, etc.
```

**Fix:**
Add pattern to FootnoteDetector:

```python
# In detectors/footnote_detector.py
PATTERNS = {
    'bracket': re.compile(r'\[(\d{1,2})\]'),
    'paren': re.compile(r'\((\d{1,2})\)'),
    'period': re.compile(r'(?<=\w)\.(\d{1,2})(?=\s|$)'),
    'superscript': re.compile(r'(?<=[a-zA-Z])(\d{1,2})(?=\s|$)'),
    # Add your custom pattern here:
    'custom': re.compile(r'your-pattern-here'),
}
```

#### Cause 2: Endnotes not detected

**Diagnosis:**
Check if endnotes are in expected page range:
```python
print(f"Endnotes range: {config.page_ranges.endnotes}")
```

**Fix:**
Adjust endnotes page range:
```python
page_ranges=PageRanges(
    endnotes=(-3, -1)  # Last 3 pages instead of 2
)
```

---

## Encoding Problems

### Symptom: Garbled or missing characters

**Diagnosis:**
```python
import fitz
doc = fitz.open("input.pdf")
text = doc[0].get_text()
print(repr(text[:500]))  # Check for weird characters
```

**Fix:**
This usually indicates a PDF with non-standard encoding or embedded fonts. Options:
1. Try different PDF extraction library
2. Pre-process PDF with tools like `pdf2pdf`
3. Accept some character loss if minor

---

## Performance Problems

### Symptom: Conversion takes too long

**Diagnosis:**
- Check PDF size and page count
- Check image count and size

**Fix:**
```python
# Process fewer pages for testing
page_ranges=PageRanges(
    content=(1, 20)  # First 20 pages only
)

# Reduce image quality (faster processing)
image_optimization=ImageOptimizationConfig(
    max_width=600,
    jpeg_quality=60
)
```

---

## Validation Failures

### Symptom: Validation script crashes

**Error:** `ModuleNotFoundError`
**Fix:** Install dependencies:
```bash
pip install pymupdf pdfplumber ebooklib lxml Pillow
```

**Error:** `FileNotFoundError`
**Fix:** Check file paths are correct and files exist.

**Error:** `PermissionError`
**Fix:** Close any programs that have the PDF/EPUB open.

---

## Still Stuck?

If none of the above solutions work:

1. **Check the test fixtures** - Look at `tests/integration/` for similar PDFs
2. **Enable debug logging** - Set `LOG_LEVEL=DEBUG` environment variable
3. **Examine intermediate output** - Check what each phase produces
4. **Simplify the problem** - Try converting just a few pages first
5. **Consider code adaptation** - See [code-adaptation.md](code-adaptation.md)

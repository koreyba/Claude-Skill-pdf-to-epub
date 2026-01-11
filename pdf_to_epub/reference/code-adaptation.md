# Code Adaptation Guide

When and how to modify ADAPTABLE code when configuration isn't enough.

## When to Modify Code

Only modify code when:

1. Configuration changes have been tried (2-3 attempts)
2. The problem is clearly in heuristics, not data
3. The required change is isolated to ADAPTABLE files

**Never modify FROZEN files** (see [architecture.md](architecture.md)).

---

## ADAPTABLE Files Reference

| File | Purpose | Common Modifications |
|------|---------|---------------------|
| `strategies/simple_strategy.py` | Main conversion logic | Add preprocessing steps |
| `strategies/base_strategy.py` | Template pattern | Add new hook methods |
| `detectors/structure_classifier.py` | Role detection | Tune heading heuristics |
| `detectors/reading_order/y_sorter.py` | Single-column ordering | Custom sort logic |
| `detectors/reading_order/xy_cut_sorter.py` | Multi-column ordering | Threshold adjustments |
| `detectors/footnote_detector.py` | Footnote patterns | Add new patterns |
| `detectors/endnote_formatter.py` | HTML output | Custom styling |

---

## Pattern 1: Adding a New Strategy

When the default `SimpleStrategy` doesn't work for a specific PDF type.

### Steps

1. Create new file in `strategies/`:

```python
# strategies/academic_strategy.py

from .base_strategy import BaseStrategy
from detectors.reading_order.xy_cut_sorter import XYCutSorter

class AcademicStrategy(BaseStrategy):
    """Strategy for academic papers with columns and citations."""

    def order_blocks(self, blocks, config):
        # Always use XY-cut for academic papers
        sorter = XYCutSorter()
        ordered, confidence = sorter.sort(blocks)
        return ordered, confidence

    def detect_structure(self, blocks, config, images, metadata):
        # Custom structure detection for academic format
        # ... your implementation
        pass
```

2. Register in `converter.py`:

```python
from .strategies.academic_strategy import AcademicStrategy

STRATEGY_REGISTRY = {
    "simple": SimpleStrategy,
    "academic": AcademicStrategy,  # Add this
}
```

3. Use the new strategy:

```python
converter = Converter(strategy="academic")
result = converter.convert(pdf_path, epub_path, config)
```

---

## Pattern 2: Adding a Footnote Pattern

When footnotes use a non-standard format.

### Steps

1. Identify the pattern in the PDF:

```python
import fitz
doc = fitz.open("input.pdf")
text = doc[5].get_text()
# Look for: †1, *1, ^1, etc.
```

2. Add pattern to `footnote_detector.py`:

```python
# In detectors/footnote_detector.py

PATTERNS = {
    'bracket': re.compile(r'\[(\d{1,2})\]'),
    'paren': re.compile(r'\((\d{1,2})\)'),
    'period': re.compile(r'(?<=\w)\.(\d{1,2})(?=\s|$)'),
    'superscript': re.compile(r'(?<=[a-zA-Z])(\d{1,2})(?=\s|$)'),
    # Add your pattern:
    'dagger': re.compile(r'†(\d{1,2})'),
    'asterisk': re.compile(r'\*(\d{1,2})'),
}
```

3. Test:

```python
from conversion.detectors.footnote_detector import FootnoteDetector

detector = FootnoteDetector(patterns=['dagger'])
refs = detector.find_references("This statement†1 is cited.")
print(refs)  # [FootnoteRef(number=1, original_text='†1', ...)]
```

---

## Pattern 3: Tuning Heading Detection

When the default heuristics don't identify headings correctly.

### Steps

1. Understand the current scoring in `structure_classifier.py`:

```python
def _calculate_heading_score(self, block, prev, next_b, body_size, body_flags):
    score = 0.0
    signals = []

    # Font size check
    if block.font_size > body_size * self.heading_threshold:
        score += 0.4
        signals.append(f"font_size +0.4")

    # Bold check
    if block.flags & 16:  # Bold flag
        score += 0.2
        signals.append("bold +0.2")

    # Short text (headings are usually short)
    if len(block.text) < 100:
        score += 0.1
        signals.append("short +0.1")

    # ... more signals
    return score, signals
```

2. Add new signals or adjust weights:

```python
def _calculate_heading_score(self, block, prev, next_b, body_size, body_flags):
    score = 0.0
    signals = []

    # Existing checks...

    # NEW: Check for all-caps (common heading style)
    if block.text.isupper() and len(block.text) < 50:
        score += 0.3
        signals.append("all_caps +0.3")

    # NEW: Check for centered text (approximate)
    page_center = 0.5  # Assume page center
    block_center = (block.x0 + block.x1) / 2 / page_width
    if abs(block_center - page_center) < 0.1:
        score += 0.15
        signals.append("centered +0.15")

    return score, signals
```

3. Test with debug output:

```python
classifier = StructureClassifier()
blocks = classifier.classify(text_blocks)

for block in blocks:
    if block.score > 0:
        print(f"{block.role}: {block.original_block.text[:50]}")
        print(f"  Score: {block.score}, Signals: {block.debug_signals}")
```

---

## Pattern 4: Custom Reading Order

When neither `y_sort` nor `xy_cut` produces correct order.

### Steps

1. Create new sorter in `reading_order/`:

```python
# detectors/reading_order/custom_sorter.py

from .base import BlockSorter

class CustomSorter(BlockSorter):
    """Custom reading order for specific layout type."""

    def sort(self, blocks):
        # Your custom sorting logic
        # Example: Sort by sections first, then by position within section

        sections = self._detect_sections(blocks)
        ordered = []

        for section in sections:
            # Sort blocks within section by y, then x
            section_blocks = sorted(
                [b for b in blocks if self._in_section(b, section)],
                key=lambda b: (b.y0, b.x0)
            )
            ordered.extend(section_blocks)

        confidence = self._calculate_confidence(ordered)
        return ordered, confidence

    def _detect_sections(self, blocks):
        # Detect logical sections (e.g., by horizontal lines)
        ...

    def _in_section(self, block, section):
        # Check if block belongs to section
        ...

    def _calculate_confidence(self, ordered):
        # Estimate confidence in ordering
        return 0.85
```

2. Register sorter:

```python
# In simple_strategy.py or base_strategy.py
from .detectors.reading_order.custom_sorter import CustomSorter

def order_blocks(self, blocks, config):
    if config.reading_order_strategy == "custom":
        sorter = CustomSorter()
    elif config.reading_order_strategy == "xy_cut":
        sorter = XYCutSorter()
    else:
        sorter = YSorter()

    return sorter.sort(blocks)
```

---

## Pattern 5: Modifying HTML Output

When EPUB styling needs customization.

### EndnoteFormatter Customization

```python
# In detectors/endnote_formatter.py

class EndnoteFormatter:
    def format_endnotes(self, blocks):
        html_parts = []

        for block in blocks:
            if block.role != "endnote":
                continue

            num = block.endnote_num
            content = self._extract_content(block)

            # Customize the HTML output:
            html_parts.append(
                f'<div class="endnote" id="note{num}">'
                f'  <span class="endnote-number">{num}</span>'
                f'  <span class="endnote-text">{content}</span>'
                f'</div>'
            )

        return '\n'.join(html_parts)
```

### EPUBBuilder Stylesheet

To modify default styles, edit `core/epub_builder.py`:

```python
def _write_stylesheet(self, temp_path):
    css = '''
    /* Custom styles */
    .endnote {
        margin: 1em 0;
        padding-left: 2em;
        text-indent: -2em;
    }

    .endnote-number {
        font-weight: bold;
        color: #0066cc;
    }
    '''
    # ... write to file
```

**Note:** `epub_builder.py` is technically FROZEN, but stylesheet changes are cosmetic and safe.

---

## Testing Your Changes

After any code modification:

1. Run unit tests:
```bash
python -m pytest tests/ -v
```

2. Run specific test file:
```bash
python -m pytest tests/conversion/test_structure_classifier.py -v
```

3. Test on real PDF:
```bash
python -m scripts.convert input.pdf output.epub
python -m scripts.validate input.pdf output.epub
```

4. Verify validation passes:
```
Completeness: > 95%
Order score: > 80%
```

---

## Documenting Changes

When you modify code:

1. Add comment explaining the change:
```python
# MODIFIED: Added all-caps heading detection for Book XYZ
# Original threshold was insufficient for this PDF style
if block.text.isupper():
    score += 0.3
```

2. Update tests if behavior changes
3. Consider if change should be configurable instead

---

## Rollback Strategy

If changes break things:

1. Git revert:
```bash
git checkout -- path/to/file.py
```

2. Or restore from known good state:
```bash
git stash
python -m pytest tests/  # Verify tests pass
git stash pop  # Re-apply changes
```

---

## When to Ask for Help

If you're unsure about a change:
- It affects multiple files
- It changes fundamental algorithms
- Tests start failing
- You need to modify FROZEN files

Stop and reconsider the approach. Often there's a configuration solution that was missed.

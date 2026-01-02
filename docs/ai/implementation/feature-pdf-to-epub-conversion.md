---
phase: implementation
title: PDF to EPUB Conversion - Implementation
description: Technical implementation guide and code patterns
feature: pdf-to-epub-conversion
---

# Implementation Guide

## Code Patterns

### Pattern 1: Strategy Registration
**Use Case:** Dynamically select strategy by name

```python
# pdf_to_epub/conversion/strategies/__init__.py
from .base_strategy import BaseStrategy
from .simple_strategy import SimpleStrategy

STRATEGY_REGISTRY = {
    "simple": SimpleStrategy,
    # Future: "academic": AcademicStrategy,
}

def get_strategy(name: str) -> BaseStrategy:
    if name not in STRATEGY_REGISTRY:
        raise ValueError(f"Unknown strategy: {name}. Available: {list(STRATEGY_REGISTRY.keys())}")
    return STRATEGY_REGISTRY[name]()
```

### Pattern 2: Config Defaults with Metadata
**Use Case:** Provide sensible defaults for conversion config

```python
# pdf_to_epub/conversion/models.py
DEFAULT_CONFIG = ConversionConfig(
    page_ranges=PageRanges(skip=[1, 2], content=(3, -3), endnotes=(-2, -1)),
    exclude_regions=ExcludeRegions(top=0.05, bottom=0.05, left=0.0, right=0.0),
    multi_column=MultiColumnConfig(enabled=False, column_count=1, threshold=0.4),
    reading_order_strategy="y_sort",
    heading_detection=HeadingConfig(font_size_threshold=1.2),
    footnote_processing=FootnoteConfig(enabled=False),
    metadata=BookMetadata(title=None, author=None, language="en"),  # None = extract from PDF
)

def load_config(config_path: Path = None) -> ConversionConfig:
    if config_path is None:
        return DEFAULT_CONFIG
    
    with open(config_path) as f:
        data = json.load(f)
    
    # Merge with defaults
    merged = {**asdict(DEFAULT_CONFIG), **data}
    return ConversionConfig(**merged)

def validate_config(config: ConversionConfig) -> None:
    """Validate config immediately (fail-fast). Raise ValueError if invalid."""
    # Validate exclude_regions (must be 0.0-1.0)
    for field in ['top', 'bottom', 'left', 'right']:
        value = getattr(config.exclude_regions, field)
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"exclude_regions.{field} must be 0.0-1.0, got {value}")
    
    # Validate reading_order_strategy
    allowed_strategies = ["y_sort", "xy_cut", "column_based"]
    if config.reading_order_strategy not in allowed_strategies:
        raise ValueError(f"reading_order_strategy must be one of {allowed_strategies}")
    
    # Validate language code (basic check)
    if len(config.metadata.language) != 2:
        raise ValueError(f"metadata.language must be 2-letter ISO 639-1 code, got '{config.metadata.language}'")
```

### Pattern 3: Error Context Preservation
**Use Case:** Capture errors with step context for debugging

```python
# pdf_to_epub/conversion/converter.py
def convert(self, pdf_path: Path, output_path: Path, config: ConversionConfig = None) -> ConversionResult:
    log = ConversionLog(timestamp=datetime.now(), strategy_used=self.strategy_name, config=config)
    
    try:
        log.steps_completed.append("loading_config")
        config = config or load_config()
        
        log.steps_completed.append("extracting")
        content = self.strategy.convert(pdf_path, config)
        
        log.steps_completed.append("building_epub")
        epub_path = self.epub_builder.build(content, output_path)
        
        return ConversionResult(epub_path=epub_path, status="success", log=log)
    
    except Exception as e:
        log.errors.append(f"{log.steps_completed[-1]}: {str(e)}")
        return ConversionResult(epub_path=None, status="failed", log=log)
```

## Integration Points

### Integration 1: PDFExtractor (core/pdf_extractor.py)
**Method:** `extract_text_blocks(pdf_path, exclude_regions=None) -> List[TextBlock]`
**Usage in SimpleStrategy:**
```python
def extract(self, pdf_path: Path, config: ConversionConfig) -> Tuple[List[TextBlock], List[ImageResource], BookMetadata]:
    from pdf_to_epub.core.pdf_extractor import PDFExtractor
    import fitz  # PyMuPDF
    
    extractor = PDFExtractor()
    
    # Extract text blocks
    blocks = extractor.extract_text_blocks(
        pdf_path,
        exclude_regions={
            "top": config.exclude_regions.top,
            "bottom": config.exclude_regions.bottom,
            "left": config.exclude_regions.left,
            "right": config.exclude_regions.right,
        }
    )
    
    # Extract images
    images = []
    doc = fitz.open(pdf_path)
    for page_num, page in enumerate(doc):
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            images.append(ImageResource(
                id=f"img-page-{page_num+1}-{img_index+1}",
                filename=f"image{len(images)+1:03d}.{base_image['ext']}",
                data=base_image["image"],
                format=base_image["ext"],
                width=base_image["width"],
                height=base_image["height"],
                page_num=page_num + 1
            ))
    
    # Extract metadata
    pdf_meta = doc.metadata or {}
    metadata = BookMetadata(
        title=pdf_meta.get('title') or config.metadata.title or "Unknown",
        author=pdf_meta.get('author') or config.metadata.author or "Unknown",
        language=config.metadata.language or "en",
        publisher=pdf_meta.get('producer'),
        isbn=None,  # ISBN typically not in PDF metadata
        description=pdf_meta.get('subject')
    )
    doc.close()
    
    return blocks, images, metadata
```

### Integration 2: Reading Order Sorters
**Method:** `sort(blocks) -> Tuple[List[TextBlock], float]`
**Usage:**
```python
def order_blocks(self, blocks: List[TextBlock], config: ConversionConfig) -> Tuple[List[TextBlock], float]:
    if config.reading_order_strategy == "y_sort":
        from pdf_to_epub.detectors.reading_order.y_sorter import YSorter
        sorter = YSorter()
    elif config.reading_order_strategy == "xy_cut":
        from pdf_to_epub.detectors.reading_order.xy_cut_sorter import XYCutSorter
        sorter = XYCutSorter()
    
    ordered, confidence = sorter.sort(blocks)
    return ordered, confidence
```

### Integration 3: Structure Detection
**Methods:**
- `FontAnalyzer.analyze_fonts(blocks) -> FontProfile`
- `StructureClassifier.classify(blocks, font_profile) -> List[ClassifiedBlock]`
- `StructureBuilder.build_structure(classified_blocks) -> StructuredContent`

**Usage:**
```python
def detect_structure(self, blocks: List[TextBlock], config: ConversionConfig) -> StructuredContent:
    from pdf_to_epub.detectors.font_analyzer import FontAnalyzer
    from pdf_to_epub.detectors.structure_classifier import StructureClassifier
    from pdf_to_epub.detectors.structure_builder import StructureBuilder
    
    # Step 1: Analyze fonts to identify headings
    font_analyzer = FontAnalyzer()
    font_profile = font_analyzer.analyze_fonts(blocks)
    
    # Step 2: Classify each block as heading or paragraph
    classifier = StructureClassifier()
    classified = classifier.classify(blocks, font_profile)
    
    # Step 3: Group into chapters
    builder = StructureBuilder()
    structured = builder.build_structure(classified)
    
    return structured
```

## EPUB Generation Details

### Image Extraction from PDF
```python
import fitz  # PyMuPDF

def extract_images_from_pdf(pdf_path: Path) -> List[ImageResource]:
    """
    Extract all images from PDF pages.
    Returns list of ImageResource objects with binary data.
    """
    images = []
    doc = fitz.open(pdf_path)
    
    for page_num, page in enumerate(doc, start=1):
        # Get all images on this page
        image_list = page.get_images(full=True)
        
        for img_index, img in enumerate(image_list, start=1):
            xref = img[0]  # Image reference number
            base_image = doc.extract_image(xref)
            
            # Create ImageResource
            images.append(ImageResource(
                id=f"img-page-{page_num}-{img_index}",
                filename=f"image{len(images)+1:03d}.{base_image['ext']}",
                data=base_image["image"],
                format=base_image["ext"],  # "png", "jpeg", "gif"
                width=base_image["width"],
                height=base_image["height"],
                page_num=page_num
            ))
    
    doc.close()
    return images
```

### EPUB Directory Structure
```
temp_dir/
├── mimetype                  # "application/epub+zip"
├── META-INF/
│   └── container.xml         # Points to content.opf
└── OEBPS/
    ├── content.opf           # Package metadata
    ├── toc.ncx               # Navigation
    ├── stylesheet.css        # Basic styles
    ├── chapter1.xhtml
    ├── chapter2.xhtml
    └── ...
```

### content.opf Template
```xml
<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">{uuid}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:language>{language}</dc:language>
    <dc:publisher>{publisher}</dc:publisher>  <!-- if available -->
    <dc:description>{description}</dc:description>  <!-- if available -->
    <meta property="dcterms:modified">{timestamp}</meta>
  </metadata>
  
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="css" href="stylesheet.css" media-type="text/css"/>
    {chapter_items}
    {image_items}  <!-- e.g., <item id="img001" href="images/image001.png" media-type="image/png"/> -->
  </manifest>
  
  <spine toc="ncx">
    {chapter_refs}
  </spine>
</package>
```

### Chapter XHTML Template
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>{chapter_title}</title>
  <link rel="stylesheet" href="stylesheet.css"/>
</head>
<body>
  <section epub:type="chapter">
    <h1>{chapter_title}</h1>
    {paragraphs}
  </section>
</body>
</html>
```

### ZIP Packaging Code
```python
import zipfile
from pathlib import Path

def package_epub(temp_dir: Path, output_path: Path):
    """Package EPUB directory as ZIP file."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as epub:
        # mimetype MUST be first and uncompressed
        epub.write(temp_dir / 'mimetype', 'mimetype', compress_type=zipfile.ZIP_STORED)
        
        # Add all other files
        for file_path in temp_dir.rglob('*'):
            if file_path.is_file() and file_path.name != 'mimetype':
                arcname = file_path.relative_to(temp_dir)
                epub.write(file_path, arcname, compress_type=zipfile.ZIP_DEFLATED)
```

## Configuration Schema

### Example conversion_config.json
```json
{
  "page_ranges": {
    "skip": [1, 2],
    "content": [3, -3],
    "endnotes": [-2, -1]
  },
  "exclude_regions": {
    "top": 0.05,
    "bottom": 0.05,
    "left": 0.0,
    "right": 0.0
  },
  "multi_column": {
    "enabled": false,
    "column_count": 1,
    "threshold": 0.4
  },
  "reading_order_strategy": "y_sort",
  "heading_detection": {
    "font_size_threshold": 1.2
  },
  "footnote_processing": {
    "enabled": false
  },
  "metadata": {
    "title": null,
    "author": null,
    "language": "en"
  }
}
```
**Note:** `null` values for title/author mean "extract from PDF metadata".

### Config Validation Rules
- `page_ranges.skip` must be list of integers
- `exclude_regions` values must be 0.0-1.0 (percentages)
- `reading_order_strategy` must be "y_sort", "xy_cut", or "column_based"
- `metadata.language` must be valid 2-letter ISO 639-1 code ("en", "ru", "fr", etc.)
- `metadata.title` and `metadata.author` can be `null` (extract from PDF) or string

**Validation is performed immediately in Converter.__init__() before conversion starts (fail-fast).**

## Error Handling

### Common Errors and Solutions

#### Error 1: Encrypted PDF
```python
# Detection
import fitz
try:
    doc = fitz.open(pdf_path)
    if doc.is_encrypted:
        raise ValueError("PDF is encrypted. Please decrypt before conversion.")
except Exception as e:
    raise
```

#### Error 2: No Text Extracted
```python
# Detection in SimpleStrategy.extract()
blocks = extractor.extract_text_blocks(pdf_path)
if not blocks:
    raise ValueError("No text blocks extracted. PDF may be image-based.")
```

#### Error 3: No Chapters Detected
```python
# Handling in SimpleStrategy.detect_structure()
structured = builder.build_structure(classified)
if not structured.chapters:
    # Create single chapter with all content
    structured.chapters = [Chapter(
        title="Content",
        level=1,
        content="\n".join(block.text for block in classified),
        footnotes=[]
    )]
```

#### Error 4: Invalid EPUB
```python
# Validation after build
import subprocess
result = subprocess.run(['epubcheck', str(epub_path)], capture_output=True)
if result.returncode != 0:
    warnings.append(f"EPUB validation warnings: {result.stderr.decode()}")
```

## Testing Utilities

### Fixture Helper: Create Mock StructuredContent
```python
# tests/fixtures/content_factory.py
def create_test_content(num_chapters: int = 3) -> StructuredContent:
    chapters = []
    for i in range(1, num_chapters + 1):
        chapters.append(Chapter(
            title=f"Chapter {i}",
            level=1,
            content=f"<p>This is chapter {i} content.</p>",
            footnotes=[]
        ))
    
    return StructuredContent(
        chapters=chapters,
        metadata=BookMetadata(title="Test Book", author="Test Author", language="en"),
        reading_order_confidence=1.0
    )
```

### Test Helper: Validate EPUB Structure
```python
# tests/helpers/epub_validator.py
import zipfile
from pathlib import Path

def validate_epub_structure(epub_path: Path) -> bool:
    """Check basic EPUB structure is valid."""
    with zipfile.ZipFile(epub_path, 'r') as epub:
        files = epub.namelist()
        
        # Check required files
        assert 'mimetype' in files
        assert 'META-INF/container.xml' in files
        assert 'OEBPS/content.opf' in files
        
        # Check mimetype is first and uncompressed
        assert files[0] == 'mimetype'
        info = epub.getinfo('mimetype')
        assert info.compress_type == zipfile.ZIP_STORED
        
        return True
```

## Performance Considerations

### Optimization 1: Lazy Loading
**Issue:** Loading entire PDF into memory
**Solution:** Process page-by-page
```python
def extract(self, pdf_path: Path, config: ConversionConfig) -> List[TextBlock]:
    blocks = []
    doc = fitz.open(pdf_path)
    
    for page_num in range(doc.page_count):
        page = doc[page_num]
        page_blocks = self._extract_page_blocks(page, config)
        blocks.extend(page_blocks)
        page = None  # Free memory
    
    doc.close()
    return blocks
```

### Optimization 2: Avoid String Concatenation in Loops
**Issue:** Building HTML with += in loops
**Solution:** Use list and join
```python
# Bad
content = ""
for para in paragraphs:
    content += f"<p>{para}</p>\n"

# Good
parts = [f"<p>{para}</p>" for para in paragraphs]
content = "\n".join(parts)
```

## Deployment Notes

### CLI Usage Examples
```bash
# Analyze PDF structure
python -m pdf_to_epub.scripts.analyze --pdf book.pdf --output analysis.json

# Convert with defaults
python -m pdf_to_epub.scripts.convert --pdf book.pdf --output book.epub

# Convert with custom config
python -m pdf_to_epub.scripts.convert --pdf book.pdf --output book.epub --config my_config.json

# Validate conversion
python -m pdf_to_epub.scripts.validate --pdf book.pdf --epub book.epub
```

### Environment Variables
```bash
# Optional: Set default strategy
export pdf_to_epub_STRATEGY=simple

# Optional: Enable debug logging
export pdf_to_epub_DEBUG=1
```

## Known Limitations

1. **Table Support:** Tables are extracted as plain text, not preserved as tables
2. **Math Equations:** LaTeX or MathML equations are not supported
3. **Multi-Column Detection:** Config supports it, but SimpleStrategy does not implement (uses YSorter only)
4. **Footnote Processing:** Config has flag, but SimpleStrategy does not link footnotes to references
5. **Image Positioning:** Images are extracted but original page positions may not be preserved in EPUB layout

## Future Enhancements

### Enhancement 1: AcademicStrategy
- Use XY-cut reading order
- Detect and link footnotes/endnotes
- Preserve table structure
- Extract citations

### Enhancement 2: Advanced Image Handling
- Preserve original image positions in EPUB layout
- Support SVG and other vector formats
- Image compression/optimization options
- Extract image alt-text from PDF (if available)

### Enhancement 3: Stylesheet Customization
- Allow custom CSS in config
- Support different themes (serif, sans-serif, night mode)
- Responsive font sizing

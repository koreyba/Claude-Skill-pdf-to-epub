---
phase: testing
title: PDF to EPUB Conversion - Testing
description: Test strategy and test cases for conversion pipeline
feature: pdf-to-epub-conversion
---

# Testing Strategy

## Testing Overview
This document defines the testing strategy for the PDF to EPUB conversion feature (Phase 5), targeting **100% code coverage** for critical paths and **80%+ overall coverage**.

## Test Pyramid

```
        /\
       /  \
      / E2E \ (5 tests)
     /______\
    /        \
   / Integr.  \ (15 tests)
  /____________\
 /              \
/  Unit Tests    \ (60 tests)
\________________/
```

**Distribution:**
- **Unit Tests (60):** Test individual components in isolation
- **Integration Tests (15):** Test component interactions
- **End-to-End Tests (5):** Test full PDF → EPUB → Validation workflow

## Test Environment

### Test Fixtures
```
tests/fixtures/
├── pdfs/
│   ├── simple_fiction.pdf          # 3 chapters, single column
│   ├── academic_with_endnotes.pdf  # Chapters + endnotes section
│   ├── multi_column.pdf            # 2-column layout
│   └── encrypted.pdf               # Test error handling
├── configs/
│   ├── default_config.json
│   ├── academic_config.json
│   └── multi_column_config.json
└── expected_outputs/
    ├── simple_fiction_structure.json
    └── simple_fiction_chapters.json
```

### Setup/Teardown
```python
# tests/conftest.py
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def temp_output_dir():
    """Temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def simple_pdf():
    """Path to simple fiction test PDF."""
    return Path(__file__).parent / 'fixtures' / 'pdfs' / 'simple_fiction.pdf'

@pytest.fixture
def default_config():
    """Load default conversion config."""
    from claude_skill.conversion.models import load_config
    config_path = Path(__file__).parent / 'fixtures' / 'configs' / 'default_config.json'
    return load_config(config_path)
```

## Unit Tests

### Test Suite 1: BaseStrategy (tests/conversion/test_base_strategy.py)

#### Test 1.1: Cannot instantiate abstract class
```python
def test_base_strategy_is_abstract():
    """BaseStrategy cannot be instantiated directly."""
    from claude_skill.conversion.strategies.base_strategy import BaseStrategy
    
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        BaseStrategy()
```

#### Test 1.2: Template method calls hooks in order
```python
def test_template_method_calls_hooks():
    """convert() calls extract, order, detect in sequence."""
    from claude_skill.conversion.strategies.base_strategy import BaseStrategy
    
    class MockStrategy(BaseStrategy):
        def __init__(self):
            self.calls = []
        
        def extract(self, pdf_path, config):
            self.calls.append('extract')
            return []
        
        def order_blocks(self, blocks, config):
            self.calls.append('order')
            return [], 1.0
        
        def detect_structure(self, blocks, config):
            self.calls.append('detect')
            from claude_skill.conversion.models import StructuredContent
            return StructuredContent(chapters=[], metadata=None, reading_order_confidence=1.0)
    
    strategy = MockStrategy()
    strategy.convert(Path('dummy.pdf'), None)
    
    assert strategy.calls == ['extract', 'order', 'detect']
```

### Test Suite 2: SimpleStrategy (tests/conversion/test_simple_strategy.py)

#### Test 2.1: Extract calls PDFExtractor
```python
def test_extract_calls_pdf_extractor(mocker, simple_pdf, default_config):
    """extract() uses PDFExtractor with correct parameters."""
    from claude_skill.conversion.strategies.simple_strategy import SimpleStrategy
    
    mock_extractor = mocker.patch('claude_skill.conversion.strategies.simple_strategy.PDFExtractor')
    mock_extractor.return_value.extract_text_blocks.return_value = []
    
    strategy = SimpleStrategy()
    blocks, images, metadata = strategy.extract(simple_pdf, default_config)
    
    mock_extractor.assert_called_once()
    mock_extractor.return_value.extract_text_blocks.assert_called_once()
    assert isinstance(metadata, BookMetadata)
```

#### Test 2.1b: Extract metadata from PDF
```python
def test_extract_metadata_from_pdf(simple_pdf, default_config):
    """extract() reads title and author from PDF info dict."""
    from claude_skill.conversion.strategies.simple_strategy import SimpleStrategy
    
    strategy = SimpleStrategy()
    blocks, images, metadata = strategy.extract(simple_pdf, default_config)
    
    # Check metadata extracted (or fallback to config/Unknown)
    assert metadata.title is not None
    assert metadata.author is not None
    assert metadata.language == "en"  # From config
```

#### Test 2.1c: Extract images from PDF
```python
def test_extract_images_from_pdf(simple_pdf, default_config):
    """extract() extracts images with metadata."""
    from claude_skill.conversion.strategies.simple_strategy import SimpleStrategy
    
    strategy = SimpleStrategy()
    blocks, images, metadata = strategy.extract(simple_pdf, default_config)
    
    # Check images extracted
    for img in images:
        assert img.id.startswith('img-page-')
        assert img.format in ['png', 'jpeg', 'jpg', 'gif']
        assert img.width > 0
        assert img.height > 0
        assert len(img.data) > 0
```

#### Test 2.2: Order blocks uses YSorter
```python
def test_order_blocks_uses_y_sorter(mocker, default_config):
    """order_blocks() uses YSorter for single-column."""
    from claude_skill.conversion.strategies.simple_strategy import SimpleStrategy
    from claude_skill.core.models import TextBlock
    
    blocks = [
        TextBlock(text="B", bbox=(0, 100, 100, 120)),
        TextBlock(text="A", bbox=(0, 0, 100, 20)),
    ]
    
    strategy = SimpleStrategy()
    ordered, confidence = strategy.order_blocks(blocks, default_config)
    
    assert ordered[0].text == "A"  # Top block first
    assert ordered[1].text == "B"
    assert confidence == 1.0
```

#### Test 2.3: Detect structure uses existing components
```python
def test_detect_structure_pipeline(mocker, default_config):
    """detect_structure() calls FontAnalyzer → Classifier → Builder."""
    from claude_skill.conversion.strategies.simple_strategy import SimpleStrategy
    
    mock_analyzer = mocker.patch('claude_skill.conversion.strategies.simple_strategy.FontAnalyzer')
    mock_classifier = mocker.patch('claude_skill.conversion.strategies.simple_strategy.StructureClassifier')
    mock_builder = mocker.patch('claude_skill.conversion.strategies.simple_strategy.StructureBuilder')
    
    # Mock return values
    mock_analyzer.return_value.analyze_fonts.return_value = None
    mock_classifier.return_value.classify.return_value = []
    mock_builder.return_value.build_structure.return_value = mocker.Mock()
    
    strategy = SimpleStrategy()
    strategy.detect_structure([], default_config)
    
    mock_analyzer.return_value.analyze_fonts.assert_called_once()
    mock_classifier.return_value.classify.assert_called_once()
    mock_builder.return_value.build_structure.assert_called_once()
```

### Test Suite 3: EPUBBuilder (tests/core/test_epub_builder.py)

#### Test 3.1: Creates valid directory structure
```python
def test_epub_directory_structure(temp_output_dir):
    """EPUBBuilder creates correct directory structure."""
    from claude_skill.core.epub_builder import EPUBBuilder
    from tests.fixtures.content_factory import create_test_content
    
    builder = EPUBBuilder()
    content = create_test_content(num_chapters=3)
    epub_path = temp_output_dir / 'test.epub'
    
    builder.build(content, epub_path)
    
    # Validate EPUB structure
    import zipfile
    with zipfile.ZipFile(epub_path, 'r') as epub:
        files = epub.namelist()
        assert 'mimetype' in files
        assert 'META-INF/container.xml' in files
        assert 'OEBPS/content.opf' in files
        assert 'OEBPS/toc.ncx' in files
        assert any('chapter' in f for f in files)
```

#### Test 3.2: Mimetype is first and uncompressed
```python
def test_mimetype_format(temp_output_dir):
    """mimetype is first file and stored uncompressed."""
    from claude_skill.core.epub_builder import EPUBBuilder
    from tests.fixtures.content_factory import create_test_content
    
    builder = EPUBBuilder()
    epub_path = temp_output_dir / 'test.epub'
    builder.build(create_test_content(), epub_path)
    
    import zipfile
    with zipfile.ZipFile(epub_path, 'r') as epub:
        files = epub.namelist()
        assert files[0] == 'mimetype'
        
        info = epub.getinfo('mimetype')
        assert info.compress_type == zipfile.ZIP_STORED
        
        content = epub.read('mimetype').decode()
        assert content == 'application/epub+zip'
```

#### Test 3.3: Generates valid XHTML
```python
def test_chapter_xhtml_validity(temp_output_dir):
    """Chapter XHTML files are well-formed."""
    from claude_skill.core.epub_builder import EPUBBuilder
    from tests.fixtures.content_factory import create_test_content
    from lxml import etree
    
    builder = EPUBBuilder()
    epub_path = temp_output_dir / 'test.epub'
    builder.build(create_test_content(num_chapters=2), epub_path)
    
    import zipfile
    with zipfile.ZipFile(epub_path, 'r') as epub:
        chapter1 = epub.read('OEBPS/chapter1.xhtml')
        
        # Parse with lxml to validate well-formedness
        tree = etree.fromstring(chapter1)
        assert tree.tag.endswith('html')
        
        # Check for chapter title
        h1 = tree.xpath('//h1')[0]
        assert 'Chapter 1' in h1.text
```

#### Test 3.4: Escapes HTML entities
```python
def test_html_entity_escaping(temp_output_dir):
    """Special characters are escaped in XHTML."""
    from claude_skill.core.epub_builder import EPUBBuilder
    from claude_skill.conversion.models import StructuredContent, Chapter, BookMetadata
    
    content = StructuredContent(
        chapters=[Chapter(
            title="Test & Title",
            level=1,
            content="<p>Quote: \"Hello\" & <goodbye></p>",
            footnotes=[]
        )],
        metadata=BookMetadata(title="Test", author="Test", language="en"),
        reading_order_confidence=1.0,
        images=[]
    )
    
    builder = EPUBBuilder()
    epub_path = temp_output_dir / 'test.epub'
    builder.build(content, epub_path)
    
    import zipfile
    with zipfile.ZipFile(epub_path, 'r') as epub:
        chapter = epub.read('OEBPS/chapter1.xhtml').decode()
        assert '&amp;' in chapter
        assert '&quot;' in chapter or '&#34;' in chapter
        assert '&lt;' in chapter or '&#60;' in chapter
```

#### Test 3.5: Includes images in EPUB
```python
def test_images_in_epub(temp_output_dir):
    """EPUBBuilder saves images and references them in XHTML."""
    from claude_skill.core.epub_builder import EPUBBuilder
    from claude_skill.conversion.models import StructuredContent, Chapter, BookMetadata, ImageResource
    
    # Create fake image
    fake_image_data = b'\x89PNG\r\n\x1a\n'  # PNG header
    
    content = StructuredContent(
        chapters=[Chapter(title="Ch 1", level=1, content="<p>Text</p>", footnotes=[])],
        metadata=BookMetadata(title="Test", author="Test", language="en"),
        reading_order_confidence=1.0,
        images=[ImageResource(
            id="img-page-1-1",
            filename="image001.png",
            data=fake_image_data,
            format="png",
            width=100,
            height=100,
            page_num=1
        )]
    )
    
    builder = EPUBBuilder()
    epub_path = temp_output_dir / 'test.epub'
    builder.build(content, epub_path)
    
    import zipfile
    with zipfile.ZipFile(epub_path, 'r') as epub:
        # Check image file exists
        assert 'OEBPS/images/image001.png' in epub.namelist()
        
        # Check content.opf includes image
        opf = epub.read('OEBPS/content.opf').decode()
        assert 'image001.png' in opf
        assert 'media-type="image/png"' in opf
```

#### Test 3.6: Extracts metadata to content.opf
```python
def test_metadata_in_content_opf(temp_output_dir):
    """EPUBBuilder includes metadata in content.opf."""
    from claude_skill.core.epub_builder import EPUBBuilder
    from tests.fixtures.content_factory import create_test_content
    from claude_skill.conversion.models import BookMetadata
    
    content = create_test_content()
    content.metadata = BookMetadata(
        title="My Book Title",
        author="Jane Doe",
        language="ru",
        publisher="Test Publisher",
        isbn="978-0-123456-78-9",
        description="A test book"
    )
    
    builder = EPUBBuilder()
    epub_path = temp_output_dir / 'test.epub'
    builder.build(content, epub_path)
    
    import zipfile
    with zipfile.ZipFile(epub_path, 'r') as epub:
        opf = epub.read('OEBPS/content.opf').decode()
        assert '<dc:title>My Book Title</dc:title>' in opf
        assert '<dc:creator>Jane Doe</dc:creator>' in opf
        assert '<dc:language>ru</dc:language>' in opf
        assert 'Test Publisher' in opf
        assert '978-0-123456-78-9' in opf or 'A test book' in opf
```

### Test Suite 4: Converter (tests/conversion/test_converter.py)

#### Test 4.1: Loads config from file
```python
def test_load_config_from_file(tmp_path):
    """Converter loads and validates config from JSON."""
    import json
    from claude_skill.conversion.converter import Converter
    
    config_data = {
        "metadata": {"title": "Custom Title", "author": "Author", "language": "en"}
    }
    config_path = tmp_path / 'config.json'
    config_path.write_text(json.dumps(config_data))
    
    converter = Converter()
    result = converter.convert(
        pdf_path=Path('dummy.pdf'),
        output_path=Path('output.epub'),
        config_path=config_path
    )
    
    assert result.log.config.metadata.title == "Custom Title"
```

#### Test 4.2: Handles unknown strategy
```python
def test_unknown_strategy_error():
    """Converter raises error for unknown strategy."""
    from claude_skill.conversion.converter import Converter
    
    with pytest.raises(ValueError, match="Unknown strategy"):
        Converter(strategy="nonexistent")
```

#### Test 4.3: Returns failed result on error
```python
def test_error_returns_failed_result(mocker):
    """Converter returns ConversionResult with status=failed on error."""
    from claude_skill.conversion.converter import Converter
    
    # Mock strategy to raise error
    mocker.patch(
        'claude_skill.conversion.strategies.simple_strategy.SimpleStrategy.convert',
        side_effect=Exception("Test error")
    )
    
    converter = Converter(strategy="simple")
    result = converter.convert(Path('dummy.pdf'), Path('output.epub'))
    
    assert result.status == "failed"
    assert "Test error" in result.log.errors[0]
```

#### Test 4.4: Logs all steps
```python
def test_conversion_log_includes_steps(mocker, simple_pdf, temp_output_dir):
    """ConversionLog includes all completed steps."""
    from claude_skill.conversion.converter import Converter
    
    # Mock successful conversion
    mocker.patch('claude_skill.conversion.strategies.simple_strategy.SimpleStrategy.convert')
    mocker.patch('claude_skill.core.epub_builder.EPUBBuilder.build')
    
    converter = Converter(strategy="simple")
    result = converter.convert(simple_pdf, temp_output_dir / 'test.epub')
    
    assert "loading_config" in result.log.steps_completed
    assert "extracting" in result.log.steps_completed
    assert "building_epub" in result.log.steps_completed
```

#### Test 4.5: Config validation (fail-fast)
```python
def test_config_validation_fail_fast():
    """Invalid config raises ValueError immediately."""
    from claude_skill.conversion.models import ConversionConfig, ExcludeRegions, BookMetadata
    from claude_skill.conversion.converter import Converter
    
    # Invalid exclude_regions (>1.0)
    bad_config = ConversionConfig(
        exclude_regions=ExcludeRegions(top=1.5, bottom=0.0, left=0.0, right=0.0),
        metadata=BookMetadata(title="Test", author="Test", language="en")
    )
    
    with pytest.raises(ValueError, match="exclude_regions.top"):
        Converter(config=bad_config)
```

#### Test 4.6: Config validation - invalid strategy
```python
def test_invalid_reading_order_strategy():
    """Invalid reading_order_strategy raises ValueError."""
    from claude_skill.conversion.models import ConversionConfig, BookMetadata
    from claude_skill.conversion.converter import Converter
    
    bad_config = ConversionConfig(
        reading_order_strategy="invalid_strategy",
        metadata=BookMetadata(title="Test", author="Test", language="en")
    )
    
    with pytest.raises(ValueError, match="reading_order_strategy"):
        Converter(config=bad_config)
```

#### Test 4.7: Config validation - invalid language code
```python
def test_invalid_language_code():
    """Invalid language code raises ValueError."""
    from claude_skill.conversion.models import ConversionConfig, BookMetadata
    from claude_skill.conversion.converter import Converter
    
    bad_config = ConversionConfig(
        metadata=BookMetadata(title="Test", author="Test", language="english")  # Should be "en"
    )
    
    with pytest.raises(ValueError, match="language"):
        Converter(config=bad_config)
```

## Integration Tests

### Test Suite 5: End-to-End Conversion (tests/integration/test_conversion_pipeline.py)

#### Test 5.1: Convert simple fiction PDF
```python
def test_convert_simple_pdf_to_epub(simple_pdf, temp_output_dir, default_config):
    """Full conversion of simple PDF to valid EPUB."""
    from claude_skill.conversion.converter import Converter
    
    converter = Converter(strategy="simple")
    result = converter.convert(
        pdf_path=simple_pdf,
        output_path=temp_output_dir / 'output.epub',
        config=default_config
    )
    
    assert result.status == "success"
    assert result.epub_path.exists()
    assert result.reading_order_confidence >= 0.9
```

#### Test 5.2: Validate EPUB passes completeness check
```python
def test_converted_epub_passes_validation(simple_pdf, temp_output_dir, default_config):
    """Converted EPUB passes completeness and order validation."""
    from claude_skill.conversion.converter import Converter
    from claude_skill.validation.completeness_checker import CompletenessChecker
    from claude_skill.validation.order_checker import OrderChecker
    
    # Convert
    converter = Converter()
    result = converter.convert(simple_pdf, temp_output_dir / 'output.epub', default_config)
    
    # Validate completeness
    completeness = CompletenessChecker()
    comp_result = completeness.check(simple_pdf, result.epub_path)
    assert comp_result.is_complete
    assert comp_result.completeness_score >= 0.995  # 99.5%+ from requirements
    
    # Validate order
    order = OrderChecker()
    order_result = order.check(simple_pdf, result.epub_path)
    assert order_result.is_correct
```

#### Test 5.3: Config override works
```python
def test_config_override(simple_pdf, temp_output_dir):
    """Config parameters are applied during conversion."""
    from claude_skill.conversion.converter import Converter
    from claude_skill.conversion.models import ConversionConfig, BookMetadata
    
    config = ConversionConfig(
        metadata=BookMetadata(title="Override Title", author="Test Author", language="fr")
    )
    
    converter = Converter()
    result = converter.convert(simple_pdf, temp_output_dir / 'output.epub', config)
    
    # Check metadata in EPUB
    import zipfile
    with zipfile.ZipFile(result.epub_path, 'r') as epub:
        opf = epub.read('OEBPS/content.opf').decode()
        assert 'Override Title' in opf
        assert 'Test Author' in opf
        assert '<dc:language>fr</dc:language>' in opf
```

### Test Suite 6: CLI Scripts (tests/scripts/test_cli.py)

#### Test 6.1: convert.py creates EPUB
```python
def test_convert_cli(simple_pdf, temp_output_dir, monkeypatch):
    """convert.py CLI creates EPUB file."""
    import sys
    from claude_skill.scripts import convert
    
    output_path = temp_output_dir / 'output.epub'
    monkeypatch.setattr(sys, 'argv', [
        'convert.py',
        '--pdf', str(simple_pdf),
        '--output', str(output_path)
    ])
    
    convert.main()
    
    assert output_path.exists()
```

#### Test 6.2: validate.py runs checks
```python
def test_validate_cli(simple_pdf, temp_output_dir, monkeypatch, capsys):
    """validate.py CLI runs validation checks."""
    import sys
    from claude_skill.scripts import convert, validate
    
    # First convert
    epub_path = temp_output_dir / 'test.epub'
    monkeypatch.setattr(sys, 'argv', [
        'convert.py', '--pdf', str(simple_pdf), '--output', str(epub_path)
    ])
    convert.main()
    
    # Then validate
    monkeypatch.setattr(sys, 'argv', [
        'validate.py', '--pdf', str(simple_pdf), '--epub', str(epub_path)
    ])
    validate.main()
    
    captured = capsys.readouterr()
    assert 'Completeness:' in captured.out
    assert 'Order:' in captured.out
```

## Edge Cases & Error Handling

### Test Suite 7: Error Scenarios (tests/conversion/test_error_handling.py)

#### Test 7.1: Encrypted PDF
```python
def test_encrypted_pdf_error():
    """Encrypted PDF raises clear error."""
    from claude_skill.conversion.converter import Converter
    
    encrypted_pdf = Path('tests/fixtures/pdfs/encrypted.pdf')
    converter = Converter()
    result = converter.convert(encrypted_pdf, Path('output.epub'))
    
    assert result.status == "failed"
    assert "encrypted" in result.log.errors[0].lower()
```

#### Test 7.2: No text extracted
```python
def test_image_only_pdf_error(mocker):
    """PDF with no text raises error."""
    from claude_skill.conversion.converter import Converter
    
    # Mock extractor to return empty list
    mocker.patch(
        'claude_skill.core.pdf_extractor.PDFExtractor.extract_text_blocks',
        return_value=[]
    )
    
    converter = Converter()
    result = converter.convert(Path('dummy.pdf'), Path('output.epub'))
    
    assert result.status == "failed"
    assert "no text" in result.log.errors[0].lower()
```

#### Test 7.3: Invalid config JSON
```python
def test_invalid_config_json(tmp_path):
    """Invalid JSON config raises error."""
    from claude_skill.conversion.models import load_config
    
    config_path = tmp_path / 'bad.json'
    config_path.write_text("{ invalid json }")
    
    with pytest.raises(json.JSONDecodeError):
        load_config(config_path)
```

## Test Coverage Targets

### Critical Paths (100% coverage required)
- [x] BaseStrategy template method flow
- [x] Converter error handling and logging
- [x] EPUBBuilder EPUB structure creation
- [x] Config validation

### Standard Paths (80%+ coverage required)
- [x] SimpleStrategy extraction/ordering/detection
- [x] CLI argument parsing
- [x] Data model serialization

### Acceptable Gaps (<80% coverage)
- Debug print statements
- Type checking branches (if TYPE_CHECKING)
- Exception message formatting

## Test Execution

### Run All Tests
```bash
pytest tests/ -v --cov=claude_skill.conversion --cov=claude_skill.core.epub_builder
```

### Run Specific Suite
```bash
pytest tests/conversion/test_simple_strategy.py -v
```

### Coverage Report
```bash
pytest --cov=claude_skill.conversion --cov-report=html
open htmlcov/index.html
```

## CI/CD Integration

### GitHub Actions Workflow
```yaml
name: Test Conversion Feature
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      - run: pip install -e .[dev]
      - run: pytest tests/ --cov --cov-fail-under=80
```

## Test Maintenance

### Adding New Strategy
When adding new strategy (e.g., AcademicStrategy):
1. Copy `test_simple_strategy.py` → `test_academic_strategy.py`
2. Update test fixtures with academic PDF
3. Add integration test for academic-specific features
4. Update coverage targets

### Updating Data Models
When changing StructuredContent:
1. Update `content_factory.py` helper
2. Update serialization tests
3. Check all integration tests still pass

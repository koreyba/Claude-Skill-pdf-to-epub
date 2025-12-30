"""Test suite for conversion data models."""

import pytest
from datetime import datetime
from pathlib import Path

from claude_skill.conversion.models import (
    PageRanges,
    ExcludeRegions,
    MultiColumnConfig,
    HeadingConfig,
    FootnoteConfig,
    BookMetadata,
    ImageResource,
    Footnote,
    Chapter,
    StructuredContent,
    ConversionLog,
    ConversionResult,
    ConversionConfig,
)


class TestPageRanges:
    """Test PageRanges dataclass."""
    
    def test_default_values(self):
        """PageRanges has correct defaults."""
        pr = PageRanges()
        assert pr.skip == []
        assert pr.content == (1, -1)
        assert pr.endnotes == (-1, -1)
    
    def test_custom_values(self):
        """PageRanges accepts custom values."""
        pr = PageRanges(skip=[1, 2, 3], content=(4, 100), endnotes=(101, 110))
        assert pr.skip == [1, 2, 3]
        assert pr.content == (4, 100)
        assert pr.endnotes == (101, 110)


class TestExcludeRegions:
    """Test ExcludeRegions dataclass."""
    
    def test_default_values(self):
        """ExcludeRegions defaults to zero."""
        er = ExcludeRegions()
        assert er.top == 0.0
        assert er.bottom == 0.0
        assert er.left == 0.0
        assert er.right == 0.0
    
    def test_custom_values(self):
        """ExcludeRegions accepts custom percentages."""
        er = ExcludeRegions(top=0.1, bottom=0.1, left=0.05, right=0.05)
        assert er.top == 0.1
        assert er.bottom == 0.1


class TestMultiColumnConfig:
    """Test MultiColumnConfig dataclass."""
    
    def test_defaults_to_single_column(self):
        """MultiColumnConfig defaults to disabled."""
        mc = MultiColumnConfig()
        assert mc.enabled is False
        assert mc.column_count == 1
        assert mc.threshold == 0.4


class TestBookMetadata:
    """Test BookMetadata dataclass."""
    
    def test_valid_metadata(self):
        """BookMetadata accepts valid values."""
        meta = BookMetadata(
            title="Test Book",
            author="Test Author",
            language="en",
            publisher="Publisher",
            isbn="1234567890",
            description="A test book"
        )
        assert meta.title == "Test Book"
        assert meta.author == "Test Author"
        assert meta.language == "en"
    
    def test_allows_none_for_title_and_author(self):
        """BookMetadata allows None for title and author (PDF extraction)."""
        meta = BookMetadata(title=None, author=None, language="en")
        assert meta.title is None
        assert meta.author is None
    
    def test_rejects_empty_string_title(self):
        """BookMetadata rejects empty string for title."""
        with pytest.raises(ValueError, match="Title cannot be empty string"):
            BookMetadata(title="", author="Author", language="en")
    
    def test_rejects_empty_string_author(self):
        """BookMetadata rejects empty string for author."""
        with pytest.raises(ValueError, match="Author cannot be empty string"):
            BookMetadata(title="Title", author="  ", language="en")
    
    def test_rejects_invalid_language_code(self):
        """BookMetadata requires 2-letter ISO 639-1 code."""
        with pytest.raises(ValueError, match="2-letter ISO 639-1 code"):
            BookMetadata(title="Title", author="Author", language="eng")
    
    def test_to_dict_from_dict_roundtrip(self):
        """BookMetadata serialization roundtrip."""
        original = BookMetadata(
            title="Book",
            author="Author",
            language="ru",
            isbn="123"
        )
        
        data = original.to_dict()
        restored = BookMetadata.from_dict(data)
        
        assert restored.title == original.title
        assert restored.author == original.author
        assert restored.language == original.language


class TestImageResource:
    """Test ImageResource dataclass."""
    
    def test_valid_image(self):
        """ImageResource accepts valid image data."""
        img = ImageResource(
            id="img-1",
            filename="test.png",
            data=b"imagedata",
            format="png",
            width=640,
            height=480,
            page_num=1
        )
        assert img.id == "img-1"
        assert img.width == 640
    
    def test_rejects_invalid_format(self):
        """ImageResource rejects unsupported formats."""
        with pytest.raises(ValueError, match="Unsupported image format"):
            ImageResource(
                id="img-1",
                filename="test.bmp",
                data=b"data",
                format="bmp",
                width=100,
                height=100,
                page_num=1
            )
    
    def test_rejects_negative_dimensions(self):
        """ImageResource requires positive dimensions."""
        with pytest.raises(ValueError, match="dimensions must be positive"):
            ImageResource(
                id="img-1",
                filename="test.png",
                data=b"data",
                format="png",
                width=-100,
                height=100,
                page_num=1
            )
    
    def test_to_dict_excludes_binary_data(self):
        """ImageResource.to_dict() doesn't include full binary data."""
        img = ImageResource(
            id="img-1",
            filename="test.png",
            data=b"x" * 10000,
            format="png",
            width=100,
            height=100,
            page_num=1
        )
        
        data = img.to_dict()
        assert "bytes" in str(data['data'])
        assert len(str(data['data'])) < 100  # Shortened representation


class TestChapter:
    """Test Chapter dataclass."""
    
    def test_valid_chapter(self):
        """Chapter accepts valid data."""
        ch = Chapter(
            title="Chapter 1",
            level=1,
            content="<p>Content</p>",
            footnotes=[]
        )
        assert ch.title == "Chapter 1"
        assert ch.level == 1
    
    def test_rejects_invalid_level(self):
        """Chapter level must be 1-3."""
        with pytest.raises(ValueError, match="level must be 1-3"):
            Chapter(title="Test", level=4, content="", footnotes=[])
    
    def test_to_dict_from_dict_roundtrip(self):
        """Chapter serialization roundtrip."""
        footnote = Footnote(marker="1", id="fn-1", text="Note")
        original = Chapter(
            title="Ch1",
            level=2,
            content="<p>Text</p>",
            footnotes=[footnote]
        )
        
        data = original.to_dict()
        restored = Chapter.from_dict(data)
        
        assert restored.title == original.title
        assert len(restored.footnotes) == 1


class TestStructuredContent:
    """Test StructuredContent dataclass."""
    
    def test_valid_content(self):
        """StructuredContent accepts valid data."""
        meta = BookMetadata(title="Book", author="Author", language="en")
        ch = Chapter(title="Ch1", level=1, content="<p>text</p>", footnotes=[])
        
        content = StructuredContent(
            chapters=[ch],
            metadata=meta,
            reading_order_confidence=0.95,
            images=[]
        )
        
        assert len(content.chapters) == 1
        assert content.reading_order_confidence == 0.95
    
    def test_rejects_invalid_confidence(self):
        """StructuredContent confidence must be 0.0-1.0."""
        meta = BookMetadata(title="Book", author="Author", language="en")
        
        with pytest.raises(ValueError, match="Confidence must be 0.0-1.0"):
            StructuredContent(
                chapters=[],
                metadata=meta,
                reading_order_confidence=1.5,
                images=[]
            )


class TestConversionResult:
    """Test ConversionResult dataclass."""
    
    def test_valid_result(self):
        """ConversionResult accepts valid data."""
        log = ConversionLog(
            timestamp=datetime.now(),
            strategy_used="simple",
            config={}
        )
        
        result = ConversionResult(
            epub_path=Path("output.epub"),
            status="success",
            reading_order_confidence=0.9,
            log=log
        )
        
        assert result.status == "success"
        assert result.epub_path == Path("output.epub")
    
    def test_rejects_invalid_status(self):
        """ConversionResult status must be valid enum."""
        log = ConversionLog(
            timestamp=datetime.now(),
            strategy_used="simple",
            config={}
        )
        
        with pytest.raises(ValueError, match="Invalid status"):
            ConversionResult(
                epub_path=Path("out.epub"),
                status="invalid",
                reading_order_confidence=0.9,
                log=log
            )
    
    def test_accepts_none_epub_path_on_failure(self):
        """ConversionResult allows None epub_path when failed."""
        log = ConversionLog(
            timestamp=datetime.now(),
            strategy_used="simple",
            config={}
        )
        
        result = ConversionResult(
            epub_path=None,
            status="failed",
            reading_order_confidence=0.0,
            log=log
        )
        
        assert result.epub_path is None


class TestConversionConfig:
    """Test ConversionConfig dataclass."""
    
    def test_valid_config(self):
        """ConversionConfig accepts valid configuration."""
        config = ConversionConfig(
            page_ranges=PageRanges(),
            exclude_regions=ExcludeRegions(),
            multi_column=MultiColumnConfig(),
            reading_order_strategy="y_sort",
            heading_detection=HeadingConfig(),
            footnote_processing=FootnoteConfig(),
            metadata=BookMetadata(title=None, author=None, language="en")
        )
        
        assert config.reading_order_strategy == "y_sort"
    
    def test_rejects_invalid_reading_order_strategy(self):
        """ConversionConfig rejects invalid strategy."""
        with pytest.raises(ValueError, match="Invalid reading_order_strategy"):
            ConversionConfig(
                page_ranges=PageRanges(),
                exclude_regions=ExcludeRegions(),
                multi_column=MultiColumnConfig(),
                reading_order_strategy="invalid",
                heading_detection=HeadingConfig(),
                footnote_processing=FootnoteConfig(),
                metadata=BookMetadata(title=None, author=None, language="en")
            )
    
    def test_rejects_exclude_regions_out_of_range(self):
        """ConversionConfig validates exclude_regions are 0.0-1.0."""
        with pytest.raises(ValueError, match="exclude_regions.top must be 0.0-1.0"):
            ConversionConfig(
                page_ranges=PageRanges(),
                exclude_regions=ExcludeRegions(top=1.5),
                multi_column=MultiColumnConfig(),
                reading_order_strategy="y_sort",
                heading_detection=HeadingConfig(),
                footnote_processing=FootnoteConfig(),
                metadata=BookMetadata(title=None, author=None, language="en")
            )
    
    def test_to_dict_from_dict_roundtrip(self):
        """ConversionConfig serialization roundtrip."""
        original = ConversionConfig(
            page_ranges=PageRanges(skip=[1, 2]),
            exclude_regions=ExcludeRegions(top=0.1),
            multi_column=MultiColumnConfig(enabled=True),
            reading_order_strategy="xy_cut",
            heading_detection=HeadingConfig(font_size_threshold=1.3),
            footnote_processing=FootnoteConfig(enabled=True),
            metadata=BookMetadata(title="Book", author="Author", language="ru")
        )
        
        data = original.to_dict()
        restored = ConversionConfig.from_dict(data)
        
        assert restored.reading_order_strategy == original.reading_order_strategy
        assert restored.exclude_regions.top == 0.1

"""Test suite for BaseStrategy abstract class."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from pdf_to_epub.conversion.strategies.base_strategy import BaseStrategy
from pdf_to_epub.conversion.models import (
    ConversionConfig,
    StructuredContent,
    BookMetadata,
    ImageResource,
    Chapter,
    PageRanges,
    ExcludeRegions,
    MultiColumnConfig,
    HeadingConfig,
    FootnoteConfig,
)


class TestBaseStrategyAbstract:
    """Test that BaseStrategy is properly abstract."""
    
    def test_cannot_instantiate_abstract_class(self):
        """BaseStrategy cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseStrategy()
    
    def test_has_abstract_methods(self):
        """BaseStrategy defines abstract methods."""
        abstract_methods = BaseStrategy.__abstractmethods__
        assert 'extract' in abstract_methods
        assert 'order_blocks' in abstract_methods
        assert 'detect_structure' in abstract_methods


class MockStrategy(BaseStrategy):
    """Concrete strategy for testing template method."""
    
    def __init__(self):
        super().__init__()
        self.calls = []
        self.extract_result = ([], [], BookMetadata(title="Test", author="Author", language="en"))
        self.order_result = ([], 1.0)
        self.detect_result = None
    
    def extract(self, pdf_path, config):
        self.calls.append('extract')
        return self.extract_result
    
    def order_blocks(self, blocks, config):
        self.calls.append('order')
        return self.order_result
    
    def detect_structure(self, blocks, config, images, metadata):
        self.calls.append('detect')
        if self.detect_result is None:
            return StructuredContent(
                chapters=[],
                metadata=metadata,
                reading_order_confidence=0.0,
                images=images
            )
        return self.detect_result


class TestBaseStrategyTemplateMethod:
    """Test the template method pattern in convert()."""
    
    def test_template_method_calls_hooks_in_order(self, tmp_path):
        """convert() calls extract → order_blocks → detect_structure."""
        strategy = MockStrategy()
        
        # Create dummy PDF
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"dummy")
        
        config = ConversionConfig(
            page_ranges=PageRanges(),
            exclude_regions=ExcludeRegions(),
            multi_column=MultiColumnConfig(),
            reading_order_strategy="y_sort",
            heading_detection=HeadingConfig(),
            footnote_processing=FootnoteConfig(),
            metadata=BookMetadata(title=None, author=None, language="en")
        )
        
        result = strategy.convert(pdf_path, config)
        
        assert strategy.calls == ['extract', 'order', 'detect']
        assert isinstance(result, StructuredContent)
    
    def test_sets_reading_order_confidence(self, tmp_path):
        """convert() sets reading_order_confidence from order_blocks()."""
        strategy = MockStrategy()
        strategy.order_result = ([], 0.85)
        
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"dummy")
        
        config = ConversionConfig(
            page_ranges=PageRanges(),
            exclude_regions=ExcludeRegions(),
            multi_column=MultiColumnConfig(),
            reading_order_strategy="y_sort",
            heading_detection=HeadingConfig(),
            footnote_processing=FootnoteConfig(),
            metadata=BookMetadata(title=None, author=None, language="en")
        )
        
        result = strategy.convert(pdf_path, config)
        
        assert result.reading_order_confidence == 0.85
    
    def test_raises_file_not_found_for_missing_pdf(self, tmp_path):
        """convert() raises FileNotFoundError if PDF doesn't exist."""
        strategy = MockStrategy()
        
        pdf_path = tmp_path / "nonexistent.pdf"
        config = ConversionConfig(
            page_ranges=PageRanges(),
            exclude_regions=ExcludeRegions(),
            multi_column=MultiColumnConfig(),
            reading_order_strategy="y_sort",
            heading_detection=HeadingConfig(),
            footnote_processing=FootnoteConfig(),
            metadata=BookMetadata(title=None, author=None, language="en")
        )
        
        with pytest.raises(FileNotFoundError):
            strategy.convert(pdf_path, config)
    
    def test_passes_images_and_metadata_to_detect(self, tmp_path):
        """convert() passes images and metadata from extract to detect_structure."""
        strategy = MockStrategy()
        
        # Setup extract to return specific images and metadata
        test_image = ImageResource(
            id="img-1",
            filename="test.png",
            data=b"imagedata",
            format="png",
            width=100,
            height=100,
            page_num=1
        )
        test_metadata = BookMetadata(title="Book", author="Author", language="en")
        strategy.extract_result = ([], [test_image], test_metadata)
        
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"dummy")
        
        config = ConversionConfig(
            page_ranges=PageRanges(),
            exclude_regions=ExcludeRegions(),
            multi_column=MultiColumnConfig(),
            reading_order_strategy="y_sort",
            heading_detection=HeadingConfig(),
            footnote_processing=FootnoteConfig(),
            metadata=BookMetadata(title=None, author=None, language="en")
        )
        
        result = strategy.convert(pdf_path, config)
        
        # Verify images and metadata passed through
        assert len(result.images) == 1
        assert result.images[0].id == "img-1"
        assert result.metadata.title == "Book"


class TestBaseStrategyValidateConfig:
    """Test configuration validation."""

    def test_validate_config_accepts_valid_config(self):
        """_validate_config() accepts valid configuration."""
        strategy = MockStrategy()

        config = ConversionConfig(
            page_ranges=PageRanges(),
            exclude_regions=ExcludeRegions(),
            multi_column=MultiColumnConfig(),
            reading_order_strategy="y_sort",
            heading_detection=HeadingConfig(),
            footnote_processing=FootnoteConfig(),
            metadata=BookMetadata(title=None, author=None, language="en")
        )

        # Should not raise
        strategy._validate_config(config)

    def test_validate_config_rejects_none(self):
        """_validate_config() raises ValueError for None config."""
        strategy = MockStrategy()

        with pytest.raises(ValueError, match="Configuration cannot be None"):
            strategy._validate_config(None)

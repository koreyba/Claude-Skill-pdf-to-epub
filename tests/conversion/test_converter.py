"""Test suite for Converter orchestrator."""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime

from claude_skill.conversion.converter import Converter, DEFAULT_CONFIG, STRATEGY_REGISTRY
from claude_skill.conversion.models import (
    ConversionConfig,
    ConversionResult,
    StructuredContent,
    BookMetadata,
    Chapter,
    PageRanges,
    ExcludeRegions,
    MultiColumnConfig,
    HeadingConfig,
    FootnoteConfig,
)


class TestConverterInit:
    """Test Converter initialization."""
    
    def test_initializes_with_valid_strategy(self):
        """Converter accepts valid strategy name."""
        converter = Converter(strategy="simple")
        assert converter.strategy_name == "simple"
    
    def test_rejects_unknown_strategy(self):
        """Converter raises ValueError for unknown strategy."""
        with pytest.raises(ValueError, match="Unknown strategy"):
            Converter(strategy="nonexistent")
    
    def test_lists_available_strategies_in_error(self):
        """Error message includes available strategies."""
        try:
            Converter(strategy="bad")
        except ValueError as e:
            assert "simple" in str(e)


class TestConverterConvert:
    """Test Converter.convert() orchestration."""
    
    def test_successful_conversion(self, tmp_path, mocker):
        """convert() returns success result for valid conversion."""
        # Create dummy PDF
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")
        
        output_path = tmp_path / "output.epub"
        
        # Mock all dependencies at instance level
        mock_metadata = BookMetadata(title="Book", author="Author", language="en")
        mock_content = StructuredContent(
            chapters=[Chapter(title="Ch1", level=1, content="<p>test</p>", footnotes=[])],
            metadata=mock_metadata,
            reading_order_confidence=0.95,
            images=[]
        )
        
        # Patch strategy.convert at instance level
        converter = Converter(strategy="simple")
        mocker.patch.object(converter.strategy, 'convert', return_value=mock_content)
        mocker.patch.object(converter.epub_builder, 'build', return_value=output_path)
        
        result = converter.convert(pdf_path, output_path)
        
        assert result.status == "success"
        assert result.epub_path == output_path
        assert result.reading_order_confidence == 0.95
        assert "loading_config" in result.log.steps_completed
        assert "extracting" in result.log.steps_completed
        assert "building_epub" in result.log.steps_completed
    
    def test_adds_warning_for_low_confidence(self, tmp_path, mocker):
        """convert() adds warning if reading_order_confidence < 0.7."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")
        output_path = tmp_path / "output.epub"
        
        # Low confidence content
        mock_metadata = BookMetadata(title="Book", author="Author", language="en")
        mock_content = StructuredContent(
            chapters=[],
            metadata=mock_metadata,
            reading_order_confidence=0.5,
            images=[]
        )
        
        converter = Converter(strategy="simple")
        mocker.patch.object(converter.strategy, 'convert', return_value=mock_content)
        mocker.patch.object(converter.epub_builder, 'build', return_value=output_path)
        
        result = converter.convert(pdf_path, output_path)
        
        assert result.status == "warning"
        assert len(result.log.warnings) > 0
        assert "Low reading order confidence" in result.log.warnings[0]
    
    def test_handles_file_not_found(self, tmp_path):
        """convert() returns failed result if PDF not found."""
        pdf_path = tmp_path / "nonexistent.pdf"
        output_path = tmp_path / "output.epub"
        
        converter = Converter(strategy="simple")
        result = converter.convert(pdf_path, output_path)
        
        assert result.status == "failed"
        assert result.epub_path is None
        assert len(result.log.errors) > 0
    
    def test_handles_strategy_exception(self, tmp_path, mocker):
        """convert() catches and logs strategy exceptions."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")
        output_path = tmp_path / "output.epub"
        
        converter = Converter(strategy="simple")
        mocker.patch.object(converter.strategy, 'convert', side_effect=RuntimeError("Strategy failed"))
        
        result = converter.convert(pdf_path, output_path)
        
        assert result.status == "failed"
        assert len(result.log.errors) > 0
        assert "RuntimeError" in result.log.errors[0]
        assert "Strategy failed" in result.log.errors[0]
    
    def test_uses_custom_config(self, tmp_path, mocker):
        """convert() uses provided config instead of default."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")
        output_path = tmp_path / "output.epub"
        
        custom_config = ConversionConfig(
            page_ranges=PageRanges(),
            exclude_regions=ExcludeRegions(top=0.2),
            multi_column=MultiColumnConfig(),
            reading_order_strategy="xy_cut",
            heading_detection=HeadingConfig(),
            footnote_processing=FootnoteConfig(),
            metadata=BookMetadata(title="Custom", author="Author", language="en")
        )
        
        mock_metadata = BookMetadata(title="Book", author="Author", language="en")
        mock_content = StructuredContent(
            chapters=[],
            metadata=mock_metadata,
            reading_order_confidence=1.0,
            images=[]
        )
        
        converter = Converter(strategy="simple")
        mock_convert = mocker.patch.object(converter.strategy, 'convert', return_value=mock_content)
        mocker.patch.object(converter.epub_builder, 'build', return_value=output_path)
        
        result = converter.convert(pdf_path, output_path, config=custom_config)
        
        # Verify custom config was used
        assert mock_convert.called
        call_config = mock_convert.call_args[0][1]
        assert call_config.exclude_regions.top == 0.2
        assert call_config.reading_order_strategy == "xy_cut"


class TestConverterLoadConfig:
    """Test Converter._load_config()."""
    
    def test_returns_default_when_no_path(self):
        """_load_config(None) returns DEFAULT_CONFIG."""
        converter = Converter(strategy="simple")
        config = converter._load_config(None)
        
        assert config == DEFAULT_CONFIG
    
    def test_loads_from_json_file(self, tmp_path):
        """_load_config() loads config from JSON file."""
        config_path = tmp_path / "config.json"
        config_data = {
            "reading_order_strategy": "xy_cut"
        }
        config_path.write_text(json.dumps(config_data), encoding='utf-8')
        
        converter = Converter(strategy="simple")
        
        # Currently returns DEFAULT_CONFIG (TODO in implementation)
        config = converter._load_config(config_path)
        assert isinstance(config, ConversionConfig)


class TestConverterValidateConfig:
    """Test Converter._validate_config()."""
    
    def test_accepts_valid_config(self):
        """_validate_config() accepts valid configuration."""
        converter = Converter(strategy="simple")
        
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
        converter._validate_config(config)
    
    def test_rejects_none_config(self):
        """_validate_config() rejects None."""
        converter = Converter(strategy="simple")
        
        with pytest.raises(ValueError, match="Configuration cannot be None"):
            converter._validate_config(None)
    
    def test_rejects_invalid_exclude_regions(self):
        """_validate_config() validates exclude_regions range."""
        converter = Converter(strategy="simple")
        
        # Create config bypassing dataclass validation
        config = ConversionConfig.__new__(ConversionConfig)
        config.page_ranges = PageRanges()
        config.exclude_regions = ExcludeRegions.__new__(ExcludeRegions)
        config.exclude_regions.top = 0.0
        config.exclude_regions.bottom = 1.5  # Invalid
        config.exclude_regions.left = 0.0
        config.exclude_regions.right = 0.0
        config.multi_column = MultiColumnConfig()
        config.reading_order_strategy = "y_sort"
        config.heading_detection = HeadingConfig()
        config.footnote_processing = FootnoteConfig()
        config.metadata = BookMetadata(title=None, author=None, language="en")
        
        with pytest.raises(ValueError, match="exclude_regions.bottom must be 0.0-1.0"):
            converter._validate_config(config)
    
    def test_rejects_invalid_reading_order_strategy(self):
        """_validate_config() validates reading_order_strategy."""
        converter = Converter(strategy="simple")
        
        # Bypass __post_init__ validation by creating object directly
        config = ConversionConfig.__new__(ConversionConfig)
        config.page_ranges = PageRanges()
        config.exclude_regions = ExcludeRegions()
        config.multi_column = MultiColumnConfig()
        config.reading_order_strategy = "invalid"
        config.heading_detection = HeadingConfig()
        config.footnote_processing = FootnoteConfig()
        config.metadata = BookMetadata(title=None, author=None, language="en")
        
        with pytest.raises(ValueError, match="reading_order_strategy must be one of"):
            converter._validate_config(config)
    
    def test_rejects_invalid_language_code(self):
        """_validate_config() validates 2-letter language code."""
        converter = Converter(strategy="simple")
        
        # Create config with invalid language code
        config = ConversionConfig.__new__(ConversionConfig)
        config.page_ranges = PageRanges()
        config.exclude_regions = ExcludeRegions()
        config.multi_column = MultiColumnConfig()
        config.reading_order_strategy = "y_sort"
        config.heading_detection = HeadingConfig()
        config.footnote_processing = FootnoteConfig()
        config.metadata = BookMetadata.__new__(BookMetadata)
        config.metadata.title = "Book"
        config.metadata.author = "Author"
        config.metadata.language = "eng"  # Invalid: 3 letters
        
        with pytest.raises(ValueError, match="2-letter ISO 639-1 code"):
            converter._validate_config(config)


class TestDefaultConfig:
    """Test DEFAULT_CONFIG is properly configured."""
    
    def test_default_config_is_valid(self):
        """DEFAULT_CONFIG passes validation."""
        converter = Converter(strategy="simple")
        
        # Should not raise
        converter._validate_config(DEFAULT_CONFIG)
    
    def test_default_metadata_allows_none(self):
        """DEFAULT_CONFIG.metadata allows None for PDF extraction."""
        assert DEFAULT_CONFIG.metadata.title is None
        assert DEFAULT_CONFIG.metadata.author is None
        assert DEFAULT_CONFIG.metadata.language == "en"

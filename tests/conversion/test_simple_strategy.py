"""Test suite for SimpleStrategy."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import fitz

from claude_skill.conversion.strategies.simple_strategy import SimpleStrategy
from claude_skill.conversion.models import (
    ConversionConfig,
    BookMetadata,
    ImageResource,
    StructuredContent,
    Chapter,
    PageRanges,
    ExcludeRegions,
    MultiColumnConfig,
    HeadingConfig,
    FootnoteConfig,
)
from claude_skill.conversion.detectors.models import TextBlock


class TestSimpleStrategyExtract:
    """Test SimpleStrategy.extract() method."""
    
    @patch('claude_skill.conversion.strategies.simple_strategy.fitz.open')
    @patch('claude_skill.conversion.strategies.simple_strategy.PDFExtractor')
    def test_extract_calls_pdf_extractor(self, mock_extractor_class, mock_fitz_open, tmp_path):
        """extract() uses PDFExtractor with context manager."""
        # Setup mocks
        mock_extractor = MagicMock()
        mock_extractor_class.return_value.__enter__.return_value = mock_extractor
        mock_extractor.get_structural_blocks.return_value = []
        
        mock_doc = MagicMock()
        mock_doc.metadata = {}
        mock_doc.__iter__ = Mock(return_value=iter([]))
        mock_fitz_open.return_value = mock_doc
        
        # Create dummy PDF
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")
        
        config = ConversionConfig(
            page_ranges=PageRanges(),
            exclude_regions=ExcludeRegions(top=0.1, bottom=0.1),
            multi_column=MultiColumnConfig(),
            reading_order_strategy="y_sort",
            heading_detection=HeadingConfig(),
            footnote_processing=FootnoteConfig(),
            metadata=BookMetadata(title=None, author=None, language="en")
        )
        
        strategy = SimpleStrategy()
        blocks, images, metadata = strategy.extract(pdf_path, config)
        
        # Verify PDFExtractor context manager was used
        mock_extractor_class.assert_called_once_with(pdf_path)
        mock_extractor.get_structural_blocks.assert_called_once()
    
    @patch('claude_skill.conversion.strategies.simple_strategy.fitz.open')
    @patch('claude_skill.conversion.strategies.simple_strategy.PDFExtractor')
    def test_extract_returns_metadata_from_pdf(self, mock_extractor_class, mock_fitz_open, tmp_path):
        """extract() extracts metadata from PDF info dict."""
        mock_extractor = MagicMock()
        mock_extractor_class.return_value.__enter__.return_value = mock_extractor
        mock_extractor.get_structural_blocks.return_value = []
        
        # Mock PDF with metadata
        mock_doc = MagicMock()
        mock_doc.metadata = {
            'title': 'Test Book',
            'author': 'Test Author',
            'subject': 'Test Description',
            'producer': 'Test Publisher'
        }
        mock_doc.__iter__ = Mock(return_value=iter([]))
        mock_fitz_open.return_value = mock_doc
        
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")
        
        config = ConversionConfig(
            page_ranges=PageRanges(),
            exclude_regions=ExcludeRegions(),
            multi_column=MultiColumnConfig(),
            reading_order_strategy="y_sort",
            heading_detection=HeadingConfig(),
            footnote_processing=FootnoteConfig(),
            metadata=BookMetadata(title=None, author=None, language="en")
        )
        
        strategy = SimpleStrategy()
        blocks, images, metadata = strategy.extract(pdf_path, config)
        
        assert metadata.title == 'Test Book'
        assert metadata.author == 'Test Author'
        assert metadata.description == 'Test Description'
        assert metadata.publisher == 'Test Publisher'
    
    @patch('claude_skill.conversion.strategies.simple_strategy.fitz.open')
    @patch('claude_skill.conversion.strategies.simple_strategy.PDFExtractor')
    def test_extract_falls_back_to_config_metadata(self, mock_extractor_class, mock_fitz_open, tmp_path):
        """extract() uses config metadata when PDF has none."""
        mock_extractor = MagicMock()
        mock_extractor_class.return_value.__enter__.return_value = mock_extractor
        mock_extractor.get_structural_blocks.return_value = []
        
        # Mock PDF without metadata
        mock_doc = MagicMock()
        mock_doc.metadata = {}
        mock_doc.__iter__ = Mock(return_value=iter([]))
        mock_fitz_open.return_value = mock_doc
        
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")
        
        config = ConversionConfig(
            page_ranges=PageRanges(),
            exclude_regions=ExcludeRegions(),
            multi_column=MultiColumnConfig(),
            reading_order_strategy="y_sort",
            heading_detection=HeadingConfig(),
            footnote_processing=FootnoteConfig(),
            metadata=BookMetadata(title="Config Title", author="Config Author", language="ru")
        )
        
        strategy = SimpleStrategy()
        blocks, images, metadata = strategy.extract(pdf_path, config)
        
        assert metadata.title == 'Config Title'
        assert metadata.author == 'Config Author'
        assert metadata.language == 'ru'


class TestSimpleStrategyOrderBlocks:
    """Test SimpleStrategy.order_blocks() method."""
    
    @patch('claude_skill.conversion.strategies.simple_strategy.YSorter')
    def test_order_blocks_uses_y_sorter(self, mock_y_sorter_class):
        """order_blocks() uses YSorter for reading order."""
        mock_sorter = MagicMock()
        mock_y_sorter_class.return_value = mock_sorter
        
        block1 = TextBlock(text="A", page=1, x0=0, y0=0, x1=100, y1=20, font_name="Arial", font_size=12, flags=0)
        block2 = TextBlock(text="B", page=1, x0=0, y0=30, x1=100, y1=50, font_name="Arial", font_size=12, flags=0)
        blocks = [block2, block1]
        
        mock_sorter.sort_blocks.return_value = [block1, block2]
        
        config = ConversionConfig(
            page_ranges=PageRanges(),
            exclude_regions=ExcludeRegions(),
            multi_column=MultiColumnConfig(),
            reading_order_strategy="y_sort",
            heading_detection=HeadingConfig(),
            footnote_processing=FootnoteConfig(),
            metadata=BookMetadata(title=None, author=None, language="en")
        )
        
        strategy = SimpleStrategy()
        ordered, confidence = strategy.order_blocks(blocks, config)
        
        mock_sorter.sort_blocks.assert_called_once_with(blocks)
        assert ordered == [block1, block2]
        assert confidence == 1.0

    def test_order_blocks_moves_side_blocks_after_main(self):
        """order_blocks() places narrow side blocks after main flow."""
        strategy = SimpleStrategy()

        main1 = TextBlock(text="Main1", page=1, x0=50, y0=0, x1=450, y1=20, font_name="Arial", font_size=12, flags=0)
        side = TextBlock(text="Side", page=1, x0=480, y0=10, x1=520, y1=25, font_name="Arial", font_size=10, flags=0)
        main2 = TextBlock(text="Main2", page=1, x0=50, y0=40, x1=450, y1=60, font_name="Arial", font_size=12, flags=0)

        reordered = strategy._reorder_side_blocks([main1, side, main2])

        assert reordered == [main1, main2, side]


class TestSimpleStrategyDetectStructure:
    """Test SimpleStrategy.detect_structure() method."""
    
    @patch('claude_skill.conversion.strategies.simple_strategy.FontAnalyzer')
    @patch('claude_skill.conversion.strategies.simple_strategy.StructureClassifier')
    @patch('claude_skill.conversion.strategies.simple_strategy.StructureBuilder')
    def test_detect_structure_pipeline(self, mock_builder_class, mock_classifier_class, mock_analyzer_class):
        """detect_structure() calls FontAnalyzer → Classifier → Builder pipeline."""
        # Setup mocks
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_font_profile = {"Arial": {"avg_size": 12}}
        mock_analyzer.analyze.return_value = mock_font_profile
        
        mock_classifier = MagicMock()
        mock_classifier_class.return_value = mock_classifier
        mock_classified = [MagicMock()]
        mock_classifier.classify.return_value = mock_classified
        
        mock_builder = MagicMock()
        mock_builder_class.return_value = mock_builder
        mock_chapter = Chapter(title="Chapter 1", level=1, content="<p>Test</p>", footnotes=[])
        mock_builder.build_chapters.return_value = [mock_chapter]
        
        blocks = [TextBlock(text="Test", page=1, x0=0, y0=0, x1=100, y1=20, font_name="Arial", font_size=12, flags=0)]
        config = ConversionConfig(
            page_ranges=PageRanges(),
            exclude_regions=ExcludeRegions(),
            multi_column=MultiColumnConfig(),
            reading_order_strategy="y_sort",
            heading_detection=HeadingConfig(),
            footnote_processing=FootnoteConfig(),
            metadata=BookMetadata(title=None, author=None, language="en")
        )
        
        metadata = BookMetadata(title="Book", author="Author", language="en")
        images = []
        
        strategy = SimpleStrategy()
        result = strategy.detect_structure(blocks, config, images, metadata)
        
        # Verify pipeline
        mock_analyzer.analyze.assert_called_once_with(blocks)
        mock_classifier.classify.assert_called_once_with(blocks)
        mock_builder.build_chapters.assert_called_once_with(mock_classified)
        
        assert isinstance(result, StructuredContent)
        assert len(result.chapters) == 1
        assert result.metadata == metadata
        assert result.images == images
    
    @patch('claude_skill.conversion.strategies.simple_strategy.FontAnalyzer')
    @patch('claude_skill.conversion.strategies.simple_strategy.StructureClassifier')
    @patch('claude_skill.conversion.strategies.simple_strategy.StructureBuilder')
    def test_handles_empty_chapters(self, mock_builder_class, mock_classifier_class, mock_analyzer_class):
        """detect_structure() creates default chapter if none detected."""
        # Setup mocks to return empty chapters
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.analyze_fonts.return_value = {}
        
        mock_classifier = MagicMock()
        mock_classifier_class.return_value = mock_classifier
        mock_classifier.classify.return_value = []
        
        mock_builder = MagicMock()
        mock_builder_class.return_value = mock_builder
        mock_builder.build_chapters.return_value = []  # No chapters detected
        
        blocks = [
            TextBlock(text="Text 1", page=1, x0=0, y0=0, x1=100, y1=20, font_name="Arial", font_size=12, flags=0),
            TextBlock(text="Text 2", page=1, x0=0, y0=30, x1=100, y1=50, font_name="Arial", font_size=12, flags=0)
        ]
        config = ConversionConfig(
            page_ranges=PageRanges(),
            exclude_regions=ExcludeRegions(),
            multi_column=MultiColumnConfig(),
            reading_order_strategy="y_sort",
            heading_detection=HeadingConfig(),
            footnote_processing=FootnoteConfig(),
            metadata=BookMetadata(title=None, author=None, language="en")
        )
        
        metadata = BookMetadata(title="Book", author="Author", language="en")
        
        strategy = SimpleStrategy()
        result = strategy.detect_structure(blocks, config, [], metadata)
        
        # Should create default "Content" chapter
        assert len(result.chapters) == 1
        assert result.chapters[0].title == "Content"
        assert result.chapters[0].level == 1
        assert "Text 1" in result.chapters[0].content
        assert "Text 2" in result.chapters[0].content

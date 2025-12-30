"""
Tests for StructureClassifier (semantic block classification).
"""
import pytest
from claude_skill.conversion.detectors.structure_classifier import StructureClassifier
from claude_skill.conversion.detectors.models import TextBlock, SemanticBlock


class TestStructureClassifierClassify:
    """Test classify() method."""
    
    def test_empty_blocks_returns_empty_list(self):
        """classify() returns [] for empty block list."""
        classifier = StructureClassifier()
        assert classifier.classify([]) == []
    
    def test_single_block_classified_as_body(self):
        """classify() classifies single block as body by default."""
        blocks = [
            TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="Normal paragraph text.", 
                      font_name="Arial", font_size=12.0, flags=0)
        ]
        
        classifier = StructureClassifier()
        result = classifier.classify(blocks)
        
        assert len(result) == 1
        assert isinstance(result[0], SemanticBlock)
        assert result[0].role == "body"
    
    def test_bold_large_font_classified_as_h1(self):
        """classify() assigns h1 to bold, large font blocks."""
        blocks = [
            TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="Body text " * 20, 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=30, x1=100, y1=50, text="Chapter One", 
                      font_name="Arial", font_size=18.0, flags=16),  # Bold + Large
        ]
        
        classifier = StructureClassifier()
        result = classifier.classify(blocks)
        
        assert result[0].role == "body"
        assert result[1].role == "h1"
        assert result[1].score >= 75
    
    def test_medium_heading_classified_as_h2(self):
        """classify() assigns h2 to medium-scored headings."""
        blocks = [
            TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="Body text " * 20, 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=30, x1=100, y1=45, text="Section Title", 
                      font_name="Arial", font_size=14.0, flags=16),  # Bold + slightly larger
        ]
        
        classifier = StructureClassifier()
        result = classifier.classify(blocks)
        
        assert result[1].role in ["h1", "h2"]
        assert 50 <= result[1].score < 100
    
    def test_list_item_detected(self):
        """classify() detects list items with bullets or numbers."""
        blocks = [
            TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="Body text " * 20, 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=10, x1=100, y1=20, text="• First item", 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=20, x1=100, y1=30, text="- Second item", 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=30, x1=100, y1=40, text="1. Third item", 
                      font_name="Arial", font_size=12.0, flags=0),
        ]
        
        classifier = StructureClassifier()
        result = classifier.classify(blocks)
        
        assert result[1].role == "list-item"
        assert result[2].role == "list-item"
        assert result[3].role == "list-item"
    
    def test_heading_score_includes_debug_signals(self):
        """classify() populates debug_signals for transparency."""
        blocks = [
            TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="Body " * 20, 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=30, x1=100, y1=50, text="HEADING", 
                      font_name="Arial", font_size=18.0, flags=16),
        ]
        
        classifier = StructureClassifier()
        result = classifier.classify(blocks)
        
        signals = result[1].debug_signals
        assert "Bold" in signals
        assert any("Size+" in s for s in signals)
        assert "NoPunct" in signals
        assert "ALLCAPS" in signals


class TestStructureClassifierHeadingScore:
    """Test _calculate_heading_score() scoring logic."""
    
    def test_bold_text_adds_30_points(self):
        """_calculate_heading_score() adds 30 points for bold text."""
        classifier = StructureClassifier()
        
        body_block = TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="Body", 
                               font_name="Arial", font_size=12.0, flags=0)
        bold_block = TextBlock(page=1, x0=0, y0=10, x1=100, y1=20, text="Bold", 
                               font_name="Arial", font_size=12.0, flags=16)
        
        score, signals = classifier._calculate_heading_score(bold_block, None, None, 12.0, 0)
        
        assert score >= 30
        assert "Bold" in signals
    
    def test_larger_size_adds_proportional_points(self):
        """_calculate_heading_score() adds points proportional to size difference."""
        classifier = StructureClassifier()
        
        large_block = TextBlock(page=1, x0=0, y0=0, x1=100, y1=20, text="Large", 
                                font_name="Arial", font_size=18.0, flags=0)
        
        score, signals = classifier._calculate_heading_score(large_block, None, None, 12.0, 0)
        
        # 18 - 12 = 6 size diff -> 6 * 10 = 60 points
        assert score >= 60
        assert any("Size+" in s for s in signals)
    
    def test_no_punctuation_adds_20_points(self):
        """_calculate_heading_score() adds 20 points for no terminal punctuation."""
        classifier = StructureClassifier()
        
        no_punct = TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="No punctuation", 
                             font_name="Arial", font_size=12.0, flags=0)
        with_punct = TextBlock(page=1, x0=0, y0=10, x1=100, y1=20, text="With punctuation.", 
                               font_name="Arial", font_size=12.0, flags=0)
        
        score_no, signals_no = classifier._calculate_heading_score(no_punct, None, None, 12.0, 0)
        score_with, signals_with = classifier._calculate_heading_score(with_punct, None, None, 12.0, 0)
        
        assert "NoPunct" in signals_no
        assert "NoPunct" not in signals_with
        assert score_no > score_with
    
    def test_short_text_adds_points(self):
        """_calculate_heading_score() adds points for short text."""
        classifier = StructureClassifier()
        
        short = TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="Short", 
                          font_name="Arial", font_size=12.0, flags=0)
        very_short = TextBlock(page=1, x0=0, y0=10, x1=100, y1=20, text="VS", 
                               font_name="Arial", font_size=12.0, flags=0)
        long = TextBlock(page=1, x0=0, y0=20, x1=100, y1=30, text="A" * 200, 
                         font_name="Arial", font_size=12.0, flags=0)
        
        score_short, signals_short = classifier._calculate_heading_score(short, None, None, 12.0, 0)
        score_very_short, signals_very_short = classifier._calculate_heading_score(very_short, None, None, 12.0, 0)
        score_long, signals_long = classifier._calculate_heading_score(long, None, None, 12.0, 0)
        
        assert "Short" in signals_short
        assert "Short" in signals_very_short
        assert "Short" not in signals_long
        # Both very short and short get the same bonus (both < 50 chars)
        assert score_very_short >= score_short
        assert score_short > score_long
    
    def test_all_caps_adds_10_points(self):
        """_calculate_heading_score() adds 10 points for all-caps text."""
        classifier = StructureClassifier()
        
        allcaps = TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="ALL CAPS", 
                            font_name="Arial", font_size=12.0, flags=0)
        normal = TextBlock(page=1, x0=0, y0=10, x1=100, y1=20, text="Normal Case", 
                           font_name="Arial", font_size=12.0, flags=0)
        
        score_caps, signals_caps = classifier._calculate_heading_score(allcaps, None, None, 12.0, 0)
        score_normal, signals_normal = classifier._calculate_heading_score(normal, None, None, 12.0, 0)
        
        assert "ALLCAPS" in signals_caps
        assert "ALLCAPS" not in signals_normal
        assert score_caps > score_normal
    
    def test_top_margin_adds_points(self):
        """_calculate_heading_score() adds points for large top margin."""
        classifier = StructureClassifier()
        
        prev = TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="Previous", 
                         font_name="Arial", font_size=12.0, flags=0)
        # Large gap: y0=50 vs prev.y1=10 -> 40pt gap
        current = TextBlock(page=1, x0=0, y0=50, x1=100, y1=60, text="Current", 
                            font_name="Arial", font_size=12.0, flags=0)
        next_b = TextBlock(page=1, x0=0, y0=62, x1=100, y1=72, text="Next", 
                           font_name="Arial", font_size=12.0, flags=0)
        
        score, signals = classifier._calculate_heading_score(current, prev, next_b, 12.0, 0)
        
        # Line height = 12 * 1.2 = 14.4, gap 40 > 14.4 * 1.5 = 21.6
        assert any("TopMargin" in s or "Top>Bottom" in s for s in signals)
    
    def test_empty_block_returns_zero_score(self):
        """_calculate_heading_score() returns 0 for empty blocks."""
        classifier = StructureClassifier()
        
        empty = TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="", 
                          font_name="Arial", font_size=12.0, flags=0)
        
        score, signals = classifier._calculate_heading_score(empty, None, None, 12.0, 0)
        
        assert score == 0.0
        assert signals == []


class TestStructureClassifierIsListItem:
    """Test _is_list_item() detection."""
    
    def test_bullet_list_item(self):
        """_is_list_item() detects bullet points."""
        classifier = StructureClassifier()
        
        assert classifier._is_list_item("• Item one") is True
        assert classifier._is_list_item("- Item two") is True
    
    def test_numbered_list_item(self):
        """_is_list_item() detects numbered lists."""
        classifier = StructureClassifier()
        
        assert classifier._is_list_item("1. First") is True
        assert classifier._is_list_item("2. Second") is True
        assert classifier._is_list_item("9. Ninth") is True
        assert classifier._is_list_item("10. Tenth") is True
        assert classifier._is_list_item("99. Ninety-ninth") is True
    
    def test_not_list_item(self):
        """_is_list_item() returns False for non-list text."""
        classifier = StructureClassifier()
        
        assert classifier._is_list_item("Normal paragraph") is False
        assert classifier._is_list_item("1.5 is a number") is False
        assert classifier._is_list_item("•••") is True  # Just bullet counts
        assert classifier._is_list_item("-") is False  # Too short

"""
Tests for FontAnalyzer (font style detection and classification).
"""
import pytest
from pdf_to_epub.conversion.detectors.font_analyzer import FontAnalyzer
from pdf_to_epub.conversion.detectors.models import TextBlock


class TestFontAnalyzerAnalyze:
    """Test analyze() method."""
    
    def test_empty_blocks_returns_empty_dict(self):
        """analyze() returns {} for empty block list."""
        analyzer = FontAnalyzer()
        assert analyzer.analyze([]) == {}
    
    def test_single_style_detected_as_body(self):
        """analyze() detects single font style as 'body'."""
        blocks = [
            TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="Normal text", 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=10, x1=100, y1=20, text="More normal text", 
                      font_name="Arial", font_size=12.0, flags=0),
        ]
        
        analyzer = FontAnalyzer()
        style_map = analyzer.analyze(blocks)
        
        assert ("Arial", 12.0, 0) in style_map
        assert style_map[("Arial", 12.0, 0)] == "body"
    
    def test_most_frequent_style_becomes_body(self):
        """analyze() assigns 'body' to most frequent style by character count."""
        blocks = [
            TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="A" * 100, 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=10, x1=100, y1=20, text="B" * 200, 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=20, x1=100, y1=30, text="H", 
                      font_name="Arial", font_size=18.0, flags=0),
        ]
        
        analyzer = FontAnalyzer()
        style_map = analyzer.analyze(blocks)
        
        # Arial 12.0 has 300 chars total -> body
        assert style_map[("Arial", 12.0, 0)] == "body"
    
    def test_larger_font_classified_as_header(self):
        """analyze() classifies fonts >1.2x body size as headers."""
        blocks = [
            TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="Body " * 50, 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=10, x1=100, y1=30, text="Heading", 
                      font_name="Arial", font_size=18.0, flags=0),  # 18/12 = 1.5 > 1.2
        ]
        
        analyzer = FontAnalyzer()
        style_map = analyzer.analyze(blocks)
        
        assert style_map[("Arial", 12.0, 0)] == "body"
        assert style_map[("Arial", 18.0, 0)] == "h1"
    
    def test_smaller_font_classified_as_footnote(self):
        """analyze() classifies fonts <0.9x body size as footnote_or_small."""
        blocks = [
            TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="Body " * 50, 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=100, x1=100, y1=105, text="Footnote", 
                      font_name="Arial", font_size=9.0, flags=0),  # 9/12 = 0.75 < 0.9
        ]
        
        analyzer = FontAnalyzer()
        style_map = analyzer.analyze(blocks)
        
        assert style_map[("Arial", 12.0, 0)] == "body"
        assert style_map[("Arial", 9.0, 0)] == "footnote_or_small"
    
    def test_bold_same_size_classified_as_strong(self):
        """analyze() classifies same-size bold font as 'strong'."""
        blocks = [
            TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="Body " * 50, 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=10, x1=100, y1=20, text="Bold", 
                      font_name="Arial", font_size=12.0, flags=16),  # flag 2^4 = 16 = bold
        ]
        
        analyzer = FontAnalyzer()
        style_map = analyzer.analyze(blocks)
        
        assert style_map[("Arial", 12.0, 0)] == "body"
        assert style_map[("Arial", 12.0, 16)] == "strong"
    
    def test_same_size_non_bold_classified_as_body_variant(self):
        """analyze() classifies same-size non-bold as 'body_variant'."""
        blocks = [
            TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="Body " * 50, 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=10, x1=100, y1=20, text="Italic", 
                      font_name="Arial-Italic", font_size=12.0, flags=2),  # italic flag
        ]
        
        analyzer = FontAnalyzer()
        style_map = analyzer.analyze(blocks)
        
        assert style_map[("Arial", 12.0, 0)] == "body"
        assert style_map[("Arial-Italic", 12.0, 2)] == "body_variant"
    
    def test_multiple_headers_assigned_h1_to_h6(self):
        """analyze() assigns h1, h2, h3... to headers in size descending order."""
        blocks = [
            TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="Body " * 100, 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=10, x1=100, y1=20, text="H1", 
                      font_name="Arial", font_size=24.0, flags=0),
            TextBlock(page=1, x0=0, y0=20, x1=100, y1=30, text="H2", 
                      font_name="Arial", font_size=18.0, flags=0),
            TextBlock(page=1, x0=0, y0=30, x1=100, y1=40, text="H3", 
                      font_name="Arial", font_size=14.5, flags=0),  # 14.5/12 = 1.21 > 1.2
        ]
        
        analyzer = FontAnalyzer()
        style_map = analyzer.analyze(blocks)
        
        assert style_map[("Arial", 24.0, 0)] == "h1"
        assert style_map[("Arial", 18.0, 0)] == "h2"
        assert style_map[("Arial", 14.5, 0)] == "h3"
    
    def test_more_than_six_headers_capped_at_h6(self):
        """analyze() caps header levels at h6 even if more sizes exist."""
        blocks = [
            TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="Body " * 100, 
                      font_name="Arial", font_size=12.0, flags=0),
        ]
        
        # Add 8 different header sizes (all > body * 1.2 = 14.4)
        for i in range(8):
            size = 26.0 - i * 1.5  # 26, 24.5, 23, 21.5, 20, 18.5, 17, 15.5
            blocks.append(
                TextBlock(page=1, x0=0, y0=10*i, x1=100, y1=10*(i+1), text=f"H{i+1}", 
                          font_name="Arial", font_size=size, flags=0)
            )
        
        analyzer = FontAnalyzer()
        style_map = analyzer.analyze(blocks)
        
        # First 6 should be h1-h6, remaining should also be h6
        assert style_map[("Arial", 26.0, 0)] == "h1"
        assert style_map[("Arial", 24.5, 0)] == "h2"
        assert style_map[("Arial", 15.5, 0)] == "h6"  # 8th header also h6
    
    def test_font_size_rounded_to_one_decimal(self):
        """analyze() rounds font sizes to 1 decimal place."""
        blocks = [
            TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="Body " * 50, 
                      font_name="Arial", font_size=11.99, flags=0),
            TextBlock(page=1, x0=0, y0=10, x1=100, y1=20, text="More body", 
                      font_name="Arial", font_size=12.01, flags=0),
        ]
        
        analyzer = FontAnalyzer()
        style_map = analyzer.analyze(blocks)
        
        # Both should round to 12.0 and be combined
        assert ("Arial", 12.0, 0) in style_map
    
    def test_empty_text_blocks_skipped(self):
        """analyze() handles blocks with empty/whitespace text."""
        blocks = [
            TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="", 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=10, x1=100, y1=20, text="   ", 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=20, x1=100, y1=30, text="Actual text", 
                      font_name="Arial", font_size=12.0, flags=0),
        ]
        
        analyzer = FontAnalyzer()
        style_map = analyzer.analyze(blocks)
        
        # Should still detect style, only non-empty text counted
        assert ("Arial", 12.0, 0) in style_map
        assert style_map[("Arial", 12.0, 0)] == "body"
    
    def test_all_empty_blocks_returns_body_style(self):
        """analyze() detects style even for empty text blocks."""
        blocks = [
            TextBlock(page=1, x0=0, y0=0, x1=100, y1=10, text="", 
                      font_name="Arial", font_size=12.0, flags=0),
            TextBlock(page=1, x0=0, y0=10, x1=100, y1=20, text="   ", 
                      font_name="Arial", font_size=12.0, flags=0),
        ]
        
        analyzer = FontAnalyzer()
        style_map = analyzer.analyze(blocks)
        
        # Even with 0 chars, still detects the style as body
        assert ("Arial", 12.0, 0) in style_map
        assert style_map[("Arial", 12.0, 0)] == "body"

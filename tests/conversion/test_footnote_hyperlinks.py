"""Tests for footnote detection and hyperlink generation."""

import pytest
from pdf_to_epub.conversion.detectors.footnote_detector import FootnoteDetector, FootnoteRef
from pdf_to_epub.conversion.detectors.endnote_formatter import EndnoteFormatter
from pdf_to_epub.conversion.detectors.models import TextBlock, SemanticBlock


class TestFootnoteDetector:
    """Tests for FootnoteDetector class."""

    def test_find_bracket_references(self):
        """Test detection of bracket-style references [1], [2]."""
        detector = FootnoteDetector(patterns=['bracket'])
        refs = detector.find_references("This is a statement[1] with reference[12].")

        assert len(refs) == 2
        assert refs[0].number == 1
        assert refs[0].original_text == "[1]"
        assert refs[1].number == 12
        assert refs[1].original_text == "[12]"

    def test_find_paren_references(self):
        """Test detection of parenthesis-style references (1), (2)."""
        detector = FootnoteDetector(patterns=['paren'])
        refs = detector.find_references("This is a statement(1) with reference(5).")

        assert len(refs) == 2
        assert refs[0].number == 1
        assert refs[0].original_text == "(1)"
        assert refs[1].number == 5
        assert refs[1].original_text == "(5)"

    def test_find_period_references(self):
        """Test detection of period-style references word.1, sentence.2."""
        detector = FootnoteDetector(patterns=['period'])
        refs = detector.find_references("This statement.1 has a reference.12 here.")

        assert len(refs) == 2
        assert refs[0].number == 1
        assert refs[0].original_text == ".1"
        assert refs[1].number == 12
        assert refs[1].original_text == ".12"

    def test_find_superscript_references(self):
        """Test detection of superscript-style references word1, text2."""
        detector = FootnoteDetector(patterns=['superscript'])
        refs = detector.find_references("This statement1 has a reference12 here.")

        assert len(refs) == 2
        assert refs[0].number == 1
        assert refs[0].original_text == "1"
        assert refs[1].number == 12
        assert refs[1].original_text == "12"

    def test_default_patterns_bracket_paren(self):
        """Test default patterns include bracket and paren."""
        detector = FootnoteDetector()  # Default patterns
        refs = detector.find_references("Reference[1] and (2) here.")

        assert len(refs) == 2
        assert refs[0].number == 1
        assert refs[1].number == 2

    def test_ignores_large_numbers(self):
        """Test that numbers > 99 are ignored."""
        detector = FootnoteDetector(patterns=['bracket'])
        refs = detector.find_references("Reference[100] and [999] are ignored.")

        assert len(refs) == 0

    def test_no_duplicates_same_position(self):
        """Test that overlapping matches are deduplicated."""
        detector = FootnoteDetector(patterns=['bracket', 'paren'])
        # Only bracket pattern should match here
        refs = detector.find_references("Text[1] with reference.")

        assert len(refs) == 1

    def test_convert_to_hyperlinks_bracket(self):
        """Test converting bracket references to hyperlinks."""
        detector = FootnoteDetector(patterns=['bracket'])
        text = "This statement[1] is important."
        result = detector.convert_to_hyperlinks(text, "endnotes.xhtml")

        assert '[1]' not in result
        assert 'href="endnotes.xhtml#note1"' in result
        assert 'class="footnote-ref"' in result
        assert '<sup>1</sup>' in result

    def test_convert_to_hyperlinks_multiple(self):
        """Test converting multiple references."""
        detector = FootnoteDetector(patterns=['bracket'])
        text = "First[1] and second[2] references."
        result = detector.convert_to_hyperlinks(text, "chapter5.xhtml")

        assert 'href="chapter5.xhtml#note1"' in result
        assert 'href="chapter5.xhtml#note2"' in result
        assert '<sup>1</sup>' in result
        assert '<sup>2</sup>' in result

    def test_convert_to_hyperlinks_no_refs(self):
        """Test that text without references is unchanged."""
        detector = FootnoteDetector(patterns=['bracket'])
        text = "This is plain text without references."
        result = detector.convert_to_hyperlinks(text, "endnotes.xhtml")

        assert result == text

    def test_detect_reference_style(self):
        """Test automatic style detection."""
        detector = FootnoteDetector()

        assert detector.detect_reference_style("Text[1] here") == 'bracket'
        assert detector.detect_reference_style("Text(1) here") == 'paren'
        assert detector.detect_reference_style("Text.1 here") == 'period'
        assert detector.detect_reference_style("Text1 here") == 'superscript'
        assert detector.detect_reference_style("No refs here") is None

    def test_process_blocks(self):
        """Test processing SemanticBlocks to add footnote_refs metadata."""
        detector = FootnoteDetector(patterns=['bracket'])

        block = TextBlock(
            text="Statement[1] with reference.",
            page=1, x0=0, y0=0, x1=100, y1=20,
            font_name="Arial", font_size=12, flags=0
        )
        sem_block = SemanticBlock(original_block=block, role="body")

        result = detector.process([sem_block])

        assert len(result) == 1
        assert "footnote_refs" in result[0].metadata
        assert len(result[0].metadata["footnote_refs"]) == 1
        assert result[0].metadata["footnote_refs"][0]["num"] == 1


class TestEndnoteFormatter:
    """Tests for EndnoteFormatter class."""

    def _create_endnote_block(self, text: str, num: int = None) -> SemanticBlock:
        """Helper to create endnote SemanticBlock."""
        block = TextBlock(
            text=text,
            page=10, x0=0, y0=0, x1=100, y1=20,
            font_name="Arial", font_size=10, flags=0
        )
        return SemanticBlock(original_block=block, role="endnote", endnote_num=num)

    def test_format_single_endnote(self):
        """Test formatting a single endnote."""
        formatter = EndnoteFormatter()
        blocks = [self._create_endnote_block("1  This is the first endnote.", num=1)]

        html = formatter.format_endnotes(blocks)

        assert 'id="note1"' in html
        assert 'class="endnote"' in html
        assert '<span class="endnote-num">1.</span>' in html
        assert "This is the first endnote." in html

    def test_format_multiple_endnotes(self):
        """Test formatting multiple endnotes."""
        formatter = EndnoteFormatter()
        blocks = [
            self._create_endnote_block("1  First endnote.", num=1),
            self._create_endnote_block("2  Second endnote.", num=2),
            self._create_endnote_block("3  Third endnote.", num=3),
        ]

        html = formatter.format_endnotes(blocks)

        assert 'id="note1"' in html
        assert 'id="note2"' in html
        assert 'id="note3"' in html
        assert "First endnote" in html
        assert "Second endnote" in html
        assert "Third endnote" in html

    def test_format_endnote_without_num_extracts_from_text(self):
        """Test that endnote number is extracted from text if not provided."""
        formatter = EndnoteFormatter()
        blocks = [self._create_endnote_block("5  Fifth endnote content.", num=None)]

        html = formatter.format_endnotes(blocks)

        assert 'id="note5"' in html
        assert '<span class="endnote-num">5.</span>' in html

    def test_format_endnotes_with_backlinks(self):
        """Test formatting endnotes with back-links to main chapter."""
        formatter = EndnoteFormatter()
        blocks = [self._create_endnote_block("1  First endnote.", num=1)]

        html = formatter.format_endnotes_with_backlinks(blocks, "chapter1.xhtml")

        assert 'id="note1"' in html
        assert 'href="chapter1.xhtml#ref1"' in html
        assert 'class="endnote-backlink"' in html
        assert '[^]' in html

    def test_skips_non_endnote_blocks(self):
        """Test that non-endnote blocks are skipped."""
        formatter = EndnoteFormatter()
        block = TextBlock(
            text="Regular paragraph.",
            page=1, x0=0, y0=0, x1=100, y1=20,
            font_name="Arial", font_size=12, flags=0
        )
        blocks = [SemanticBlock(original_block=block, role="body")]

        html = formatter.format_endnotes(blocks)

        assert html == ""

    def test_get_endnote_numbers(self):
        """Test extracting endnote numbers from blocks."""
        formatter = EndnoteFormatter()
        blocks = [
            self._create_endnote_block("1  First.", num=1),
            self._create_endnote_block("3  Third.", num=3),
            self._create_endnote_block("2  Second.", num=2),
        ]

        numbers = formatter.get_endnote_numbers(blocks)

        assert numbers == [1, 2, 3]  # Sorted

    def test_html_escaping(self):
        """Test that HTML special characters are escaped."""
        formatter = EndnoteFormatter()
        blocks = [self._create_endnote_block("1  Contains <script> & \"quotes\".", num=1)]

        html = formatter.format_endnotes(blocks)

        assert "&lt;script&gt;" in html
        assert "&amp;" in html
        assert "&quot;quotes&quot;" in html
        assert "<script>" not in html


class TestFootnoteIntegration:
    """Integration tests for footnote/endnote system."""

    def test_footnote_ref_links_to_endnote_anchor(self):
        """Test that footnote refs link to correct endnote anchors."""
        # Main text with reference
        detector = FootnoteDetector(patterns=['bracket'])
        main_text = "Important statement[1] here."
        main_html = detector.convert_to_hyperlinks(main_text, "endnotes.xhtml")

        # Endnotes with anchor
        formatter = EndnoteFormatter()
        block = TextBlock(
            text="1  The source for this statement.",
            page=10, x0=0, y0=0, x1=100, y1=20,
            font_name="Arial", font_size=10, flags=0
        )
        endnote_blocks = [SemanticBlock(original_block=block, role="endnote", endnote_num=1)]
        endnotes_html = formatter.format_endnotes(endnote_blocks)

        # Verify linking
        assert 'href="endnotes.xhtml#note1"' in main_html
        assert 'id="note1"' in endnotes_html

    def test_round_trip_backlinks(self):
        """Test that backlinks work correctly for round-trip navigation."""
        formatter = EndnoteFormatter()
        block = TextBlock(
            text="1  The source.",
            page=10, x0=0, y0=0, x1=100, y1=20,
            font_name="Arial", font_size=10, flags=0
        )
        endnote_blocks = [SemanticBlock(original_block=block, role="endnote", endnote_num=1)]

        html = formatter.format_endnotes_with_backlinks(endnote_blocks, "chapter1.xhtml")

        # Should have anchor and backlink
        assert 'id="note1"' in html
        assert 'href="chapter1.xhtml#ref1"' in html

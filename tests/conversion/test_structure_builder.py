"""
Tests for StructureBuilder (hierarchical chapter tree construction).
"""
import pytest
from pdf_to_epub.conversion.detectors.structure_builder import StructureBuilder, Chapter
from pdf_to_epub.conversion.detectors.models import SemanticBlock, TextBlock


def make_block(
    text: str,
    role: str = "body",
    *,
    page: int = 1,
    x0: float = 0.0,
    y0: float = 0.0,
    x1: float = 100.0,
    y1: float = 10.0,
    font_name: str = "Arial",
    font_size: float = 12.0,
    flags: int = 0,
    endnote_num: int | None = None,
) -> SemanticBlock:
    """Helper to create SemanticBlock for testing."""
    tb = TextBlock(
        text=text,
        page=page,
        x0=x0,
        y0=y0,
        x1=x1,
        y1=y1,
        font_name=font_name,
        font_size=font_size,
        flags=flags,
    )
    return SemanticBlock(original_block=tb, role=role, endnote_num=endnote_num)


class TestStructureBuilderBuildChapters:
    """Test build_chapters() method."""
    
    def test_empty_blocks_returns_empty_list(self):
        """build_chapters() returns [] for empty block list."""
        builder = StructureBuilder()
        chapters = builder.build_chapters([])
        assert chapters == []
    
    def test_single_h1_creates_one_chapter(self):
        """build_chapters() creates one chapter for single H1."""
        blocks = [
            make_block("Chapter One", "h1"),
            make_block("Body text.", "body"),
        ]
        
        builder = StructureBuilder()
        chapters = builder.build_chapters(blocks)
        
        assert len(chapters) == 1
        assert chapters[0].title == "Chapter One"
        assert chapters[0].level == 1
        assert len(chapters[0].content_blocks) == 2  # H1 block + body
    
    def test_preamble_before_first_heading(self):
        """build_chapters() creates Intro chapter for content before first heading."""
        blocks = [
            make_block("Preamble text.", "body"),
            make_block("Chapter One", "h1"),
        ]
        
        builder = StructureBuilder()
        chapters = builder.build_chapters(blocks)
        
        assert len(chapters) == 2
        assert chapters[0].title == "Intro"
        assert chapters[0].level == 0
        assert len(chapters[0].content_blocks) == 1
        assert chapters[1].title == "Chapter One"
    
    def test_removes_empty_preamble(self):
        """build_chapters() removes empty Intro chapter if first block is heading."""
        blocks = [
            make_block("Chapter One", "h1"),
            make_block("Body text.", "body"),
        ]
        
        builder = StructureBuilder()
        chapters = builder.build_chapters(blocks)
        
        # Should not have Intro chapter
        assert len(chapters) == 1
        assert chapters[0].title == "Chapter One"
        assert chapters[0].level == 1
    
    def test_multiple_h1_creates_sibling_chapters(self):
        """build_chapters() creates sibling chapters for multiple H1s."""
        blocks = [
            make_block("Chapter One", "h1"),
            make_block("Body 1.", "body"),
            make_block("Chapter Two", "h1"),
            make_block("Body 2.", "body"),
        ]
        
        builder = StructureBuilder()
        chapters = builder.build_chapters(blocks)
        
        assert len(chapters) == 2
        assert chapters[0].title == "Chapter One"
        assert chapters[1].title == "Chapter Two"
        assert len(chapters[0].subchapters) == 0
        assert len(chapters[1].subchapters) == 0
    
    def test_h2_becomes_subchapter_of_h1(self):
        """build_chapters() nests H2 under H1."""
        blocks = [
            make_block("Chapter One", "h1"),
            make_block("Section 1.1", "h2"),
            make_block("Body text.", "body"),
        ]
        
        builder = StructureBuilder()
        chapters = builder.build_chapters(blocks)
        
        assert len(chapters) == 1
        assert chapters[0].title == "Chapter One"
        assert len(chapters[0].subchapters) == 1
        assert chapters[0].subchapters[0].title == "Section 1.1"
        assert chapters[0].subchapters[0].level == 2
    
    def test_nested_h1_h2_h3(self):
        """build_chapters() handles three levels of nesting."""
        blocks = [
            make_block("Chapter", "h1"),
            make_block("Section", "h2"),
            make_block("Subsection", "h3"),
            make_block("Body", "body"),
        ]
        
        builder = StructureBuilder()
        chapters = builder.build_chapters(blocks)
        
        assert len(chapters) == 1
        h1 = chapters[0]
        assert h1.title == "Chapter"
        assert len(h1.subchapters) == 1
        
        h2 = h1.subchapters[0]
        assert h2.title == "Section"
        assert len(h2.subchapters) == 1
        
        h3 = h2.subchapters[0]
        assert h3.title == "Subsection"
        assert h3.level == 3
    
    def test_h2_after_h2_becomes_sibling(self):
        """build_chapters() creates sibling H2s under same H1."""
        blocks = [
            make_block("Chapter", "h1"),
            make_block("Section A", "h2"),
            make_block("Body A", "body"),
            make_block("Section B", "h2"),
            make_block("Body B", "body"),
        ]
        
        builder = StructureBuilder()
        chapters = builder.build_chapters(blocks)
        
        assert len(chapters) == 1
        assert len(chapters[0].subchapters) == 2
        assert chapters[0].subchapters[0].title == "Section A"
        assert chapters[0].subchapters[1].title == "Section B"
    
    def test_h1_after_h2_creates_new_root(self):
        """build_chapters() creates new root chapter when H1 follows H2."""
        blocks = [
            make_block("Chapter One", "h1"),
            make_block("Section", "h2"),
            make_block("Chapter Two", "h1"),
        ]
        
        builder = StructureBuilder()
        chapters = builder.build_chapters(blocks)
        
        assert len(chapters) == 2
        assert chapters[0].title == "Chapter One"
        assert chapters[1].title == "Chapter Two"
        assert len(chapters[0].subchapters) == 1
        assert len(chapters[1].subchapters) == 0
    
    def test_list_items_added_to_current_chapter(self):
        """build_chapters() adds list items to current chapter content."""
        blocks = [
            make_block("Chapter", "h1"),
            make_block("• Item 1", "list-item"),
            make_block("• Item 2", "list-item"),
        ]
        
        builder = StructureBuilder()
        chapters = builder.build_chapters(blocks)
        
        assert len(chapters) == 1
        # H1 block + 2 list items = 3 content blocks
        assert len(chapters[0].content_blocks) == 3
    
    def test_get_text_concatenates_blocks(self):
        """Chapter.get_text() concatenates all content block texts."""
        blocks = [
            make_block("Chapter", "h1"),
            make_block("First paragraph.", "body"),
            make_block("Second paragraph.", "body"),
        ]
        
        builder = StructureBuilder()
        chapters = builder.build_chapters(blocks)
        
        text = chapters[0].get_text()
        assert "Chapter" in text
        assert "First paragraph" in text
        assert "Second paragraph" in text

    def test_endnotes_heading_used_for_endnotes_title(self):
        """build_chapters() uses ENDNOTES heading as endnotes title."""
        blocks = [
            make_block("Chapter One", "h1"),
            make_block("Body text.", "body"),
            make_block("ENDNOTES to Excerpt C", "body"),
            make_block("1  First endnote text.", "endnote"),
        ]

        builder = StructureBuilder()
        chapters = builder.build_chapters(blocks)

        endnotes_chapter = next((ch for ch in chapters if ch.is_endnotes), None)
        assert endnotes_chapter is not None
        assert endnotes_chapter.title == "ENDNOTES to Excerpt C"

        main_text = " ".join(ch.get_text() for ch in chapters if not ch.is_endnotes)
        assert "ENDNOTES to Excerpt C" not in main_text

    def test_endnotes_merge_continuation_blocks(self):
        blocks = [
            make_block("Chapter One", "h1", page=1),
            make_block("Body text.", "body", page=1),
            make_block("ENDNOTES", "body", page=2),
            make_block("1  First line of note", "endnote", page=2, x0=50, endnote_num=1),
            make_block("Continuation line of same note", "body", page=2, x0=120),
            make_block("2  Second note starts", "endnote", page=2, x0=50, endnote_num=2),
        ]

        builder = StructureBuilder()
        chapters = builder.build_chapters(blocks)

        endnotes_chapter = next((ch for ch in chapters if ch.is_endnotes), None)
        assert endnotes_chapter is not None

        note1 = next((b for b in endnotes_chapter.content_blocks if b.endnote_num == 1), None)
        assert note1 is not None
        assert "First line of note" in note1.original_block.text
        assert "Continuation line of same note" in note1.original_block.text


class TestStructureBuilderMergeHeaders:
    """Test _merge_headers() preprocessing."""
    
    def test_empty_blocks_returns_empty(self):
        """_merge_headers() returns [] for empty list."""
        builder = StructureBuilder()
        assert builder._merge_headers([]) == []
    
    def test_no_consecutive_headers_unchanged(self):
        """_merge_headers() returns unchanged list when no consecutive headers."""
        blocks = [
            make_block("Chapter", "h1"),
            make_block("Body", "body"),
            make_block("Section", "h2"),
        ]
        
        builder = StructureBuilder()
        merged = builder._merge_headers(blocks)
        
        assert len(merged) == 3
        assert merged[0].original_block.text == "Chapter"
    
    def test_consecutive_same_level_headers_merged(self):
        """_merge_headers() merges consecutive headers of same level."""
        blocks = [
            make_block("Chapter", "h1"),
            make_block("Continued", "h1"),
            make_block("Body", "body"),
        ]
        
        builder = StructureBuilder()
        merged = builder._merge_headers(blocks)
        
        assert len(merged) == 2
        assert merged[0].original_block.text == "Chapter Continued"
        assert merged[1].original_block.text == "Body"
    
    def test_different_level_headers_not_merged(self):
        """_merge_headers() does not merge headers of different levels."""
        blocks = [
            make_block("Chapter", "h1"),
            make_block("Section", "h2"),
        ]
        
        builder = StructureBuilder()
        merged = builder._merge_headers(blocks)
        
        assert len(merged) == 2
        assert merged[0].original_block.text == "Chapter"
        assert merged[1].original_block.text == "Section"
    
    def test_body_interrupts_merging(self):
        """_merge_headers() stops merging when body text interrupts."""
        blocks = [
            make_block("Part 1", "h1"),
            make_block("Body", "body"),
            make_block("Part 2", "h1"),
        ]
        
        builder = StructureBuilder()
        merged = builder._merge_headers(blocks)
        
        assert len(merged) == 3
        assert merged[0].original_block.text == "Part 1"
        assert merged[2].original_block.text == "Part 2"
    
    def test_three_consecutive_headers_all_merged(self):
        """_merge_headers() merges three consecutive headers of same level."""
        blocks = [
            make_block("Part", "h1"),
            make_block("One:", "h1"),
            make_block("Introduction", "h1"),
            make_block("Body", "body"),
        ]
        
        builder = StructureBuilder()
        merged = builder._merge_headers(blocks)
        
        assert len(merged) == 2
        assert merged[0].original_block.text == "Part One: Introduction"
    
    def test_preserves_non_header_blocks(self):
        """_merge_headers() preserves all non-header blocks."""
        blocks = [
            make_block("Body 1", "body"),
            make_block("• List", "list-item"),
            make_block("Chapter", "h1"),
        ]
        
        builder = StructureBuilder()
        merged = builder._merge_headers(blocks)
        
        assert len(merged) == 3
        assert merged[0].role == "body"
        assert merged[1].role == "list-item"
        assert merged[2].role == "h1"

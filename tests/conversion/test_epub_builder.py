"""Test suite for EPUBBuilder."""

import pytest
import zipfile
import tempfile
from pathlib import Path
from lxml import etree

from pdf_to_epub.core.epub_builder import EPUBBuilder
from pdf_to_epub.conversion.models import (
    StructuredContent,
    BookMetadata,
    Chapter,
    Footnote,
    ImageResource,
)


class TestEPUBBuilderBuild:
    """Test EPUBBuilder.build() end-to-end."""
    
    def test_creates_valid_epub_structure(self, tmp_path):
        """build() creates valid EPUB with all required files."""
        metadata = BookMetadata(
            title="Test Book",
            author="Test Author",
            language="en",
            publisher="Test Publisher",
            isbn="1234567890"
        )
        
        chapter = Chapter(
            title="Chapter 1",
            level=1,
            content="<p>Test content</p>",
            footnotes=[]
        )
        
        content = StructuredContent(
            chapters=[chapter],
            metadata=metadata,
            reading_order_confidence=1.0,
            images=[]
        )
        
        output_path = tmp_path / "test.epub"
        builder = EPUBBuilder()
        result = builder.build(content, output_path)
        
        assert result == output_path
        assert output_path.exists()
        
        # Verify it's a valid ZIP
        with zipfile.ZipFile(output_path, 'r') as zf:
            files = zf.namelist()
            
            # Required files
            assert 'mimetype' in files
            assert 'META-INF/container.xml' in files
            assert 'OEBPS/content.opf' in files
            assert 'OEBPS/toc.ncx' in files
            assert 'OEBPS/stylesheet.css' in files
            assert 'OEBPS/chapter1.xhtml' in files
    
    def test_mimetype_is_first_and_uncompressed(self, tmp_path):
        """mimetype must be first file and uncompressed."""
        metadata = BookMetadata(title="Book", author="Author", language="en")
        chapter = Chapter(title="Ch1", level=1, content="<p>test</p>", footnotes=[])
        content = StructuredContent(
            chapters=[chapter],
            metadata=metadata,
            reading_order_confidence=1.0,
            images=[]
        )
        
        output_path = tmp_path / "test.epub"
        builder = EPUBBuilder()
        builder.build(content, output_path)
        
        with zipfile.ZipFile(output_path, 'r') as zf:
            # First file must be mimetype
            first_file = zf.namelist()[0]
            assert first_file == 'mimetype'
            
            # Must be uncompressed (STORED)
            info = zf.getinfo('mimetype')
            assert info.compress_type == zipfile.ZIP_STORED
            
            # Content must be exact
            mimetype_content = zf.read('mimetype').decode('utf-8')
            assert mimetype_content == 'application/epub+zip'
    
    def test_includes_all_chapters(self, tmp_path):
        """build() creates XHTML file for each chapter."""
        metadata = BookMetadata(title="Book", author="Author", language="en")
        chapters = [
            Chapter(title="Chapter 1", level=1, content="<p>Ch1</p>", footnotes=[]),
            Chapter(title="Chapter 2", level=1, content="<p>Ch2</p>", footnotes=[]),
            Chapter(title="Chapter 3", level=1, content="<p>Ch3</p>", footnotes=[]),
        ]
        content = StructuredContent(
            chapters=chapters,
            metadata=metadata,
            reading_order_confidence=1.0,
            images=[]
        )
        
        output_path = tmp_path / "test.epub"
        builder = EPUBBuilder()
        builder.build(content, output_path)
        
        with zipfile.ZipFile(output_path, 'r') as zf:
            assert 'OEBPS/chapter1.xhtml' in zf.namelist()
            assert 'OEBPS/chapter2.xhtml' in zf.namelist()
            assert 'OEBPS/chapter3.xhtml' in zf.namelist()
    
    def test_includes_images(self, tmp_path):
        """build() saves images to OEBPS/images/ folder."""
        metadata = BookMetadata(title="Book", author="Author", language="en")
        chapter = Chapter(title="Ch1", level=1, content="<p>test</p>", footnotes=[])
        
        image1 = ImageResource(
            id="img-1",
            filename="image001.png",
            data=b"PNG_DATA",
            format="png",
            width=100,
            height=100,
            page_num=1
        )
        image2 = ImageResource(
            id="img-2",
            filename="image002.jpg",
            data=b"JPEG_DATA",
            format="jpeg",
            width=200,
            height=200,
            page_num=2
        )
        
        content = StructuredContent(
            chapters=[chapter],
            metadata=metadata,
            reading_order_confidence=1.0,
            images=[image1, image2]
        )
        
        output_path = tmp_path / "test.epub"
        builder = EPUBBuilder()
        builder.build(content, output_path)
        
        with zipfile.ZipFile(output_path, 'r') as zf:
            assert 'OEBPS/images/image001.png' in zf.namelist()
            assert 'OEBPS/images/image002.jpg' in zf.namelist()
            
            # Verify image data
            assert zf.read('OEBPS/images/image001.png') == b"PNG_DATA"
            assert zf.read('OEBPS/images/image002.jpg') == b"JPEG_DATA"


class TestEPUBBuilderContentOPF:
    """Test content.opf generation."""
    
    def test_content_opf_includes_metadata(self, tmp_path):
        """content.opf includes all metadata fields."""
        metadata = BookMetadata(
            title="Test Book",
            author="Test Author",
            language="ru",
            publisher="Test Publisher",
            isbn="1234567890",
            description="Test Description"
        )
        chapter = Chapter(title="Ch1", level=1, content="<p>test</p>", footnotes=[])
        content = StructuredContent(
            chapters=[chapter],
            metadata=metadata,
            reading_order_confidence=1.0,
            images=[]
        )
        
        output_path = tmp_path / "test.epub"
        builder = EPUBBuilder()
        builder.build(content, output_path)
        
        with zipfile.ZipFile(output_path, 'r') as zf:
            opf_content = zf.read('OEBPS/content.opf').decode('utf-8')
            
            assert '<dc:title>Test Book</dc:title>' in opf_content
            assert '<dc:creator>Test Author</dc:creator>' in opf_content
            assert '<dc:language>ru</dc:language>' in opf_content
            assert '<dc:publisher>Test Publisher</dc:publisher>' in opf_content
            assert '<dc:description>Test Description</dc:description>' in opf_content
            assert '1234567890' in opf_content
    
    def test_content_opf_manifest_includes_all_items(self, tmp_path):
        """content.opf manifest includes chapters, images, CSS."""
        metadata = BookMetadata(title="Book", author="Author", language="en")
        chapters = [
            Chapter(title="Ch1", level=1, content="<p>1</p>", footnotes=[]),
            Chapter(title="Ch2", level=1, content="<p>2</p>", footnotes=[]),
        ]
        
        image = ImageResource(
            id="img-1",
            filename="test.png",
            data=b"data",
            format="png",
            width=100,
            height=100,
            page_num=1
        )
        
        content = StructuredContent(
            chapters=chapters,
            metadata=metadata,
            reading_order_confidence=1.0,
            images=[image]
        )
        
        output_path = tmp_path / "test.epub"
        builder = EPUBBuilder()
        builder.build(content, output_path)
        
        with zipfile.ZipFile(output_path, 'r') as zf:
            opf_content = zf.read('OEBPS/content.opf').decode('utf-8')
            
            # Check manifest items
            assert 'id="ncx"' in opf_content
            assert 'href="toc.ncx"' in opf_content
            assert 'id="css"' in opf_content
            assert 'href="stylesheet.css"' in opf_content
            assert 'id="chapter1"' in opf_content
            assert 'href="chapter1.xhtml"' in opf_content
            assert 'id="chapter2"' in opf_content
            assert 'id="img001"' in opf_content
            assert 'href="images/test.png"' in opf_content
    
    def test_content_opf_spine_has_correct_order(self, tmp_path):
        """content.opf spine lists chapters in order."""
        metadata = BookMetadata(title="Book", author="Author", language="en")
        chapters = [
            Chapter(title="Ch1", level=1, content="<p>1</p>", footnotes=[]),
            Chapter(title="Ch2", level=1, content="<p>2</p>", footnotes=[]),
            Chapter(title="Ch3", level=1, content="<p>3</p>", footnotes=[]),
        ]
        content = StructuredContent(
            chapters=chapters,
            metadata=metadata,
            reading_order_confidence=1.0,
            images=[]
        )
        
        output_path = tmp_path / "test.epub"
        builder = EPUBBuilder()
        builder.build(content, output_path)
        
        with zipfile.ZipFile(output_path, 'r') as zf:
            opf_content = zf.read('OEBPS/content.opf').decode('utf-8')
            
            # Check spine itemrefs
            assert '<itemref idref="chapter1"/>' in opf_content
            assert '<itemref idref="chapter2"/>' in opf_content
            assert '<itemref idref="chapter3"/>' in opf_content


class TestEPUBBuilderTOC:
    """Test toc.ncx generation."""
    
    def test_toc_includes_all_chapters(self, tmp_path):
        """toc.ncx includes all chapters with correct titles."""
        metadata = BookMetadata(title="Book Title", author="Author", language="en")
        chapters = [
            Chapter(title="Introduction", level=1, content="<p>1</p>", footnotes=[]),
            Chapter(title="Main Content", level=1, content="<p>2</p>", footnotes=[]),
            Chapter(title="Conclusion", level=1, content="<p>3</p>", footnotes=[]),
        ]
        content = StructuredContent(
            chapters=chapters,
            metadata=metadata,
            reading_order_confidence=1.0,
            images=[]
        )
        
        output_path = tmp_path / "test.epub"
        builder = EPUBBuilder()
        builder.build(content, output_path)
        
        with zipfile.ZipFile(output_path, 'r') as zf:
            toc_content = zf.read('OEBPS/toc.ncx').decode('utf-8')
            
            assert '<text>Introduction</text>' in toc_content
            assert '<text>Main Content</text>' in toc_content
            assert '<text>Conclusion</text>' in toc_content
            assert 'src="chapter1.xhtml"' in toc_content
            assert 'src="chapter2.xhtml"' in toc_content
            assert 'src="chapter3.xhtml"' in toc_content
    
    def test_toc_has_correct_play_order(self, tmp_path):
        """toc.ncx navPoints have sequential playOrder."""
        metadata = BookMetadata(title="Book", author="Author", language="en")
        chapters = [
            Chapter(title="Ch1", level=1, content="<p>1</p>", footnotes=[]),
            Chapter(title="Ch2", level=1, content="<p>2</p>", footnotes=[]),
        ]
        content = StructuredContent(
            chapters=chapters,
            metadata=metadata,
            reading_order_confidence=1.0,
            images=[]
        )
        
        output_path = tmp_path / "test.epub"
        builder = EPUBBuilder()
        builder.build(content, output_path)
        
        with zipfile.ZipFile(output_path, 'r') as zf:
            toc_content = zf.read('OEBPS/toc.ncx').decode('utf-8')
            
            assert 'playOrder="1"' in toc_content
            assert 'playOrder="2"' in toc_content


class TestEPUBBuilderChapterXHTML:
    """Test chapter XHTML generation."""
    
    def test_chapter_has_valid_xhtml5_structure(self, tmp_path):
        """Chapter XHTML has proper DOCTYPE and structure."""
        metadata = BookMetadata(title="Book", author="Author", language="en")
        chapter = Chapter(
            title="Test Chapter",
            level=1,
            content="<p>Content here</p>",
            footnotes=[]
        )
        content = StructuredContent(
            chapters=[chapter],
            metadata=metadata,
            reading_order_confidence=1.0,
            images=[]
        )
        
        output_path = tmp_path / "test.epub"
        builder = EPUBBuilder()
        builder.build(content, output_path)
        
        with zipfile.ZipFile(output_path, 'r') as zf:
            chapter_content = zf.read('OEBPS/chapter1.xhtml').decode('utf-8')
            
            assert '<?xml version="1.0" encoding="UTF-8"?>' in chapter_content
            assert '<!DOCTYPE html>' in chapter_content
            assert '<html xmlns="http://www.w3.org/1999/xhtml"' in chapter_content
            assert '<title>Test Chapter</title>' in chapter_content
            assert '<h1>Test Chapter</h1>' in chapter_content
            assert '<p>Content here</p>' in chapter_content
    
    def test_chapter_escapes_html_entities(self, tmp_path):
        """Chapter XHTML escapes special characters in title."""
        metadata = BookMetadata(title="Book", author="Author", language="en")
        chapter = Chapter(
            title="Chapter & Section <1>",
            level=1,
            content="<p>Test</p>",
            footnotes=[]
        )
        content = StructuredContent(
            chapters=[chapter],
            metadata=metadata,
            reading_order_confidence=1.0,
            images=[]
        )
        
        output_path = tmp_path / "test.epub"
        builder = EPUBBuilder()
        builder.build(content, output_path)
        
        with zipfile.ZipFile(output_path, 'r') as zf:
            chapter_content = zf.read('OEBPS/chapter1.xhtml').decode('utf-8')
            
            # Should escape & and < in title
            assert '&amp;' in chapter_content
            assert '&lt;' in chapter_content
    
    def test_chapter_links_stylesheet(self, tmp_path):
        """Chapter XHTML links to stylesheet.css."""
        metadata = BookMetadata(title="Book", author="Author", language="en")
        chapter = Chapter(title="Ch1", level=1, content="<p>test</p>", footnotes=[])
        content = StructuredContent(
            chapters=[chapter],
            metadata=metadata,
            reading_order_confidence=1.0,
            images=[]
        )
        
        output_path = tmp_path / "test.epub"
        builder = EPUBBuilder()
        builder.build(content, output_path)
        
        with zipfile.ZipFile(output_path, 'r') as zf:
            chapter_content = zf.read('OEBPS/chapter1.xhtml').decode('utf-8')
            
            assert '<link rel="stylesheet" href="stylesheet.css"/>' in chapter_content


class TestEPUBBuilderHelpers:
    """Test helper methods."""
    
    def test_escape_html(self):
        """_escape_html() escapes special characters."""
        builder = EPUBBuilder()
        
        assert builder._escape_html("Normal text") == "Normal text"
        assert builder._escape_html("A & B") == "A &amp; B"
        assert builder._escape_html("<tag>") == "&lt;tag&gt;"
        assert builder._escape_html("\"quoted\"") == "&quot;quoted&quot;"
        # Python's html.escape uses &#39; instead of &apos;
        assert builder._escape_html("'apostrophe'") == "&#39;apostrophe&#39;"
        assert builder._get_media_type("gif") == "image/gif"

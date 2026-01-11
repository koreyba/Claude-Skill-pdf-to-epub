# FROZEN: Do not modify - implements EPUB3 specification
# See ~/.claude/skills/pdf-to-epub/reference/architecture.md
"""EPUB file builder."""

import tempfile
import zipfile
import uuid
from pathlib import Path
from datetime import datetime, timezone

from conversion.models import StructuredContent
from conversion.detectors.footnote_detector import FootnoteDetector
from conversion.detectors.endnote_formatter import EndnoteFormatter


class EPUBBuilder:
    """
    Builds valid EPUB3 files from structured content.
    
    Creates proper EPUB structure with:
    - mimetype file (uncompressed)
    - META-INF/container.xml
    - OEBPS/content.opf (metadata, manifest, spine)
    - OEBPS/toc.ncx (navigation)
    - OEBPS/chapterN.xhtml files
    - OEBPS/images/ folder
    - OEBPS/stylesheet.css
    """
    
    def build(self, content: StructuredContent, output_path: Path) -> Path:
        """
        Build EPUB3 file from structured content.
        
        Args:
            content: StructuredContent with chapters, metadata, images
            output_path: Path for output EPUB file
            
        Returns:
            Path to created EPUB file
        """
        # Create temporary directory for EPUB structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Step 1: Create EPUB directory structure
            self._create_directory_structure(temp_path)
            
            # Step 2: Write mimetype file (must be first, uncompressed)
            self._write_mimetype(temp_path)
            
            # Step 3: Write META-INF/container.xml
            self._write_container_xml(temp_path)
            
            # Step 4: Save images to OEBPS/images/
            self._save_images(temp_path, content.images)
            
            # Step 5: Write chapter XHTML files (with embedded images)
            self._write_chapters(temp_path, content.chapters, content.images)
            
            # Step 6: Write stylesheet
            self._write_stylesheet(temp_path)
            
            # Step 7: Write content.opf (metadata, manifest, spine)
            self._write_content_opf(temp_path, content)
            
            # Step 8: Write toc.ncx (navigation)
            self._write_toc_ncx(temp_path, content)
            
            # Step 9: Package as ZIP with .epub extension
            self._package_epub(temp_path, output_path)
        
        return output_path
    
    def _create_directory_structure(self, temp_path: Path):
        """Create EPUB directory structure."""
        (temp_path / "META-INF").mkdir(exist_ok=True)
        (temp_path / "OEBPS").mkdir(exist_ok=True)
        (temp_path / "OEBPS" / "images").mkdir(exist_ok=True)
    
    def _write_mimetype(self, temp_path: Path):
        """Write mimetype file (must be uncompressed)."""
        mimetype_path = temp_path / "mimetype"
        mimetype_path.write_text("application/epub+zip", encoding="utf-8")
    
    def _write_container_xml(self, temp_path: Path):
        """Write META-INF/container.xml."""
        container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
        
        container_path = temp_path / "META-INF" / "container.xml"
        container_path.write_text(container_xml, encoding="utf-8")
    
    def _save_images(self, temp_path: Path, images):
        """Save images to OEBPS/images/ folder."""
        images_dir = temp_path / "OEBPS" / "images"
        
        for image in images:
            image_path = images_dir / image.filename
            image_path.write_bytes(image.data)
    
    def _write_chapters(self, temp_path: Path, chapters, images=None):
        """Write chapter XHTML files with embedded images."""
        images = images or []

        # Find endnotes chapter to get its filename for hyperlinks
        endnotes_filename = None
        for i, chapter in enumerate(chapters, start=1):
            if hasattr(chapter, 'is_endnotes') and chapter.is_endnotes:
                endnotes_filename = f"chapter{i}.xhtml"
                break

        # Build page-to-chapter mapping to assign images to chapters
        chapter_page_ranges = []
        for i, chapter in enumerate(chapters, start=1):
            pages = self._get_chapter_pages(chapter)
            chapter_page_ranges.append((i, pages))

        for i, chapter in enumerate(chapters, start=1):
            chapter_path = temp_path / "OEBPS" / f"chapter{i}.xhtml"

            # Get images for this chapter based on page numbers
            chapter_pages = chapter_page_ranges[i-1][1]
            chapter_images = [img for img in images if img.page_num in chapter_pages]

            chapter_html = self._generate_chapter_xhtml(
                chapter, i, endnotes_filename if endnotes_filename else None, chapter_images
            )
            chapter_path.write_text(chapter_html, encoding="utf-8")

    def _get_chapter_pages(self, chapter) -> set:
        """Get the set of page numbers covered by a chapter."""
        pages = set()
        if hasattr(chapter, 'content_blocks'):
            for block in chapter.content_blocks:
                if hasattr(block, 'original_block') and hasattr(block.original_block, 'page'):
                    pages.add(block.original_block.page)
        if hasattr(chapter, 'subchapters'):
            for sub in chapter.subchapters:
                pages.update(self._get_chapter_pages(sub))
        return pages
    
    def _generate_chapter_xhtml(
        self, chapter, chapter_num: int, endnotes_filename: str | None = None, images: list | None = None
    ) -> str:
        """Generate XHTML content for a chapter with embedded images."""
        images = images or []

        # Escape HTML entities
        title = self._escape_html(chapter.title)

        # Check if this is the endnotes chapter
        is_endnotes = hasattr(chapter, 'is_endnotes') and chapter.is_endnotes

        if is_endnotes:
            # Use EndnoteFormatter for endnotes chapter
            content = self._generate_endnotes_content(chapter)
        elif hasattr(chapter, 'get_text'):
            # Plain text - need to wrap in <p> tags with footnote hyperlinks
            raw_text = chapter.get_text()
            content = self._text_to_html_with_footnotes(raw_text, endnotes_filename)
        elif hasattr(chapter, 'content'):
            content = chapter.content  # Already HTML from tests
        else:
            content = ""

        # Generate image HTML for this chapter
        images_html = self._generate_images_html(images)

        # Set epub:type based on chapter type
        epub_type = "endnotes" if is_endnotes else "chapter"

        xhtml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>{title}</title>
  <link rel="stylesheet" href="stylesheet.css"/>
</head>
<body>
  <section epub:type="{epub_type}" id="chapter{chapter_num}">
    <h1>{title}</h1>
{images_html}
    {content}
  </section>
</body>
</html>'''

        return xhtml

    def _generate_images_html(self, images: list) -> str:
        """Generate HTML for chapter images."""
        if not images:
            return ""

        html_parts = []
        for img in images:
            # Generate img tag with alt text
            alt_text = f"Image from page {img.page_num}"
            html_parts.append(
                f'    <figure class="chapter-image">\n'
                f'      <img src="images/{img.filename}" alt="{alt_text}"/>\n'
                f'    </figure>'
            )

        return '\n'.join(html_parts)

    def _generate_endnotes_content(self, chapter) -> str:
        """Generate HTML content for endnotes chapter using EndnoteFormatter."""
        if not hasattr(chapter, 'content_blocks'):
            return ""

        formatter = EndnoteFormatter()
        return formatter.format_endnotes(chapter.content_blocks)

    def _text_to_html_with_footnotes(self, text: str, endnotes_filename: str | None = None) -> str:
        """Convert plain text to HTML with paragraph tags and footnote hyperlinks."""
        if not text:
            return ""

        # Split by double newlines (paragraph breaks)
        paragraphs = text.split('\n\n')

        # Create footnote detector for hyperlink conversion
        detector = FootnoteDetector() if endnotes_filename else None

        html_parts = []
        for para in paragraphs:
            # Clean up single newlines within paragraph
            para = para.replace('\n', ' ').strip()
            if para:
                # Escape HTML first
                escaped = self._escape_html(para)
                # Then convert footnote references to hyperlinks
                if detector and endnotes_filename:
                    escaped = detector.convert_to_hyperlinks(escaped, endnotes_filename)
                html_parts.append(f'    <p>{escaped}</p>')

        return '\n'.join(html_parts)

    def _text_to_html(self, text: str) -> str:
        """Convert plain text to HTML with proper paragraph tags."""
        if not text:
            return ""

        # Split by double newlines (paragraph breaks)
        paragraphs = text.split('\n\n')

        html_parts = []
        for para in paragraphs:
            # Clean up single newlines within paragraph
            para = para.replace('\n', ' ').strip()
            if para:
                # Escape HTML and wrap in <p>
                escaped = self._escape_html(para)
                html_parts.append(f'    <p>{escaped}</p>')

        return '\n'.join(html_parts)
    
    def _write_stylesheet(self, temp_path: Path):
        """Write basic CSS stylesheet."""
        css = '''body {
    font-family: serif;
    line-height: 1.6;
    margin: 1em;
}

h1 {
    font-size: 1.8em;
    margin-top: 1em;
    margin-bottom: 0.5em;
}

p {
    margin: 0.5em 0;
    text-align: justify;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
}

/* Chapter images */
.chapter-image {
    margin: 1.5em auto;
    text-align: center;
}

.chapter-image img {
    max-width: 100%;
    height: auto;
}

/* Footnote reference links in main text */
.footnote-ref {
    text-decoration: none;
    color: #0066cc;
}

.footnote-ref sup {
    font-size: 0.8em;
    vertical-align: super;
}

/* Endnotes section */
.endnote {
    margin: 0.8em 0;
    font-size: 0.95em;
    line-height: 1.5;
}

.endnote-num {
    font-weight: bold;
    color: #333;
}

.endnote-backlink {
    text-decoration: none;
    color: #0066cc;
    font-size: 0.85em;
}
'''
        
        css_path = temp_path / "OEBPS" / "stylesheet.css"
        css_path.write_text(css, encoding="utf-8")
    
    def _write_content_opf(self, temp_path: Path, content: StructuredContent):
        """Write OEBPS/content.opf (package document)."""
        book_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        metadata = content.metadata
        
        # Build manifest items
        manifest_items = []
        manifest_items.append('    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')
        manifest_items.append('    <item id="css" href="stylesheet.css" media-type="text/css"/>')
        
        # Add chapter items
        for i in range(len(content.chapters)):
            manifest_items.append(f'    <item id="chapter{i+1}" href="chapter{i+1}.xhtml" media-type="application/xhtml+xml"/>')
        
        # Add image items
        for i, image in enumerate(content.images, start=1):
            media_type = self._get_media_type(image.format)
            manifest_items.append(f'    <item id="img{i:03d}" href="images/{image.filename}" media-type="{media_type}"/>')
        
        manifest_xml = '\n'.join(manifest_items)
        
        # Build spine
        spine_items = []
        for i in range(len(content.chapters)):
            spine_items.append(f'    <itemref idref="chapter{i+1}"/>')
        
        spine_xml = '\n'.join(spine_items)
        
        # Optional metadata
        publisher_xml = f'    <dc:publisher>{self._escape_html(metadata.publisher)}</dc:publisher>' if metadata.publisher else ''
        isbn_xml = f'    <dc:identifier id="isbn">{metadata.isbn}</dc:identifier>' if metadata.isbn else ''
        description_xml = f'    <dc:description>{self._escape_html(metadata.description)}</dc:description>' if metadata.description else ''
        
        opf_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">{book_id}</dc:identifier>
    <dc:title>{self._escape_html(metadata.title)}</dc:title>
    <dc:creator>{self._escape_html(metadata.author)}</dc:creator>
    <dc:language>{metadata.language}</dc:language>
{publisher_xml}
{isbn_xml}
{description_xml}
    <meta property="dcterms:modified">{timestamp}</meta>
  </metadata>
  
  <manifest>
{manifest_xml}
  </manifest>
  
  <spine toc="ncx">
{spine_xml}
  </spine>
</package>'''
        
        opf_path = temp_path / "OEBPS" / "content.opf"
        opf_path.write_text(opf_content, encoding="utf-8")
    
    def _write_toc_ncx(self, temp_path: Path, content: StructuredContent):
        """Write OEBPS/toc.ncx (table of contents)."""
        book_id = str(uuid.uuid4())
        
        # Build nav points
        nav_points = []
        for i, chapter in enumerate(content.chapters, start=1):
            title = self._escape_html(chapter.title)
            nav_points.append(f'''    <navPoint id="chapter{i}" playOrder="{i}">
      <navLabel>
        <text>{title}</text>
      </navLabel>
      <content src="chapter{i}.xhtml"/>
    </navPoint>''')
        
        nav_points_xml = '\n'.join(nav_points)
        
        ncx_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{book_id}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  
  <docTitle>
    <text>{self._escape_html(content.metadata.title)}</text>
  </docTitle>
  
  <navMap>
{nav_points_xml}
  </navMap>
</ncx>'''
        
        ncx_path = temp_path / "OEBPS" / "toc.ncx"
        ncx_path.write_text(ncx_content, encoding="utf-8")
    
    def _package_epub(self, temp_path: Path, output_path: Path):
        """Package EPUB directory as ZIP file."""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as epub:
            # mimetype MUST be first and uncompressed
            epub.write(temp_path / 'mimetype', 'mimetype', compress_type=zipfile.ZIP_STORED)
            
            # Add all other files
            for file_path in temp_path.rglob('*'):
                if file_path.is_file() and file_path.name != 'mimetype':
                    arcname = file_path.relative_to(temp_path)
                    epub.write(file_path, arcname, compress_type=zipfile.ZIP_DEFLATED)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))
    
    def _get_media_type(self, image_format: str) -> str:
        """Get MIME type for image format."""
        format_map = {
            'png': 'image/png',
            'jpeg': 'image/jpeg',
            'jpg': 'image/jpeg',
            'gif': 'image/gif',
        }
        return format_map.get(image_format.lower(), 'image/png')

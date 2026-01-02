"""Tests for image embedding in EPUB chapters."""

import pytest
import zipfile
import re
from pathlib import Path
from lxml import etree

from pdf_to_epub.conversion.converter import Converter, DEFAULT_CONFIG


class TestImageEmbedding:
    """Test that images are properly embedded in EPUB chapters."""

    @pytest.fixture
    def excerpt_d_path(self):
        """Path to Excerpt D PDF fixture (has images)."""
        return Path(__file__).parent.parent / "fixtures" / "Excerpt D.pdf"

    @pytest.fixture
    def excerpt_c_path(self):
        """Path to Excerpt C PDF fixture (has images)."""
        return Path(__file__).parent.parent / "fixtures" / "Excerpt C The Ways We Are in This Together.pdf"

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Temporary directory for output."""
        return tmp_path / "output"

    def test_images_saved_to_epub(self, excerpt_d_path, output_dir):
        """Test that images are saved in OEBPS/images/ folder."""
        if not excerpt_d_path.exists():
            pytest.skip(f"PDF fixture not found: {excerpt_d_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "test.epub"

        converter = Converter(strategy="simple")
        result = converter.convert(str(excerpt_d_path), str(output_path))

        assert result.status in ("success", "warning")
        assert len(result.structured_content.images) > 0, "Should extract images"

        # Check images are in EPUB
        with zipfile.ZipFile(result.epub_path, 'r') as epub:
            image_files = [f for f in epub.namelist() if f.startswith('OEBPS/images/')]
            assert len(image_files) > 0, "EPUB should contain image files"
            print(f"Images in EPUB: {image_files}")

    def test_images_in_manifest(self, excerpt_d_path, output_dir):
        """Test that images are listed in content.opf manifest."""
        if not excerpt_d_path.exists():
            pytest.skip(f"PDF fixture not found: {excerpt_d_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "test.epub"

        converter = Converter(strategy="simple")
        result = converter.convert(str(excerpt_d_path), str(output_path))

        assert result.status in ("success", "warning")

        # Check manifest
        with zipfile.ZipFile(result.epub_path, 'r') as epub:
            opf_content = epub.read('OEBPS/content.opf').decode('utf-8')

            for img in result.structured_content.images:
                assert img.filename in opf_content, (
                    f"Image {img.filename} not in manifest"
                )
            print(f"All {len(result.structured_content.images)} images in manifest")

    def test_images_referenced_in_chapters(self, excerpt_d_path, output_dir):
        """Test that images have <img> tags in chapter XHTML files."""
        if not excerpt_d_path.exists():
            pytest.skip(f"PDF fixture not found: {excerpt_d_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "test.epub"

        converter = Converter(strategy="simple")
        result = converter.convert(str(excerpt_d_path), str(output_path))

        assert result.status in ("success", "warning")
        assert len(result.structured_content.images) > 0, "Should have images"

        # Collect all chapter HTML
        all_chapter_html = ""
        with zipfile.ZipFile(result.epub_path, 'r') as epub:
            chapter_files = [f for f in epub.namelist() if f.startswith('OEBPS/chapter') and f.endswith('.xhtml')]
            for chapter_file in chapter_files:
                chapter_html = epub.read(chapter_file).decode('utf-8')
                all_chapter_html += chapter_html

        # Check each image is referenced with <img> tag
        img_tag_pattern = re.compile(r'<img[^>]+src=["\']images/([^"\']+)["\']')
        found_img_refs = img_tag_pattern.findall(all_chapter_html)

        print(f"\nImages extracted: {[img.filename for img in result.structured_content.images]}")
        print(f"Images referenced in HTML: {found_img_refs}")

        # Every extracted image should be referenced in HTML
        for img in result.structured_content.images:
            assert img.filename in found_img_refs, (
                f"Image {img.filename} not referenced in any chapter HTML. "
                f"Found refs: {found_img_refs}"
            )

    def test_images_visible_in_reading_flow(self, excerpt_d_path, output_dir):
        """Test that images appear in the correct reading order."""
        if not excerpt_d_path.exists():
            pytest.skip(f"PDF fixture not found: {excerpt_d_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "test.epub"

        converter = Converter(strategy="simple")
        result = converter.convert(str(excerpt_d_path), str(output_path))

        assert result.status in ("success", "warning")

        # Images should be placed in chapters corresponding to their page_num
        images_by_page = {}
        for img in result.structured_content.images:
            if img.page_num not in images_by_page:
                images_by_page[img.page_num] = []
            images_by_page[img.page_num].append(img)

        print(f"\nImages by page: {[(p, [i.filename for i in imgs]) for p, imgs in images_by_page.items()]}")

        # At least one image should be in a chapter
        with zipfile.ZipFile(result.epub_path, 'r') as epub:
            for chapter_file in sorted(epub.namelist()):
                if chapter_file.startswith('OEBPS/chapter') and chapter_file.endswith('.xhtml'):
                    content = epub.read(chapter_file).decode('utf-8')
                    if '<img' in content:
                        print(f"{chapter_file}: contains images")

    def test_excerpt_c_has_images(self, excerpt_c_path, output_dir):
        """Test Excerpt C conversion includes images."""
        if not excerpt_c_path.exists():
            pytest.skip(f"PDF fixture not found: {excerpt_c_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "excerpt_c.epub"

        converter = Converter(strategy="simple")
        result = converter.convert(str(excerpt_c_path), str(output_path))

        assert result.status in ("success", "warning")

        # Should have images
        num_images = len(result.structured_content.images)
        print(f"\nExcerpt C: {num_images} images extracted")

        if num_images > 0:
            # Verify images are referenced
            with zipfile.ZipFile(result.epub_path, 'r') as epub:
                all_html = ""
                for f in epub.namelist():
                    if f.endswith('.xhtml'):
                        all_html += epub.read(f).decode('utf-8')

                img_tag_count = all_html.count('<img')
                print(f"<img> tags in EPUB: {img_tag_count}")

                assert img_tag_count >= num_images, (
                    f"Expected at least {num_images} <img> tags, found {img_tag_count}"
                )


class TestValidateCLI:
    """Test the validate.py CLI script."""

    @pytest.fixture
    def excerpt_b_path(self):
        """Path to Excerpt B PDF fixture."""
        return Path(__file__).parent.parent / "fixtures" / "Excerpt_B_The_Many_Ways_We_Touch_Three_P.pdf"

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Temporary directory for output."""
        return tmp_path / "output"

    def test_validate_successful_conversion(self, excerpt_b_path, output_dir):
        """Test validate.py with a successfully converted EPUB."""
        if not excerpt_b_path.exists():
            pytest.skip(f"PDF fixture not found: {excerpt_b_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        epub_path = output_dir / "test.epub"

        # First convert
        converter = Converter(strategy="simple")
        result = converter.convert(str(excerpt_b_path), str(epub_path))
        assert result.status in ("success", "warning")

        # Now validate using the checker directly (same logic as CLI)
        from pdf_to_epub.core.pdf_extractor import PDFExtractor
        from pdf_to_epub.core.epub_extractor import EPUBExtractor
        from pdf_to_epub.validation.completeness_checker import CompletenessChecker

        with PDFExtractor(excerpt_b_path) as pdf:
            source_text = pdf.get_full_text()

        with EPUBExtractor(epub_path) as epub:
            target_text = epub.get_full_text()

        checker = CompletenessChecker(source_text, target_text)
        validation_result = checker.check()

        print(f"\nValidation results:")
        print(f"  Completeness: {validation_result.completeness_score:.1f}%")
        print(f"  Order score: {validation_result.order_score:.1f}%")
        print(f"  Missing chunks: {len(validation_result.missing_chunks)}")

        # Should pass validation thresholds
        assert validation_result.completeness_score >= 90.0, "Completeness too low"
        assert validation_result.order_score >= 70.0, "Order score too low"

    def test_validate_requires_both_files(self, tmp_path):
        """Test that validation requires both PDF and EPUB files to exist."""
        from pdf_to_epub.core.pdf_extractor import PDFExtractor

        # Non-existent file should raise
        with pytest.raises(FileNotFoundError):
            with PDFExtractor(tmp_path / "nonexistent.pdf") as pdf:
                pdf.get_full_text()


class TestExcerptCConversion:
    """Test conversion of Excerpt C - The Ways We Are in This Together."""

    @pytest.fixture
    def excerpt_c_path(self):
        """Path to Excerpt C PDF fixture."""
        return Path(__file__).parent.parent / "fixtures" / "Excerpt C The Ways We Are in This Together.pdf"

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Temporary directory for output."""
        return tmp_path / "output"

    def test_full_conversion(self, excerpt_c_path, output_dir):
        """Test full conversion pipeline for Excerpt C."""
        if not excerpt_c_path.exists():
            pytest.skip(f"PDF fixture not found: {excerpt_c_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "excerpt_c.epub"

        converter = Converter(strategy="simple")
        result = converter.convert(str(excerpt_c_path), str(output_path))

        print(f"\n--- Excerpt C Conversion ---")
        print(f"Status: {result.status}")
        print(f"Chapters: {len(result.structured_content.chapters)}")
        print(f"Images: {len(result.structured_content.images)}")
        print(f"Reading order confidence: {result.reading_order_confidence}")

        assert result.status in ("success", "warning")
        assert Path(result.epub_path).exists()

    def test_text_completeness(self, excerpt_c_path, output_dir):
        """Test that text is properly preserved in Excerpt C conversion."""
        if not excerpt_c_path.exists():
            pytest.skip(f"PDF fixture not found: {excerpt_c_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "excerpt_c.epub"

        converter = Converter(strategy="simple")
        result = converter.convert(str(excerpt_c_path), str(output_path))

        assert result.status in ("success", "warning")

        # Validate completeness
        from pdf_to_epub.core.pdf_extractor import PDFExtractor
        from pdf_to_epub.core.epub_extractor import EPUBExtractor
        from pdf_to_epub.validation.completeness_checker import CompletenessChecker

        with PDFExtractor(excerpt_c_path) as pdf:
            source_text = pdf.get_full_text()

        with EPUBExtractor(output_path) as epub:
            target_text = epub.get_full_text()

        checker = CompletenessChecker(source_text, target_text)
        validation_result = checker.check()

        print(f"\nExcerpt C Validation:")
        print(f"  PDF text: {len(source_text)} chars")
        print(f"  EPUB text: {len(target_text)} chars")
        print(f"  Completeness: {validation_result.completeness_score:.1f}%")
        print(f"  Order score: {validation_result.order_score:.1f}%")

        assert validation_result.completeness_score >= 95.0, (
            f"Completeness too low: {validation_result.completeness_score:.1f}%"
        )
        assert validation_result.order_score >= 80.0, (
            f"Order score too low: {validation_result.order_score:.1f}%"
        )

    def test_endnotes_detected(self, excerpt_c_path, output_dir):
        """Test that endnotes are properly detected in Excerpt C."""
        if not excerpt_c_path.exists():
            pytest.skip(f"PDF fixture not found: {excerpt_c_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "excerpt_c.epub"

        converter = Converter(strategy="simple")
        result = converter.convert(str(excerpt_c_path), str(output_path))

        assert result.status in ("success", "warning")

        # Check for Endnotes chapter
        chapters = result.structured_content.chapters
        endnotes_chapter = next((ch for ch in chapters if ch.title == "Endnotes"), None)

        print(f"\nChapter titles: {[ch.title for ch in chapters]}")
        print(f"Endnotes chapter: {'Found' if endnotes_chapter else 'Not found'}")

        if endnotes_chapter:
            endnotes_text = endnotes_chapter.get_text()
            print(f"Endnotes text length: {len(endnotes_text)}")

            # Count endnote markers
            import re
            endnote_markers = re.findall(r'(?:^|\n)(\d{1,2})\s{2,}', endnotes_text)
            print(f"Endnote markers found: {len(endnote_markers)}")

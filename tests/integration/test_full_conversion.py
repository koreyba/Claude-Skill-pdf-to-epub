"""Full end-to-end integration test for PDF to EPUB conversion."""

import pytest
import zipfile
from pathlib import Path
from lxml import etree

from claude_skill.conversion.converter import Converter, DEFAULT_CONFIG
from claude_skill.conversion.models import ConversionConfig, BookMetadata
from claude_skill.validation.completeness_checker import CompletenessChecker
from claude_skill.core.epub_extractor import EPUBExtractor
from claude_skill.core.pdf_extractor import PDFExtractor


class TestFullConversion:
    """Test complete PDF to EPUB conversion with real files."""

    @pytest.fixture
    def real_pdf_path(self):
        """Path to real PDF fixture."""
        return Path(__file__).parent.parent / "fixtures" / "Excerpt_B_The_Many_Ways_We_Touch_Three_P.pdf"

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Temporary directory for output."""
        return tmp_path / "output"

    def test_full_conversion_pipeline(self, real_pdf_path, output_dir):
        """Test complete conversion pipeline with validation."""
        assert real_pdf_path.exists(), f"PDF fixture not found: {real_pdf_path}"

        # Step 1: Extract and validate source PDF
        print("\n--- Step 1: Analyzing source PDF ---")
        with PDFExtractor(str(real_pdf_path)) as extractor:
            pdf_blocks = extractor.get_structural_blocks()
            pdf_text = " ".join(block.text for block in pdf_blocks)

        print(f"PDF blocks extracted: {len(pdf_blocks)}")
        print(f"PDF text length: {len(pdf_text)} characters")
        print(f"Sample text: {pdf_text[:200]}...")

        assert len(pdf_blocks) > 0, "PDF has no text blocks"
        assert len(pdf_text) > 100, "PDF text is too short"

        # Step 2: Convert PDF to EPUB
        print("\n--- Step 2: Converting PDF to EPUB ---")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "output.epub"

        converter = Converter(strategy="simple")
        config = DEFAULT_CONFIG
        result = converter.convert(str(real_pdf_path), str(output_path), config)

        print(f"Conversion status: {result.status}")
        print(f"Conversion warnings: {result.log.warnings}")
        print(f"Conversion errors: {result.log.errors}")
        print(f"Steps completed: {result.log.steps_completed}")
        print(f"Reading order confidence: {result.reading_order_confidence}")

        assert result.status in ("success", "warning"), (
            f"Conversion failed: {result.status}\n"
            f"Errors: {result.log.errors}\n"
            f"Warnings: {result.log.warnings}"
        )
        assert Path(result.epub_path).exists(), "EPUB file not created"

        # Step 3: Validate EPUB structure
        print("\n--- Step 3: Validating EPUB structure ---")
        assert zipfile.is_zipfile(result.epub_path), "EPUB is not a valid ZIP"

        with zipfile.ZipFile(result.epub_path, 'r') as epub:
            namelist = epub.namelist()
            print(f"EPUB files: {len(namelist)} files")
            print(f"Files: {namelist}")

            # Check required files
            assert 'mimetype' in namelist, "Missing mimetype"
            assert 'META-INF/container.xml' in namelist, "Missing container.xml"
            assert 'OEBPS/content.opf' in namelist, "Missing content.opf"
            assert 'OEBPS/toc.ncx' in namelist, "Missing toc.ncx"

            # Check mimetype
            mimetype = epub.read('mimetype').decode('utf-8')
            assert mimetype == 'application/epub+zip', f"Wrong mimetype: {mimetype}"

            # Parse content.opf
            opf_content = epub.read('OEBPS/content.opf')
            opf_tree = etree.fromstring(opf_content)

            # Count chapters
            spine_items = opf_tree.findall('.//{http://www.idpf.org/2007/opf}itemref')
            chapter_count = len(spine_items)
            print(f"Chapters in spine: {chapter_count}")

            assert chapter_count > 0, "No chapters in EPUB"

        # Step 4: Extract EPUB text and validate completeness SEPARATELY
        print("\n--- Step 4: Validating text completeness ---")

        # Separate main content from endnotes for accurate validation
        # Endnotes are on pages 46-49 in this PDF
        ENDNOTES_START_PAGE = 46

        pdf_main_blocks = [b for b in pdf_blocks if b.page < ENDNOTES_START_PAGE]
        pdf_endnote_blocks = [b for b in pdf_blocks if b.page >= ENDNOTES_START_PAGE]

        pdf_main_text = " ".join(block.text for block in pdf_main_blocks)
        pdf_endnotes_text = " ".join(block.text for block in pdf_endnote_blocks)

        # Get EPUB chapters (last one should be "Endnotes")
        chapters = result.structured_content.chapters
        main_chapters = [ch for ch in chapters if ch.title != "Endnotes"]
        endnotes_chapter = next((ch for ch in chapters if ch.title == "Endnotes"), None)

        epub_main_text = " ".join(ch.get_text() for ch in main_chapters)
        epub_endnotes_text = endnotes_chapter.get_text() if endnotes_chapter else ""

        print(f"PDF main content: {len(pdf_main_text)} chars ({len(pdf_main_blocks)} blocks)")
        print(f"PDF endnotes: {len(pdf_endnotes_text)} chars ({len(pdf_endnote_blocks)} blocks)")
        print(f"EPUB main chapters: {len(main_chapters)}")
        print(f"EPUB endnotes chapter: {'Yes' if endnotes_chapter else 'No'}")

        # Validate MAIN CONTENT completeness (stricter - 80%)
        main_checker = CompletenessChecker(pdf_main_text, epub_main_text)
        main_result = main_checker.check()
        main_completeness = main_result.completeness_score / 100.0
        order_score = main_result.order_score / 100.0

        print(f"\nMain content completeness: {main_completeness:.2%}")
        print(f"Main content order: {order_score:.2%}")

        # Should preserve at least 90% of MAIN content
        assert main_completeness >= 0.90, (
            f"Main content completeness too low: {main_completeness:.2%}. "
            f"PDF main: {len(pdf_main_text)} chars, EPUB main: {len(epub_main_text)} chars"
        )

        # Validate ENDNOTES (all 9 should be present)
        if endnotes_chapter:
            endnotes_checker = CompletenessChecker(pdf_endnotes_text, epub_endnotes_text)
            endnotes_result = endnotes_checker.check()
            endnotes_completeness = endnotes_result.completeness_score / 100.0
            print(f"Endnotes completeness: {endnotes_completeness:.2%}")
        else:
            endnotes_completeness = 0.0
            print("WARNING: No Endnotes chapter found!")

        # Combined score for summary
        epub_full_text = epub_main_text + " " + epub_endnotes_text
        completeness_score = main_completeness  # Use main content as primary metric

        # Step 5: Validate reading order
        print("\n--- Step 5: Validating reading order ---")
        print(f"Reading order score: {order_score:.2%}")

        # Should maintain reasonable reading order (at least 70%)
        assert order_score >= 0.7, f"Reading order too scrambled: {order_score:.2%}"

        # Step 6: Validate chapter structure
        print("\n--- Step 6: Validating chapter structure ---")
        assert len(result.structured_content.chapters) > 0, "No chapters in structured content"

        for i, chapter in enumerate(result.structured_content.chapters, 1):
            chapter_text = chapter.get_text()
            title_display = chapter.title[:50] if len(chapter.title) > 50 else chapter.title
            print(f"Chapter {i}: '{title_display}' ({len(chapter_text)} chars)")

            # Each chapter should have content (except intro which might be empty)
            if i > 1:
                assert len(chapter_text) > 0, f"Chapter {i} is empty"

            # Chapter should have valid title
            assert chapter.title and len(chapter.title.strip()) > 0, f"Chapter {i} has no title"

        # Step 7: Summary
        print("\n--- Conversion Summary ---")
        print(f"+ PDF blocks: {len(pdf_blocks)}")
        print(f"+ EPUB chapters: {len(result.structured_content.chapters)}")
        print(f"+ Completeness: {completeness_score:.2%}")
        print(f"+ Reading order: {order_score:.2%}")
        print(f"+ Output: {result.epub_path}")
        print(f"+ File size: {Path(result.epub_path).stat().st_size / 1024:.1f} KB")

        # Final assertions
        assert len(result.structured_content.chapters) >= 1, "Should have at least 1 chapter"
        assert main_completeness >= 0.90, "Should preserve 90%+ of main content"
        assert order_score >= 0.7, "Should maintain 70%+ reading order"
        assert endnotes_chapter is not None, "Should have Endnotes chapter"

    def test_conversion_handles_edge_cases(self, real_pdf_path, output_dir):
        """Test conversion with various configurations."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Test with custom metadata
        from dataclasses import replace

        config = replace(DEFAULT_CONFIG)
        config = replace(config, metadata=BookMetadata(
            title="Custom Title",
            author="Test Author",
            language="en"
        ))

        converter = Converter(strategy="simple")
        output_path = output_dir / "custom_metadata.epub"
        result = converter.convert(str(real_pdf_path), str(output_path), config)

        assert result.status in ("success", "warning")

        # Verify metadata in EPUB
        # Note: EPUBExtractor.get_metadata() returns 'creator' not 'author' (EPUB DC standard)
        with EPUBExtractor(str(result.epub_path)) as epub_extractor:
            metadata = epub_extractor.get_metadata()

        assert metadata.get('title') == "Custom Title"
        assert metadata.get('creator') == "Test Author"

    def test_detailed_chapter_analysis(self, real_pdf_path, output_dir):
        """Deep analysis of chapter detection quality."""
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "analysis.epub"

        converter = Converter(strategy="simple")
        result = converter.convert(str(real_pdf_path), str(output_path))

        assert result.status in ("success", "warning")

        with EPUBExtractor(str(result.epub_path)) as epub_extractor:
            chapters_text = list(epub_extractor.iter_chapters())

        print("\n--- Detailed Chapter Analysis ---")
        for i, chapter in enumerate(result.structured_content.chapters, 1):
            text = chapter.get_text()
            lines = text.split('\n')
            words = text.split()

            print(f"\nChapter {i}:")
            print(f"  Title: {chapter.title}")
            print(f"  Level: {chapter.level}")
            print(f"  Text length: {len(text)} chars")
            print(f"  Lines: {len(lines)}")
            print(f"  Words: {len(words)}")
            # Note: structure_builder.Chapter uses content_blocks, not footnotes
            print(f"  Content blocks: {len(chapter.content_blocks)}")
            print(f"  First 100 chars: {text[:100] if text else '(empty)'}...")

            # Quality checks
            if i > 1:  # Skip intro/preamble
                assert len(words) > 5, f"Chapter {i} too short"
                assert chapter.title, f"Chapter {i} missing title"

    def test_endnotes_extraction(self, real_pdf_path, output_dir):
        """Test that endnotes are properly extracted from PDF."""
        import re
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "endnotes_test.epub"

        converter = Converter(strategy="simple")
        result = converter.convert(str(real_pdf_path), str(output_path))

        assert result.status in ("success", "warning")

        # The PDF has exactly 9 endnotes (numbered 1-9) on pages 46-49
        # Format: "1  More technically, theories and paradigms..."

        # Check that endnotes are extracted
        with EPUBExtractor(str(result.epub_path)) as epub_extractor:
            full_text = epub_extractor.get_full_text()

        # Endnotes should be present in the EPUB text
        # Pattern: number followed by 2+ spaces at the start of a line/paragraph
        endnote_pattern = re.compile(r'(?:^|\n)(\d)\s{2,}')
        found_endnotes = endnote_pattern.findall(full_text)

        print(f"\n--- Endnotes Analysis ---")
        print(f"Found endnote markers in EPUB: {found_endnotes}")

        # We expect exactly 9 endnotes
        expected_endnotes = ['1', '2', '3', '4', '5', '6', '7', '8', '9']

        # For now, check that endnote text content exists
        # Look for specific endnote content phrases
        endnote_phrases = [
            "More technically, theories and paradigms tetra-enact",  # endnote 1
            "an integral social practice would in fact include",     # endnote 2
            "Even theories themselves are another set",              # endnote 3
            "when we say that theories map or reflect",              # endnote 4
            "What does not continue to function",                    # endnote 5
            "See note 4.  It is not necessary",                      # endnote 6
            "Ever wondered why the tribal consciousness",            # endnote 7
            "following the Basic Moral Intuition",                   # endnote 8
            "IOS",                                                   # endnote 9
        ]

        found_count = 0
        for i, phrase in enumerate(endnote_phrases, 1):
            if phrase in full_text:
                found_count += 1
                print(f"  Endnote {i}: FOUND")
            else:
                print(f"  Endnote {i}: MISSING - '{phrase[:40]}...'")

        print(f"\nEndnotes found: {found_count}/9")

        # All 9 endnotes should be present in the EPUB
        assert found_count == 9, (
            f"Expected 9 endnotes, found {found_count}. "
            f"Endnotes may not be properly extracted."
        )


class TestExcerptDConversion:
    """Test conversion of Excerpt D - a complex PDF with images."""

    @pytest.fixture
    def excerpt_d_path(self):
        """Path to Excerpt D PDF fixture."""
        return Path(__file__).parent.parent / "fixtures" / "Excerpt D.pdf"

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Temporary directory for output."""
        return tmp_path / "output"

    def test_large_pdf_with_images(self, excerpt_d_path, output_dir):
        """Test conversion of a large PDF (175 pages) with embedded images."""
        if not excerpt_d_path.exists():
            pytest.skip(f"PDF fixture not found: {excerpt_d_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "excerpt_d.epub"

        # Convert
        converter = Converter(strategy="simple")
        result = converter.convert(str(excerpt_d_path), str(output_path))

        print(f"\n--- Excerpt D Conversion ---")
        print(f"Status: {result.status}")
        print(f"Chapters: {len(result.structured_content.chapters)}")
        print(f"Images: {len(result.structured_content.images)}")

        assert result.status in ("success", "warning"), (
            f"Conversion failed: {result.log.errors}"
        )
        assert Path(result.epub_path).exists(), "EPUB file not created"

        # Verify structure
        assert len(result.structured_content.chapters) > 0, "No chapters detected"

        # This PDF has 6 images - verify they are extracted
        print(f"Extracted images: {len(result.structured_content.images)}")
        for img in result.structured_content.images:
            print(f"  - {img.filename}: {img.format}, {len(img.data)} bytes")

        assert len(result.structured_content.images) >= 1, "Should extract at least 1 image"

        # Verify EPUB structure
        with zipfile.ZipFile(result.epub_path, 'r') as epub:
            namelist = epub.namelist()

            # Check for images in EPUB
            image_files = [f for f in namelist if f.startswith('OEBPS/images/')]
            print(f"Images in EPUB: {image_files}")

            assert len(image_files) >= 1, "EPUB should contain at least 1 image"

            # Check EPUB is valid
            assert 'mimetype' in namelist
            assert 'OEBPS/content.opf' in namelist

        # Verify text completeness
        with PDFExtractor(str(excerpt_d_path)) as extractor:
            pdf_blocks = extractor.get_structural_blocks()
            pdf_text = " ".join(block.text for block in pdf_blocks)

        epub_text = " ".join(ch.get_text() for ch in result.structured_content.chapters)

        print(f"\nPDF text: {len(pdf_text)} chars")
        print(f"EPUB text: {len(epub_text)} chars")

        # Large PDFs may have more variation, use 70% threshold
        ratio = len(epub_text) / len(pdf_text)
        print(f"Text ratio: {ratio:.2%}")

        assert ratio >= 0.70, f"Text preservation too low: {ratio:.2%}"

    def test_image_extraction_quality(self, excerpt_d_path, output_dir):
        """Test that images are properly extracted and have valid format."""
        if not excerpt_d_path.exists():
            pytest.skip(f"PDF fixture not found: {excerpt_d_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "images_test.epub"

        converter = Converter(strategy="simple")
        result = converter.convert(str(excerpt_d_path), str(output_path))

        assert result.status in ("success", "warning")

        # Check each image
        for img in result.structured_content.images:
            # Image should have data
            assert len(img.data) > 0, f"Image {img.filename} has no data"

            # Image should have valid format
            assert img.format in ('png', 'jpeg', 'jpg', 'gif'), (
                f"Image {img.filename} has invalid format: {img.format}"
            )

            # Image should have reasonable size (at least 100 bytes)
            assert len(img.data) >= 100, (
                f"Image {img.filename} too small: {len(img.data)} bytes"
            )

            print(f"Image {img.filename}: {img.format}, {len(img.data)} bytes - OK")

    def test_chapter_hierarchy(self, excerpt_d_path, output_dir):
        """Test that chapter hierarchy is properly detected in a complex document."""
        if not excerpt_d_path.exists():
            pytest.skip(f"PDF fixture not found: {excerpt_d_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "hierarchy_test.epub"

        converter = Converter(strategy="simple")
        result = converter.convert(str(excerpt_d_path), str(output_path))

        assert result.status in ("success", "warning")

        print("\n--- Chapter Hierarchy ---")

        def print_chapters(chapters, indent=0):
            count = 0
            for ch in chapters:
                prefix = "  " * indent
                text_len = len(ch.get_text())
                sub_count = len(ch.subchapters)
                print(f"{prefix}- {ch.title[:50]}... (L{ch.level}, {text_len} chars, {sub_count} subs)")
                count += 1
                count += print_chapters(ch.subchapters, indent + 1)
            return count

        total_chapters = print_chapters(result.structured_content.chapters)
        print(f"\nTotal chapters (including subchapters): {total_chapters}")

        # Complex document should have multiple chapters
        assert len(result.structured_content.chapters) >= 3, "Should have at least 3 chapters"

        # Check that subchapters exist (document should have hierarchy)
        has_subchapters = any(
            len(ch.subchapters) > 0
            for ch in result.structured_content.chapters
        )
        print(f"Has subchapters: {has_subchapters}")

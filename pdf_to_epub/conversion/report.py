"""Conversion report generator."""

import re
from pathlib import Path
from dataclasses import dataclass
from typing import List

from .models import ConversionResult
from core.pdf_extractor import PDFExtractor
from core.epub_extractor import EPUBExtractor
from validation.completeness_checker import CompletenessChecker


@dataclass
class ConversionStats:
    """Statistics about the conversion."""
    # Source (PDF)
    pdf_pages: int = 0
    pdf_text_blocks: int = 0
    pdf_words: int = 0
    pdf_chars: int = 0
    pdf_images: int = 0

    # Target (EPUB)
    epub_chapters: int = 0
    epub_words: int = 0
    epub_chars: int = 0
    epub_images: int = 0
    epub_endnotes: int = 0
    epub_endnote_links_total: int = 0
    epub_endnote_links_unique: int = 0
    epub_endnote_links_missing: int = 0
    epub_headings: int = 0
    epub_file_size: int = 0

    # Quality metrics
    completeness_score: float = 0.0
    order_score: float = 0.0
    reading_order_confidence: float = 0.0

    # Comparison
    words_preserved_pct: float = 0.0
    chars_preserved_pct: float = 0.0


class ConversionReporter:
    """
    Generates detailed conversion reports.

    Collects statistics from both source PDF and generated EPUB
    to provide a comprehensive comparison and quality assessment.
    """

    def generate_report(
        self,
        result: ConversionResult,
        pdf_path: Path,
        include_validation: bool = True
    ) -> ConversionStats:
        """
        Generate detailed statistics for a conversion.

        Args:
            result: ConversionResult from converter
            pdf_path: Path to original PDF
            include_validation: Whether to run completeness/order validation

        Returns:
            ConversionStats with detailed metrics
        """
        stats = ConversionStats()

        if result.status == "failed":
            return stats

        # Extract PDF statistics
        self._extract_pdf_stats(pdf_path, stats)

        # Extract EPUB statistics from result
        self._extract_epub_stats(result, stats)

        # Run validation if requested
        if include_validation and result.epub_path:
            self._run_validation(pdf_path, Path(result.epub_path), stats)

        # Calculate preservation percentages
        if stats.pdf_words > 0:
            stats.words_preserved_pct = (stats.epub_words / stats.pdf_words) * 100
        if stats.pdf_chars > 0:
            stats.chars_preserved_pct = (stats.epub_chars / stats.pdf_chars) * 100

        # Store reading order confidence
        stats.reading_order_confidence = result.reading_order_confidence

        return stats

    def _extract_pdf_stats(self, pdf_path: Path, stats: ConversionStats):
        """Extract statistics from source PDF."""
        import fitz

        doc = fitz.open(str(pdf_path))
        try:
            stats.pdf_pages = len(doc)

            # Count text blocks and words
            total_text = ""
            for page in doc:
                blocks = page.get_text("blocks")
                stats.pdf_text_blocks += len([b for b in blocks if b[6] == 0])  # Type 0 = text
                total_text += page.get_text()

                # Count images
                stats.pdf_images += len(page.get_images(full=True))

            stats.pdf_words = len(total_text.split())
            stats.pdf_chars = len(total_text)
        finally:
            doc.close()

    def _extract_epub_stats(self, result: ConversionResult, stats: ConversionStats):
        """Extract statistics from conversion result."""
        content = result.structured_content
        if not content:
            return

        stats.epub_chapters = len(content.chapters)
        stats.epub_images = len(content.images)

        # Count headings and text
        total_text = ""
        for chapter in content.chapters:
            # Count chapter as heading
            stats.epub_headings += 1

            # Get chapter text
            if hasattr(chapter, 'get_text'):
                chapter_text = chapter.get_text()
                total_text += chapter_text + " "

                # Count endnotes (look for endnote markers)
                if hasattr(chapter, 'is_endnotes') and chapter.is_endnotes:
                    # Prefer structural count (more reliable than regex on merged text).
                    if hasattr(chapter, "content_blocks"):
                        stats.epub_endnotes = len([
                            b for b in getattr(chapter, "content_blocks", [])
                            if getattr(b, "role", None) == "endnote"
                        ])
                    else:
                        endnote_pattern = re.compile(r'(?:^|\n)(\d{1,3})[.)]?\s+')
                        stats.epub_endnotes = len(endnote_pattern.findall(chapter_text))

            # Count subchapter headings
            if hasattr(chapter, 'subchapters'):
                stats.epub_headings += self._count_subchapter_headings(chapter.subchapters)

        stats.epub_words = len(total_text.split())
        stats.epub_chars = len(total_text)

        self._extract_endnote_link_stats(content, stats)

        # Get file size
        if result.epub_path:
            epub_path = Path(result.epub_path)
            if epub_path.exists():
                stats.epub_file_size = epub_path.stat().st_size

    def _count_subchapter_headings(self, subchapters: List) -> int:
        """Recursively count subchapter headings."""
        count = 0
        for sub in subchapters:
            count += 1
            if hasattr(sub, 'subchapters'):
                count += self._count_subchapter_headings(sub.subchapters)
        return count

    def _run_validation(self, pdf_path: Path, epub_path: Path, stats: ConversionStats):
        """Run validation and store scores."""
        try:
            with PDFExtractor(pdf_path) as pdf:
                source_text = pdf.get_full_text()

            with EPUBExtractor(epub_path) as epub:
                target_text = epub.get_full_text()

            checker = CompletenessChecker(source_text, target_text)
            result = checker.check()

            stats.completeness_score = result.completeness_score
            stats.order_score = result.order_score
        except Exception:
            # If validation fails, leave scores at 0
            pass

    def _extract_endnote_link_stats(self, content, stats: ConversionStats) -> None:
        """
        Extract endnote hyperlink statistics from rendered chapters (HTML).

        This is a best-effort heuristic:
        - Finds the rendered endnotes chapter by searching for id="note1" or class="endnote"
        - Extracts all note ids: noteN
        - Counts all href="...#noteN" references in non-endnotes chapters
        """
        rendered = getattr(content, "rendered_chapters", None)
        if not rendered:
            return

        endnotes_index = None
        endnotes_html = ""
        for idx, ch in enumerate(rendered):
            html = getattr(ch, "content", "") or ""
            if 'id="note1"' in html or 'class="endnote"' in html:
                endnotes_index = idx
                endnotes_html = html
                break

        if endnotes_index is None:
            return

        note_ids = {int(m.group(1)) for m in re.finditer(r'id="note(\d{1,3})"', endnotes_html)}
        if not note_ids:
            return

        # If endnotes weren't counted structurally, fall back to rendered ids.
        if stats.epub_endnotes == 0:
            stats.epub_endnotes = len(note_ids)

        href_re = re.compile(r'href="[^"]*#note(\d{1,3})"')
        total_links = 0
        unique_linked = set()
        for idx, ch in enumerate(rendered):
            if idx == endnotes_index:
                continue
            html = getattr(ch, "content", "") or ""
            for m in href_re.finditer(html):
                num = int(m.group(1))
                if num in note_ids:
                    total_links += 1
                    unique_linked.add(num)

        stats.epub_endnote_links_total = total_links
        stats.epub_endnote_links_unique = len(unique_linked)
        stats.epub_endnote_links_missing = len(note_ids - unique_linked)

    def format_report(self, stats: ConversionStats) -> str:
        """
        Format statistics as a readable report.

        Args:
            stats: ConversionStats to format

        Returns:
            Formatted string report
        """
        lines = [
            "=" * 60,
            "CONVERSION REPORT",
            "=" * 60,
            "",
            "SOURCE (PDF):",
            f"  Pages:        {stats.pdf_pages}",
            f"  Text blocks:  {stats.pdf_text_blocks}",
            f"  Words:        {stats.pdf_words:,}",
            f"  Characters:   {stats.pdf_chars:,}",
            f"  Images:       {stats.pdf_images}",
            "",
            "TARGET (EPUB):",
            f"  Chapters:     {stats.epub_chapters}",
            f"  Headings:     {stats.epub_headings}",
            f"  Words:        {stats.epub_words:,}",
            f"  Characters:   {stats.epub_chars:,}",
            f"  Images:       {stats.epub_images}",
            f"  Endnotes:     {stats.epub_endnotes}",
            f"  Endnote links: {stats.epub_endnote_links_total}",
            f"  Link coverage: {stats.epub_endnote_links_unique}/{stats.epub_endnotes}",
            f"  File size:    {stats.epub_file_size / 1024:.1f} KB",
            "",
            "PRESERVATION:",
            f"  Words:        {stats.words_preserved_pct:.1f}%",
            f"  Characters:   {stats.chars_preserved_pct:.1f}%",
            "",
            "QUALITY METRICS:",
            f"  Completeness:    {stats.completeness_score:.1f}%",
            f"  Order score:     {stats.order_score:.1f}%",
            f"  Reading conf.:   {stats.reading_order_confidence * 100:.1f}%",
            "",
            "=" * 60,
        ]

        if stats.epub_endnotes > 0 and stats.epub_endnote_links_unique < stats.epub_endnotes:
            lines.append(
                f"ALERT: Endnote links missing "
                f"({stats.epub_endnote_links_unique}/{stats.epub_endnotes} linked; "
                f"{stats.epub_endnote_links_missing} missing)."
            )

        # Add status summary
        passed = (
            stats.completeness_score >= 95.0 and
            stats.order_score >= 80.0 and
            stats.epub_images >= stats.pdf_images  # All images transferred
        )
        lines.append(f"STATUS: {'[PASS]' if passed else '[NEEDS REVIEW]'}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def format_summary(self, stats: ConversionStats) -> str:
        """
        Format a brief one-line summary.

        Args:
            stats: ConversionStats to format

        Returns:
            Short summary string
        """
        return (
            f"Converted: {stats.pdf_pages} pages, "
            f"{stats.epub_chapters} chapters, "
            f"{stats.epub_images} images, "
            f"{stats.epub_endnotes} endnotes | "
            f"Completeness: {stats.completeness_score:.1f}% | "
            f"Order: {stats.order_score:.1f}%"
        )

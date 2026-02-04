"""Tests for ConversionReporter endnote link metrics."""

from datetime import datetime
from pathlib import Path

from pdf_to_epub.conversion.report import ConversionReporter, ConversionStats
from pdf_to_epub.conversion.models import ConversionResult, ConversionLog
from pdf_to_epub.conversion.detectors.structure_builder import Chapter as StructureChapter
from pdf_to_epub.conversion.detectors.models import TextBlock, SemanticBlock
from pdf_to_epub.conversion.models import Chapter as RenderedChapter


def _sb(text: str, role: str, num: int | None = None) -> SemanticBlock:
    tb = TextBlock(
        text=text,
        page=1,
        x0=0,
        y0=0,
        x1=100,
        y1=20,
        font_name="Arial",
        font_size=10,
        flags=0,
    )
    return SemanticBlock(original_block=tb, role=role, endnote_num=num)


def test_report_alerts_when_links_missing(tmp_path: Path) -> None:
    # Structured chapters (used for endnote counting)
    main = StructureChapter(title="Intro", level=1, content_blocks=[_sb("Body text.", "body")])
    endnotes = StructureChapter(
        title="Endnotes",
        level=1,
        content_blocks=[
            _sb("1  First note.", "endnote", 1),
            _sb("2  Second note.", "endnote", 2),
            _sb("3  Third note.", "endnote", 3),
        ],
        is_endnotes=True,
    )

    # Rendered chapters (used for link statistics)
    rendered_main = RenderedChapter(
        title="Intro",
        level=1,
        content=(
            '<p>Some text <a href="chapter2.xhtml#note1" class="footnote-ref"><sup>1</sup></a> '
            'and <a href="chapter2.xhtml#note2" class="footnote-ref"><sup>2</sup></a>.</p>'
        ),
        footnotes=[],
    )
    rendered_endnotes = RenderedChapter(
        title="Endnotes",
        level=1,
        content=(
            '<p class="endnote" id="note1">...</p>'
            '<p class="endnote" id="note2">...</p>'
            '<p class="endnote" id="note3">...</p>'
        ),
        footnotes=[],
    )

    structured_content = type("SC", (), {})()
    structured_content.chapters = [main, endnotes]
    structured_content.images = []
    structured_content.rendered_chapters = [rendered_main, rendered_endnotes]

    result = ConversionResult(
        epub_path=None,
        status="success",
        reading_order_confidence=1.0,
        log=ConversionLog(timestamp=datetime(2026, 2, 3, 12, 0, 0), strategy_used="simple", config={}),
        structured_content=structured_content,
        metadata=None,
    )

    reporter = ConversionReporter()
    stats = ConversionStats()
    reporter._extract_epub_stats(result, stats)  # pylint: disable=protected-access

    assert stats.epub_endnotes == 3
    assert stats.epub_endnote_links_total == 2
    assert stats.epub_endnote_links_unique == 2
    assert stats.epub_endnote_links_missing == 1

    report_text = reporter.format_report(stats)
    assert "ALERT: Endnote links missing" in report_text

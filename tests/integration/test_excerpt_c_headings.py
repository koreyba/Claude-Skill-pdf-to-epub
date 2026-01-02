"""Integration tests for heading detection on Excerpt C (full conversion)."""

import re
from pathlib import Path

import pytest

from pdf_to_epub.conversion.converter import Converter


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def _iter_chapters(chapters):
    if hasattr(chapters, "title"):
        chapters = [chapters]
    for chapter in chapters:
        yield chapter
        for sub in getattr(chapter, "subchapters", []):
            yield from _iter_chapters(sub)


def _find_chapter(chapters, predicate):
    for chapter in _iter_chapters(chapters):
        if predicate(chapter):
            return chapter
    return None


def _find_direct_subchapter(chapter, predicate):
    for sub in getattr(chapter, "subchapters", []):
        if predicate(sub):
            return sub
    return None


class TestExcerptCHeadings:
    """Validate that specific lines are (not) detected as headings."""

    @pytest.fixture(scope="module")
    def conversion_result(self, tmp_path_factory):
        pdf_path = Path(__file__).parent.parent / "fixtures" / "Excerpt C The Ways We Are in This Together.pdf"
        if not pdf_path.exists():
            pytest.skip(f"PDF fixture not found: {pdf_path}")

        output_dir = tmp_path_factory.mktemp("excerpt_c_headings")
        output_path = output_dir / "excerpt_c.epub"

        converter = Converter(strategy="simple")
        result = converter.convert(str(pdf_path), str(output_path))

        assert result.status in ("success", "warning")
        assert result.structured_content is not None
        return result

    def test_specific_texts_are_not_headings(self, conversion_result):
        chapters = conversion_result.structured_content.chapters
        titles = [_normalize(ch.title) for ch in _iter_chapters(chapters)]

        assert not any(
            "we also saw that the collective or communal dimensions" in title
            for title in titles
        )
        assert not any(
            "the result, as you can see in figure" in title
            for title in titles
        )
        assert not any(
            "figure 2" in title and "native perspectives" in title
            for title in titles
        )

    def test_expected_heading_hierarchy(self, conversion_result):
        chapters = conversion_result.structured_content.chapters

        excerpt_prefix = (
            "excerpt c: the ways we are in this together: "
            "intersubjectivity and interobjectivity in the holonic kosmos"
        )
        excerpt_chapter = _find_chapter(
            chapters,
            lambda ch: _normalize(ch.title).startswith(excerpt_prefix),
        )
        assert excerpt_chapter is not None
        assert excerpt_chapter.level == 1

        part_chapter = _find_chapter(
            chapters,
            lambda ch: (
                "part i." in _normalize(ch.title)
                and "introduction" in _normalize(ch.title)
                and "systems theory versus hermeneutics" in _normalize(ch.title)
            ),
        )
        assert part_chapter is not None
        assert part_chapter.level == 1

        important_chapter = _find_direct_subchapter(
            part_chapter,
            lambda ch: _normalize(ch.title) == "important",
        )
        assert important_chapter is not None
        assert important_chapter.level == 2

        overview_chapter = _find_direct_subchapter(
            important_chapter,
            lambda ch: _normalize(ch.title) == "overview",
        )
        assert overview_chapter is not None
        assert overview_chapter.level == 3

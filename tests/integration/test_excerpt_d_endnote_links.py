"""Integration test: Excerpt D endnote references must be hyperlinked."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

import pytest

from pdf_to_epub.conversion.converter import Converter


@pytest.fixture(scope="module")
def excerpt_d_epub(tmp_path_factory) -> Path:
    """Convert Excerpt D once per module; return EPUB path."""
    pdf_path = Path(__file__).parent.parent / "fixtures" / "Excerpt D.pdf"
    if not pdf_path.exists():
        pytest.skip(f"PDF fixture not found: {pdf_path}")

    out_dir = tmp_path_factory.mktemp("excerpt_d_links")
    out_path = out_dir / "excerpt_d.epub"

    converter = Converter(strategy="simple")
    result = converter.convert(str(pdf_path), str(out_path))

    assert result.status in ("success", "warning"), f"Conversion failed: {result.log.errors}"
    assert out_path.exists(), "EPUB file not created"

    return out_path


def _find_endnotes_xhtml(epub: zipfile.ZipFile) -> str:
    """Return the path of the XHTML file that contains endnote targets."""
    for name in epub.namelist():
        if name.endswith(".xhtml") and name.startswith("OEBPS/"):
            data = epub.read(name).decode("utf-8", "replace")
            if 'id="note1"' in data:
                return name
    raise AssertionError("Could not find endnotes XHTML (missing id=\"note1\").")


def test_excerpt_d_all_endnotes_have_incoming_links(excerpt_d_epub: Path) -> None:
    """
    For Excerpt D, every endnote target noteN in the Endnotes chapter must be referenced
    by at least one hyperlink from the main text chapters.
    """
    assert zipfile.is_zipfile(excerpt_d_epub), "EPUB is not a valid ZIP"

    with zipfile.ZipFile(excerpt_d_epub, "r") as z:
        endnotes_path = _find_endnotes_xhtml(z)
        endnotes_basename = endnotes_path.split("/")[-1]

        endnotes_html = z.read(endnotes_path).decode("utf-8", "replace")
        note_ids = {int(m.group(1)) for m in re.finditer(r'id="note(\d{1,3})"', endnotes_html)}
        assert note_ids, "No note IDs found in endnotes chapter"

        href_re = re.compile(re.escape(endnotes_basename) + r"#note(\d{1,3})")
        incoming: dict[int, int] = {n: 0 for n in note_ids}
        unknown_targets: set[int] = set()

        footnote_ref_count = 0
        for name in z.namelist():
            if not (name.endswith(".xhtml") and name.startswith("OEBPS/")):
                continue
            if name == endnotes_path:
                continue

            html = z.read(name).decode("utf-8", "replace")
            footnote_ref_count += html.count('class="footnote-ref"')
            for m in href_re.finditer(html):
                target = int(m.group(1))
                if target in incoming:
                    incoming[target] += 1
                else:
                    unknown_targets.add(target)

        assert footnote_ref_count > 0, "No footnote-ref links found in main content"
        assert not unknown_targets, f"Found links to missing endnotes: {sorted(unknown_targets)}"

        missing = sorted([n for n, c in incoming.items() if c == 0])
        assert not missing, f"Missing incoming links for endnotes: {missing}"

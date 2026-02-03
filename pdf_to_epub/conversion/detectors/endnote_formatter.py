"""Formats endnote blocks as HTML with anchor IDs for hyperlinking."""

import re
from typing import List

from .models import SemanticBlock

# Pattern to extract endnote number and content.
# Be permissive: PDFs vary (e.g., "12  Text", "12. Text", "12) Text").
ENDNOTE_PATTERN = re.compile(r'^(\d{1,3})[.)]?\s+(.*)$', re.DOTALL)


class EndnoteFormatter:
    """
    Converts endnote blocks to HTML with proper anchor IDs.

    Each endnote gets:
    - An `id="noteN"` anchor for hyperlink targets
    - A styled number span
    - The endnote content
    """

    def format_endnotes(self, blocks: List[SemanticBlock]) -> str:
        """
        Convert endnote blocks to HTML with anchors.

        Args:
            blocks: List of SemanticBlocks with role='endnote'

        Returns:
            HTML string with anchored endnotes
        """
        html_parts = []

        for block in blocks:
            if block.role != "endnote":
                continue

            text = block.original_block.text.strip()
            num = block.endnote_num

            if num is None:
                # Fallback: try to extract from text
                match = ENDNOTE_PATTERN.match(text)
                if match:
                    num = int(match.group(1))
                    content = match.group(2).strip()
                else:
                    # Cannot determine number, render without anchor
                    html_parts.append(
                        f'    <p class="endnote">{self._escape_html(text)}</p>'
                    )
                    continue
            else:
                # Extract content after the number
                match = ENDNOTE_PATTERN.match(text)
                content = match.group(2).strip() if match else text

            # Generate anchored paragraph
            html_parts.append(
                f'    <p class="endnote" id="note{num}">'
                f'<span class="endnote-num">{num}.</span> '
                f'{self._escape_html(content)}'
                f'</p>'
            )

        return '\n'.join(html_parts)

    def format_endnotes_with_backlinks(
        self,
        blocks: List[SemanticBlock],
        main_chapter_file: str = "chapter1.xhtml"
    ) -> str:
        """
        Convert endnote blocks to HTML with anchors and back-links.

        Args:
            blocks: List of SemanticBlocks with role='endnote'
            main_chapter_file: Filename of main chapter for back-links

        Returns:
            HTML string with anchored endnotes and back-links
        """
        html_parts = []

        for block in blocks:
            if block.role != "endnote":
                continue

            text = block.original_block.text.strip()
            num = block.endnote_num

            if num is None:
                match = ENDNOTE_PATTERN.match(text)
                if match:
                    num = int(match.group(1))
                    content = match.group(2).strip()
                else:
                    html_parts.append(
                        f'    <p class="endnote">{self._escape_html(text)}</p>'
                    )
                    continue
            else:
                match = ENDNOTE_PATTERN.match(text)
                content = match.group(2).strip() if match else text

            # Generate anchored paragraph with back-link
            backlink = (
                f'<a href="{main_chapter_file}#ref{num}" '
                f'class="endnote-backlink" title="Go back"> [^]</a>'
            )

            html_parts.append(
                f'    <p class="endnote" id="note{num}">'
                f'<span class="endnote-num">{num}.</span> '
                f'{self._escape_html(content)}'
                f'{backlink}'
                f'</p>'
            )

        return '\n'.join(html_parts)

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

    def get_endnote_numbers(self, blocks: List[SemanticBlock]) -> List[int]:
        """
        Get list of endnote numbers from blocks.

        Useful for verification.

        Args:
            blocks: List of SemanticBlocks

        Returns:
            List of endnote numbers
        """
        numbers = []
        for block in blocks:
            if block.role == "endnote" and block.endnote_num is not None:
                numbers.append(block.endnote_num)
        return sorted(numbers)

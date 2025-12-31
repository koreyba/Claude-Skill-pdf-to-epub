# ADAPTABLE: New footnote patterns can be added to PATTERNS dict
# See ~/.claude/skills/pdf-to-epub/reference/code-adaptation.md
"""Detects footnote references in text blocks and converts them to hyperlinks."""

from typing import List, Optional
from dataclasses import dataclass
import re

from claude_skill.conversion.detectors.models import SemanticBlock


@dataclass
class FootnoteRef:
    """Represents a footnote reference in text."""
    number: int
    original_text: str  # e.g., ".1", "[1]", "(1)"
    start_pos: int
    end_pos: int


class FootnoteDetector:
    """
    Detects footnote references in text blocks and converts them to hyperlinks.

    Supports multiple reference styles:
    - bracket: [1], [12]
    - paren: (1), (12)
    - period: .1, .12 (after words)
    - superscript: word1, word12 (number immediately after letters)
    """

    # Patterns for different footnote styles
    PATTERNS = {
        # [1], [12] - bracket style
        'bracket': re.compile(r'\[(\d{1,2})\]'),
        # (1), (12) - parenthesis style
        'paren': re.compile(r'\((\d{1,2})\)'),
        # word.1, sentence.1 - period style (common in some books)
        'period': re.compile(r'(?<=\w)\.(\d{1,2})(?=\s|$|[,;:!?])'),
        # Superscript-like patterns (number at end of word without space)
        'superscript': re.compile(r'(?<=[a-zA-Z])(\d{1,2})(?=\s|$|[.,;:!?])'),
    }

    def __init__(self, patterns: Optional[List[str]] = None):
        """
        Initialize detector with pattern selection.

        Args:
            patterns: List of pattern types to use ('bracket', 'paren', 'period', 'superscript')
                     If None, uses ['bracket', 'paren'] for backward compatibility.
        """
        self.active_patterns = patterns or ['bracket', 'paren']

    def process(self, blocks: List[SemanticBlock]) -> List[SemanticBlock]:
        """
        Scan blocks for footnote references and tag them in metadata.

        Args:
            blocks: List of SemanticBlock objects

        Returns:
            Same blocks with footnote_refs added to metadata
        """
        for sb in blocks:
            if sb.role not in ["body", "list-item"]:
                continue

            refs = self.find_references(sb.original_block.text)
            if refs:
                sb.metadata["footnote_refs"] = [
                    {"num": r.number, "text": r.original_text,
                     "start": r.start_pos, "end": r.end_pos}
                    for r in refs
                ]

        return blocks

    def find_references(self, text: str) -> List[FootnoteRef]:
        """
        Find all footnote references in text.

        Args:
            text: Text to search for footnote references

        Returns:
            List of FootnoteRef objects sorted by position
        """
        refs = []

        for pattern_type in self.active_patterns:
            pattern = self.PATTERNS.get(pattern_type)
            if not pattern:
                continue

            for match in pattern.finditer(text):
                num = int(match.group(1))
                if 1 <= num <= 99:  # Reasonable range
                    refs.append(FootnoteRef(
                        number=num,
                        original_text=match.group(0),
                        start_pos=match.start(),
                        end_pos=match.end()
                    ))

        # Sort by position and remove duplicates (same position)
        refs.sort(key=lambda r: r.start_pos)

        # Remove duplicates at same position
        seen_positions = set()
        unique_refs = []
        for ref in refs:
            if ref.start_pos not in seen_positions:
                seen_positions.add(ref.start_pos)
                unique_refs.append(ref)

        return unique_refs

    def convert_to_hyperlinks(self, text: str, endnotes_file: str = "endnotes.xhtml") -> str:
        """
        Convert footnote references in text to hyperlinks.

        Args:
            text: Source text with footnote references
            endnotes_file: Filename of endnotes chapter for href

        Returns:
            Text with references converted to hyperlinks
        """
        refs = self.find_references(text)
        if not refs:
            return text

        # Process in reverse order to preserve positions
        result = text
        for ref in reversed(refs):
            link = (
                f'<a href="{endnotes_file}#note{ref.number}" '
                f'class="footnote-ref"><sup>{ref.number}</sup></a>'
            )
            result = result[:ref.start_pos] + link + result[ref.end_pos:]

        return result

    def detect_reference_style(self, text: str) -> Optional[str]:
        """
        Detect which reference style is used in the text.

        Useful for auto-detecting which patterns to use.

        Args:
            text: Text to analyze

        Returns:
            Pattern type ('bracket', 'paren', 'period', 'superscript') or None
        """
        for pattern_type, pattern in self.PATTERNS.items():
            if pattern.search(text):
                return pattern_type
        return None

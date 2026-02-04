from dataclasses import dataclass, field
import re
from collections import Counter
from typing import List
from .models import SemanticBlock
from core.utils import get_logger

logger = get_logger(__name__)

_ENDNOTE_START_RE = re.compile(r"^\s*(\d{1,3})\s{2,}(.*)$", re.DOTALL)
_ENDNOTE_START_FALLBACK_RE = re.compile(r"^\s*(\d{1,3})[.)]?\s+(.*)$", re.DOTALL)

@dataclass
class Chapter:
    title: str
    level: int  # 1 for H1, 2 for H2...
    content_blocks: List[SemanticBlock] = field(default_factory=list)
    subchapters: List['Chapter'] = field(default_factory=list)
    is_endnotes: bool = False  # True if this is the endnotes chapter
    
    def get_text(self) -> str:
        """Get all text from this chapter including subchapters."""
        # Merge blocks intelligently - join continuation blocks with space
        merged_parts = []
        current_paragraph = ""
        prev_block = None

        for block in self.content_blocks:
            text = block.original_block.text.strip()
            if not text:
                continue

            if not current_paragraph:
                # Start new paragraph
                current_paragraph = text
            elif self._is_continuation(prev_block, block.original_block, current_paragraph, text):
                # Continue current paragraph (join with space)
                current_paragraph += " " + text
            else:
                # Start new paragraph
                merged_parts.append(current_paragraph)
                current_paragraph = text
            prev_block = block.original_block

        # Don't forget the last paragraph
        if current_paragraph:
            merged_parts.append(current_paragraph)

        # Include text from subchapters recursively
        for sub in self.subchapters:
            sub_text = sub.get_text()
            if sub_text:
                merged_parts.append(sub_text)

        return "\n\n".join(merged_parts)

    def _is_continuation(self, prev_block, curr_block, prev_text: str, curr_text: str) -> bool:
        """Check if curr_text is a continuation of prev_text (same paragraph)."""
        if not prev_text or not curr_text:
            return False

        prev_ends_sentence = prev_text.rstrip()[-1] in '.!?:;'
        curr_starts_lower = curr_text[0].islower()
        prev_ends_hyphen = prev_text.rstrip().endswith('-')

        if prev_ends_hyphen:
            return True

        if not prev_ends_sentence and curr_starts_lower:
            return True

        if not prev_block or not curr_block:
            return False

        gap = max(0.0, curr_block.y0 - prev_block.y1)
        font_size = max(prev_block.font_size, curr_block.font_size, 1.0)
        line_height = font_size * 1.25
        indent_delta = curr_block.x0 - prev_block.x0
        indent_threshold = font_size * 1.2

        if gap > line_height * 1.5:
            return False
        if indent_delta > indent_threshold * 1.5 and gap >= line_height * 0.6:
            return False

        return gap <= line_height * 0.75 and abs(indent_delta) <= indent_threshold

class StructureBuilder:
    """
    Converts a flat list of SemanticBlocks into a hierarchical Chapter tree.
    """

    def build_chapters(self, blocks: List[SemanticBlock]) -> List[Chapter]:
        # 0. Separate endnotes from main content (and merge multi-block notes).
        main_blocks: List[SemanticBlock] = []
        endnote_blocks: List[SemanticBlock] = []
        endnotes_heading = None

        endnotes_heading_index = self._find_endnotes_heading_index(blocks)
        if endnotes_heading_index is not None:
            endnotes_heading = blocks[endnotes_heading_index].original_block.text.strip()
            main_blocks = list(blocks[:endnotes_heading_index])
            endnotes_section = list(blocks[endnotes_heading_index + 1:])
            endnote_blocks = self._merge_endnotes(endnotes_section)
        else:
            endnotes_pages = self._infer_endnotes_pages(blocks)
            if endnotes_pages:
                endnotes_section = [b for b in blocks if b.original_block.page in endnotes_pages]
                main_blocks = [b for b in blocks if b.original_block.page not in endnotes_pages]
                endnote_blocks = self._merge_endnotes(endnotes_section)
            else:
                # Fallback to legacy behavior (only explicitly-classified endnote blocks).
                for block in blocks:
                    if block.role == "endnote":
                        endnote_blocks.append(block)
                    else:
                        main_blocks.append(block)

        if endnote_blocks:
            logger.info(f"Prepared {len(endnote_blocks)} endnotes for Endnotes chapter")

        # 1. Preprocessing: Merge consecutive headers of same level
        merged_blocks = self._merge_headers(main_blocks)

        root_chapters = []
        current_stack = []  # Stack of active chapters [H1, H2, ...]

        # Create a default introductory chapter for content before the first H1
        preamble = Chapter(title="Intro", level=0)
        current_stack.append(preamble)
        root_chapters.append(preamble)

        for block in merged_blocks:
            role = block.role

            if role.startswith("h") and role[1:].isdigit():
                level = int(role[1:])
                # Found a header! Start a new chapter.
                title = block.original_block.text.strip()
                new_chapter = Chapter(title=title, level=level, content_blocks=[block])

                # Logic to place this chapter in the tree
                # Pop stack until we find a parent with level < current level
                # Special case: H1 always goes to root (never nested under Intro)
                if level == 1:
                    # Clear stack for H1, it's always a root chapter
                    current_stack.clear()
                else:
                    # Pop stack until we find a parent with level < current level
                    while current_stack and current_stack[-1].level >= level:
                        current_stack.pop()

                if not current_stack:
                    # Top level chapter (or strictly > previous top)
                    root_chapters.append(new_chapter)
                else:
                    # Add as subchapter to current parent
                    parent = current_stack[-1]
                    parent.subchapters.append(new_chapter)

                # Make this the active chapter
                current_stack.append(new_chapter)

            else:
                # Regular content (body, list, etc.)
                # Add to the currently active chapter (tip of stack)
                if current_stack:
                    current_stack[-1].content_blocks.append(block)
                else:
                    # Should not happen due to preamble, but safety check
                    pass

        # Cleanup: Remove preamble if empty and there are other chapters, or if it's the only one and empty
        if root_chapters and root_chapters[0].title == "Intro" and not root_chapters[0].content_blocks and not root_chapters[0].subchapters:
            root_chapters.pop(0)

        # 2. Add endnotes chapter if we have endnotes
        if endnote_blocks:
            endnotes_chapter = Chapter(
                title=endnotes_heading or "Endnotes",
                level=1,
                content_blocks=endnote_blocks,
                is_endnotes=True  # Mark as endnotes chapter for special rendering
            )
            root_chapters.append(endnotes_chapter)
            logger.info(f"Created Endnotes chapter with {len(endnote_blocks)} notes")

        return root_chapters

    def _is_endnotes_heading(self, text: str) -> bool:
        stripped = text.strip()
        if not stripped:
            return False
        if not stripped.upper().startswith("ENDNOTES"):
            return False
        return len(stripped) <= 80

    def _find_endnotes_heading_index(self, blocks: List[SemanticBlock]) -> int | None:
        for idx, block in enumerate(blocks):
            if self._is_endnotes_heading(block.original_block.text):
                return idx
        return None

    def _infer_endnotes_pages(self, blocks: List[SemanticBlock]) -> set[int]:
        """
        Heuristic: infer a dedicated endnotes section at the end of the PDF.

        We look for a tail run of pages containing many endnote starts, allowing
        gaps (pages with only continuation text, i.e. no new note number).
        """
        if not blocks:
            return set()

        max_page = max(b.original_block.page for b in blocks)
        starts_by_page: Counter[int] = Counter()
        for b in blocks:
            if b.role == "endnote" or b.endnote_num is not None:
                starts_by_page[b.original_block.page] += 1

        if not starts_by_page:
            return set()

        last_start_page = max(starts_by_page)
        trailing_tolerance = 3
        pages: set[int] = set()

        # Include a small tail after the last detected start (continuation-only pages).
        if 0 <= (max_page - last_start_page) <= trailing_tolerance:
            pages.update(range(last_start_page, max_page + 1))
        else:
            pages.add(last_start_page)

        # Walk backwards, including gaps only if they are "closed" by another start.
        allowed_gap_pages = 6
        pending_gaps: List[int] = []
        page = last_start_page
        while page >= 1:
            if page in starts_by_page:
                pages.add(page)
                if pending_gaps:
                    pages.update(pending_gaps)
                    pending_gaps = []
            else:
                pending_gaps.append(page)
                if len(pending_gaps) > allowed_gap_pages:
                    break
            page -= 1

        # Confidence check: don't reclassify pages as endnotes unless it looks like a real section.
        total_starts = sum(starts_by_page.get(p, 0) for p in pages)
        pages_with_starts = {p for p in pages if starts_by_page.get(p, 0) > 0}
        if total_starts < 5 or len(pages_with_starts) < 2:
            return set()

        logger.info(
            f"Inferred endnotes section on pages {min(pages)}-{max(pages)} "
            f"({total_starts} note starts across {len(pages_with_starts)} pages)"
        )
        return pages

    def _merge_endnotes(self, blocks: List[SemanticBlock]) -> List[SemanticBlock]:
        """
        Merge multi-block endnotes into single SemanticBlocks.

        In many PDFs, only the first line of a note starts with the note number;
        wrapped lines are separate blocks without the marker. If we only keep
        role=='endnote', notes get truncated. This merges following blocks into
        the current note until the next note starts.
        """
        if not blocks:
            return []

        min_x0 = min((b.original_block.x0 for b in blocks if b.original_block.text.strip()), default=0.0)

        merged: List[SemanticBlock] = []
        current: SemanticBlock | None = None
        current_num: int | None = None
        current_parts: List[str] = []

        def flush():
            nonlocal current, current_num, current_parts
            if current is None or current_num is None:
                current = None
                current_num = None
                current_parts = []
                return

            content = " ".join(p for p in current_parts if p).strip()
            current.original_block.text = f"{current_num}  {content}".strip() if content else str(current_num)
            current.role = "endnote"
            current.endnote_num = current_num
            merged.append(current)

            current = None
            current_num = None
            current_parts = []

        for block in blocks:
            text = block.original_block.text.strip()
            if not text:
                continue

            if self._is_endnotes_heading(text):
                continue

            parsed = self._parse_endnote_start(text)
            explicit_start = block.role == "endnote" or block.endnote_num is not None
            parsed_start = parsed is not None and self._is_probable_endnote_start(block, min_x0)

            if explicit_start or parsed_start:
                flush()
                current = block
                current_num = block.endnote_num if block.endnote_num is not None else (parsed[0] if parsed else None)
                first = parsed[1] if (parsed and current_num == parsed[0]) else self._strip_endnote_marker(text, current_num)
                if first:
                    current_parts.append(first)
                continue

            if current is None:
                continue
            if block.role.startswith("h") and block.role[1:].isdigit():
                continue

            current_parts.append(text)

        flush()
        return merged

    def _parse_endnote_start(self, text: str) -> tuple[int, str] | None:
        stripped = text.strip()
        if not stripped:
            return None
        match = _ENDNOTE_START_RE.match(stripped) or _ENDNOTE_START_FALLBACK_RE.match(stripped)
        if not match:
            return None
        num = int(match.group(1))
        if not 1 <= num <= 300:
            return None
        content = match.group(2).strip()
        return (num, content)

    def _strip_endnote_marker(self, text: str, num: int | None) -> str:
        if num is None:
            return text.strip()
        pattern = re.compile(rf"^\s*{re.escape(str(num))}(?:[.)])?\s+")
        return pattern.sub("", text.strip(), count=1).strip()

    def _is_probable_endnote_start(self, block: SemanticBlock, min_x0: float) -> bool:
        # Endnote numbers are usually aligned to the left margin; continuation lines are indented.
        font_size = max(getattr(block.original_block, "font_size", 0.0) or 0.0, 1.0)
        tolerance = max(24.0, font_size * 4.0)
        return (block.original_block.x0 - min_x0) <= tolerance

    def _merge_headers(self, blocks: List[SemanticBlock]) -> List[SemanticBlock]:
        if not blocks:
            return []
            
        merged = []
        current_header = None
        
        for block in blocks:
            is_header = block.role.startswith("h") and block.role[1:].isdigit()
            
            if is_header:
                if current_header and current_header.role == block.role:
                    # Merge logic: Append text to previous header block
                    # We modify the original_block text for simplicity, or create a new wrapper
                    # Here we destructively update the current_header's text representation
                    current_header.original_block.text += " " + block.original_block.text
                    # We skip appending this block to 'merged' list efficiently
                    continue
                else:
                    # New header (or different level)
                    current_header = block
                    merged.append(block)
            else:
                # Not a header (body, etc) -> interrupts merging sequence
                current_header = None
                merged.append(block)
                
        return merged

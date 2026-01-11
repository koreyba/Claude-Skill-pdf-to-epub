from dataclasses import dataclass, field
from typing import List
from .models import SemanticBlock
from core.utils import get_logger

logger = get_logger(__name__)

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
        # 0. Separate endnotes from main content
        main_blocks = []
        endnote_blocks = []
        endnotes_heading = None

        for block in blocks:
            if self._is_endnotes_heading(block.original_block.text):
                endnotes_heading = block.original_block.text.strip()
                continue
            if block.role == "endnote":
                endnote_blocks.append(block)
            else:
                main_blocks.append(block)

        if endnote_blocks:
            logger.info(f"Found {len(endnote_blocks)} endnote blocks")

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
        if not stripped.startswith("ENDNOTES"):
            return False
        return len(stripped) <= 80

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

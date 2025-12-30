from dataclasses import dataclass, field
from typing import List, Optional
from claude_skill.conversion.detectors.models import SemanticBlock
from claude_skill.core.utils import get_logger

logger = get_logger(__name__)

@dataclass
class Chapter:
    title: str
    level: int # 1 for H1, 2 for H2...
    content_blocks: List[SemanticBlock] = field(default_factory=list)
    subchapters: List['Chapter'] = field(default_factory=list)
    
    def get_text(self) -> str:
        return "\n\n".join(b.original_block.text for b in self.content_blocks)

class StructureBuilder:
    """
    Converts a flat list of SemanticBlocks into a hierarchical Chapter tree.
    """

    def build_chapters(self, blocks: List[SemanticBlock]) -> List[Chapter]:
        # 0. Separate endnotes from main content
        main_blocks = []
        endnote_blocks = []

        for block in blocks:
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
                title="Endnotes",
                level=1,
                content_blocks=endnote_blocks
            )
            root_chapters.append(endnotes_chapter)
            logger.info(f"Created Endnotes chapter with {len(endnote_blocks)} notes")

        return root_chapters

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

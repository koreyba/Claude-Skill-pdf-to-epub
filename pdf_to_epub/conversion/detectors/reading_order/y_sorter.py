# ADAPTABLE: Custom sorting logic can be added
# See ~/.claude/skills/pdf-to-epub/reference/code-adaptation.md
from typing import List
from conversion.detectors.models import TextBlock
from .base import BlockSorter

class YSorter(BlockSorter):
    """
    Simple sorter that orders blocks Top-Down, Left-Right.
    Suitable for single-column layouts.
    """
    
    def sort_blocks(self, blocks: List[TextBlock]) -> List[TextBlock]:
        # Assume Y grows DOWNWARD (standard PDF coordinate system usually used by wrappers)
        # But we must be careful: fitz returns (x0, y0, x1, y1).
        # We sort primarily by Page, then by vertical position (y0), then horizontal (x0).
        
        # To handle slight misalignment, we could round y0, but for blocks (paragraphs)
        # strict sorting is usually safer than for words.
        
        return sorted(blocks, key=lambda b: (b.page, b.y0, b.x0))

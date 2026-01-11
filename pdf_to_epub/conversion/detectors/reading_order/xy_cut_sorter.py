# ADAPTABLE: Column detection thresholds can be tuned
# See ~/.claude/skills/pdf-to-epub/reference/code-adaptation.md
from typing import List, Tuple
from conversion.detectors.models import TextBlock
from .base import BlockSorter

class XYCutSorter(BlockSorter):
    """
    Advanced sorter using Recursive X-Y Cut algorithm.
    Suitable for multi-column layouts.
    """
    
    def sort_blocks(self, blocks: List[TextBlock]) -> List[TextBlock]:
        # Process page by page
        pages = sorted(list(set(b.page for b in blocks)))
        sorted_result = []
        
        for p in pages:
            page_blocks = [b for b in blocks if b.page == p]
            if not page_blocks:
                continue
            
            # Determine page bounds
            min_x = min(b.x0 for b in page_blocks)
            max_x = max(b.x1 for b in page_blocks)
            min_y = min(b.y0 for b in page_blocks)
            max_y = max(b.y1 for b in page_blocks)
            
            sorted_page = self._xy_cut(page_blocks, (min_x, min_y, max_x, max_y))
            sorted_result.extend(sorted_page)
            
        return sorted_result
        
    def _xy_cut(self, blocks: List[TextBlock], bounds: Tuple[float, float, float, float]) -> List[TextBlock]:
        """
        Recursive function to sort blocks within bounds (x0, y0, x1, y1).
        """
        if not blocks:
            return []
        if len(blocks) == 1:
            return blocks

        # 1. Try to cut Horizontally (Projection on Y axis)
        # Find gaps where no block exists in Y range
        y_gap = self._find_gap_y(blocks)
        if y_gap:
            # Split into Top and Bottom
            split_y = y_gap
            top_blocks = [b for b in blocks if b.y1 <= split_y] # Blocks completely above gap
            bottom_blocks = [b for b in blocks if b.y0 >= split_y] # Blocks completely below
            
            # Recursively sort
            # Note: Overlapping blocks (straddling the gap) shouldn't theoretically exist if gap is valid, 
            # or they are handled by loose comparisons.
            # Simplified: assuming clean gap.
            return self._xy_cut(top_blocks, bounds) + self._xy_cut(bottom_blocks, bounds)
            
        # 2. Try to cut Vertically (Projection on X axis)
        x_gap = self._find_gap_x(blocks)
        if x_gap:
            # Split into Left and Right (Columns!)
            split_x = x_gap
            left_blocks = [b for b in blocks if b.x1 <= split_x]
            right_blocks = [b for b in blocks if b.x0 >= split_x]
            
            return self._xy_cut(left_blocks, bounds) + self._xy_cut(right_blocks, bounds)
            
        # 3. No cuts possible? Sort by Y (Reading order atomic group)
        return sorted(blocks, key=lambda b: (b.y0, b.x0))

    def _find_gap_y(self, blocks: List[TextBlock]) -> float:
        """Finds the largest Y-gap to split blocks into Top/Bottom. Returns split coordinate or None."""
        # Project all blocks onto Y axis
        # Sort by y0
        y_sorted = sorted(blocks, key=lambda b: b.y0)
        
        # We need to find a horizontal line that does not intersect ANY block.
        # This is equivalent to finding a gap in the union of intervals [y0, y1].
        
        max_y_so_far = y_sorted[0].y1
        best_gap_size = 0
        best_split = None
        
        for b in y_sorted[1:]:
            if b.y0 > max_y_so_far:
                # Gap found!
                gap_size = b.y0 - max_y_so_far
                if gap_size > best_gap_size:
                    best_gap_size = gap_size
                    # Split in the middle of the gap
                    best_split = max_y_so_far + gap_size / 2
            
            max_y_so_far = max(max_y_so_far, b.y1)
            
        return best_split if best_split is not None else 0.0

    def _find_gap_x(self, blocks: List[TextBlock]) -> float:
        """Finds the largest X-gap (columns)."""
        x_sorted = sorted(blocks, key=lambda b: b.x0)
        
        max_x_so_far = x_sorted[0].x1
        best_gap_size = 0
        best_split = None
        
        for b in x_sorted[1:]:
            if b.x0 > max_x_so_far:
                gap_size = b.x0 - max_x_so_far
                if gap_size > best_gap_size:
                    best_gap_size = gap_size
                    best_split = max_x_so_far + gap_size / 2
            
            max_x_so_far = max(max_x_so_far, b.x1)
            
        return best_split if best_split is not None else 0.0

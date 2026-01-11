# FROZEN: Do not modify - metrics must be reproducible
# See ~/.claude/skills/pdf-to-epub/reference/architecture.md
from typing import List
from core.utils import get_logger
from .models import FoundChunk
from .lis import calculate_lis_length

logger = get_logger(__name__)

class OrderChecker:
    """
    Validates that the reading order of text chunks in the target document
    matches the source order.
    
    Uses Longest Increasing Subsequence (LIS) on the positions of found chunks.
    """
    
    def __init__(self, found_chunks: List[FoundChunk]):
        """
        Args:
            found_chunks: List of FoundChunk objects, sorted by their APPEARANCE in the SOURCE (PDF).
                          (This is guaranteed if CompletenessChecker processes chunks in order)
        """
        self.found_chunks = found_chunks
        
    def check(self) -> float:
        """
        Calculates the order score.
        
        Returns:
            float: Score between 0.0 and 100.0
                   100.0 means perfect monotonic order.
                   0.0 means completely reversed or scrambled order (theoretically).
        """
        if not self.found_chunks:
            # If no chunks were found, order is technically "undefined" or 100% of 0 items.
            # But let's return 100.0 to avoid dragging down the score of an empty book.
            # Completeness checker handles the "empty" error case.
            return 100.0
            
        # Extract the sequence of observed positions in the target (EPUB)
        # We expect these indices to be strictly increasing.
        observed_positions = [fc.start_pos for fc in self.found_chunks]
        
        # Calculate LIS length
        lis_len = calculate_lis_length(observed_positions)
        total_found = len(self.found_chunks)
        
        if total_found == 0:
            return 100.0
            
        score = (lis_len / total_found) * 100.0
        
        return score

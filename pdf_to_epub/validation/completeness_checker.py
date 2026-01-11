# FROZEN: Do not modify - metrics must be reproducible
# See ~/.claude/skills/pdf-to-epub/reference/architecture.md
"""
Completeness checker for verifying that all text from source (PDF)
is present in the target (EPUB).
"""

import re
from typing import List
from core.text_segmenter import segment_text, normalize_whitespace
from core.utils import get_logger, DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP
from .models import ValidationFailure, ValidationResult, FoundChunk
from .order_checker import OrderChecker

logger = get_logger(__name__)

class CompletenessChecker:
    """
    Verifies if every part of the source text exists in the target text.
    Uses sliding window segmentation and optimized substring searching.
    """

    def __init__(self, source_text: str, target_text: str, min_significant_len: int = 20):
        self.source_text = source_text
        # Normalize target text whitespace to match the source segmentation format
        self.target_text = normalize_whitespace(target_text)
        self.min_significant_len = min_significant_len

    def check(
        self, 
        chunk_size: int = DEFAULT_CHUNK_SIZE, 
        overlap: int = DEFAULT_OVERLAP
    ) -> ValidationResult:
        """
        Executes the completeness check.
        
        Returns:
            ValidationResult containing score and list of missing segments.
        """
        if not self.source_text:
            return ValidationResult(is_valid=True, completeness_score=100.0, missing_chunks=[], total_chunks=0)

        # 1. Segment the source text
        chunks = segment_text(self.source_text, chunk_size=chunk_size, overlap=overlap)
        total_chunks = len(chunks)
        
        if total_chunks == 0:
            return ValidationResult(is_valid=True, completeness_score=100.0, missing_chunks=[], total_chunks=0)

        missing_failures: List = []
        found_chunks_list = []
        found_count = 0
        
        # 2. Optimized search loop
        # We start searching from the beginning of the target text
        current_pos = 0

        for chunk in chunks:
            # We try to find the chunk starting from current_pos (optimized window)
            # If not found from current_pos, we fallback to full-text search 
            # (in case the chunk moved back or order is slightly different)
            idx = self.target_text.find(chunk.text, current_pos)
            
            if idx == -1:
                # Fallback to full search
                idx = self.target_text.find(chunk.text)

            if idx != -1:
                # Exact match found! Update cursor
                found_count += 1
                current_pos = idx + len(chunk.text)
                found_chunks_list.append(FoundChunk(chunk, idx, "exact"))
            else:
                # Try fuzzy matching (token-based)
                fuzzy_idx = self._fuzzy_check(chunk.text, current_pos)
                if fuzzy_idx != -1:
                    found_count += 1
                    # Note: We do NOT update current_pos here. Fuzzy match positions are unstable.
                    # Jumping ahead based on a fuzzy guess can cause us to skip valid Exact Matches later.
                    # We accept the found chunk but keep searching from the same reliable anchor.
                    found_chunks_list.append(FoundChunk(chunk, fuzzy_idx, "fuzzy"))
                elif len(chunk.text.strip()) >= self.min_significant_len:
                    missing_failures.append(ValidationFailure(
                        chunk=chunk,
                        reason=f"Significant text segment missing (len={len(chunk.text)})"
                    ))
                else:
                    # Treat as noise (likely page number or header)
                    logger.debug(f"Ignoring missing noise chunk: '{chunk.text[:20]}...'")
                    # We still count it as 'not found' for the score, 
                    # but it won't be in the fatal failure list.
                    pass

        # 3. Calculate score
        # Note: completeness score is based on ALL chunks (including noise).
        # But is_valid depends on missing_failures (significant content).
        score = (found_count / total_chunks) * 100.0
        
        # 4. Check Order
        order_checker = OrderChecker(found_chunks_list)
        order_score = order_checker.check()
        
        # Validity primarily depends on content completeness.
        # Order issues are warnings/quality metrics but don't strictly invalidate the content existence.
        is_valid = len(missing_failures) == 0
        
        if order_score < 98.0:
             logger.warning(f"Order check quality low! Score: {order_score:.2f}% (Threshold: 98%)")

        logger.info(f"Validation finished. Completeness: {score:.2f}%. Order: {order_score:.2f}%. Failures: {len(missing_failures)}")
        
        return ValidationResult(
            is_valid=is_valid,
            completeness_score=score,
            missing_chunks=missing_failures,
            total_chunks=total_chunks,
            found_chunks=found_chunks_list,
            order_score=order_score
        )

    def _fuzzy_check(self, text: str, start_pos: int, threshold: float = 0.85) -> int:
        """
        Performs a token-based check. Returns estimated start position if found, else -1.
        """
        # Extract words (tokens) of significant length
        tokens = re.findall(r'\w{4,}', text)
        if not tokens:
            # If no tokens to check, treat as not found
            return -1
            
        found_tokens = 0
        search_start = start_pos
        window_size = 10000
        
        if start_pos + len(text) > len(self.target_text) or len(self.target_text[search_start : search_start + window_size]) < len(text):
             # Fallback to full text if window is too small or at end
             search_window = self.target_text
             search_start = 0
        else:
             search_window = self.target_text[search_start : search_start + window_size]
        
        # Very simple heuristic: just check presence. 
        # For meaningful position, we need to find WHERE the first few tokens are.
        # But for strictly Completeness, simple presence was enough.
        # For Order, we need an anchor. Let's try to find the index of the first matched token.
        
        first_token_idx = -1
        
        for token in tokens:
            local_idx = search_window.find(token)
            if local_idx != -1:
                found_tokens += 1
                if first_token_idx == -1:
                    first_token_idx = search_start + local_idx
        
        match_rate = found_tokens / len(tokens)
        
        if match_rate >= threshold:
            return first_token_idx if first_token_idx != -1 else start_pos
        return -1

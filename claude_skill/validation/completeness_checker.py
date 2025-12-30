"""
Completeness checker for verifying that all text from source (PDF) 
is present in the target (EPUB).
"""

import re
from typing import List, Optional
from claude_skill.core.text_segmenter import segment_text, normalize_whitespace
from claude_skill.core.utils import get_logger, DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP
from claude_skill.validation.models import ValidationFailure, ValidationResult

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

        missing_failures = []
        found_count = 0
        
        # 2. Optimized search loop
        # We start searching from the beginning of the target text
        current_pos = 0
        target_len = len(self.target_text)

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
            else:
                # Try fuzzy matching (token-based)
                if self._fuzzy_check(chunk.text, current_pos):
                    found_count += 1
                    # Note: we don't update current_pos here to be safe, 
                    # or we could approximate it. Let's stay safe.
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
        is_valid = len(missing_failures) == 0

        logger.info(f"Completeness check finished. Score: {score:.2f}%. Failures: {len(missing_failures)}")
        
        return ValidationResult(
            is_valid=is_valid,
            completeness_score=score,
            missing_chunks=missing_failures,
            total_chunks=total_chunks
        )

    def _fuzzy_check(self, text: str, start_pos: int, threshold: float = 0.85) -> bool:
        """
        Performs a token-based check to see if most of the text exists in the target.
        Helps ignore small extraction artifacts like page numbers mid-sentence.
        """
        # Extract words (tokens) of significant length
        tokens = re.findall(r'\w{4,}', text)
        if not tokens:
            return False
            
        found_tokens = 0
        # For performance, we only search in a window around the current position
        # if start_pos is provided, otherwise full search.
        # Window: 5000 chars should be plenty for a 600-char chunk.
        search_window = self.target_text[start_pos : start_pos + 10000]
        if len(search_window) < len(text):
            search_window = self.target_text # Fallback to full text if window is too small
            
        for token in tokens:
            if token in search_window:
                found_tokens += 1
        
        match_rate = found_tokens / len(tokens)
        return match_rate >= threshold

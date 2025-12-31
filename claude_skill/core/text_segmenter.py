# FROZEN: Do not modify - validation depends on identical segmentation
# See ~/.claude/skills/pdf-to-epub/reference/architecture.md
"""
Text segmentation module for deterministic slicing of long strings into overlapping chunks.
"""

import re
from dataclasses import dataclass
from typing import List

from .utils import (
    get_logger,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_OVERLAP
)

logger = get_logger(__name__)

@dataclass(frozen=True)
class Chunk:
    """
    Represents a single segment of text with position metadata.
    """
    text: str
    start_index: int
    end_index: int
    is_partial: bool = False


def normalize_whitespace(text: str) -> str:
    """
    Reduces multiple whitespace characters to single spaces and trims edges.
    """
    if not text:
        return ""
    # Replace tabs, newlines and multiple spaces with a single space
    normalized = re.sub(r'\s+', ' ', text)
    return normalized.strip()


def segment_text(
    text: str, 
    chunk_size: int = DEFAULT_CHUNK_SIZE, 
    overlap: int = DEFAULT_OVERLAP
) -> List[Chunk]:
    """
    Segments text into overlapping chunks of a fixed size.
    
    Args:
        text: The input string (will be normalized first).
        chunk_size: Maximum size of each chunk in characters.
        overlap: Number of characters to overlap with the previous chunk.
        
    Returns:
        A list of Chunk objects.
        
    Raises:
        ValueError: If overlap is greater than or equal to chunk_size.
    """
    if overlap >= chunk_size:
        raise ValueError(f"Overlap ({overlap}) must be less than chunk_size ({chunk_size})")

    # 1. Normalize whitespace
    clean_text = normalize_whitespace(text)
    
    if not clean_text:
        return []

    text_len = len(clean_text)
    chunks = []
    
    # 2. Sliding window logic
    start = 0
    while start < text_len:
        end = start + chunk_size
        
        # Determine if this is the last (partial) chunk
        is_partial = end >= text_len
        if is_partial:
            end = text_len
            
        chunk_text = clean_text[start:end]
        chunks.append(Chunk(
            text=chunk_text,
            start_index=start,
            end_index=end,
            is_partial=is_partial and (end - start < chunk_size)
        ))
        
        if is_partial:
            break
            
        # Standard sliding window step: move 'chunk_size - overlap' forward
        start = end - overlap
        
        # Safety check to avoid infinite loop if logic fails
        if start >= text_len:
            break

    logger.debug(f"Segmented text into {len(chunks)} chunks (len={text_len})")
    return chunks

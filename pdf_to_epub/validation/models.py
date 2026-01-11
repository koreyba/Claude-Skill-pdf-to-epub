"""
Data models for validation results.
"""
from dataclasses import dataclass
from typing import List
from core.text_segmenter import Chunk

@dataclass(frozen=True)
class ValidationFailure:
    """Represents a segment of text missing from the target."""
    chunk: Chunk
    reason: str = "Missing in target"

@dataclass(frozen=True)
class ValidationResult:
    """Result of a completeness check."""
    is_valid: bool
    completeness_score: float  # 0.0 to 100.0
    missing_chunks: List[ValidationFailure]
    total_chunks: int
    found_chunks: List['FoundChunk'] | None = None  # To be populated by completeness checker
    order_score: float = 100.0   # Default to 100 until calculated

@dataclass(frozen=True)
class FoundChunk:
    """Represents a chunk that was successfully found."""
    chunk: Chunk
    start_pos: int  # Position in the target document
    match_type: str = "exact" # "exact" or "fuzzy"

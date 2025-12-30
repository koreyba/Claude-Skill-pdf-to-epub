"""
Data models for validation results.
"""
from dataclasses import dataclass
from typing import List
from claude_skill.core.text_segmenter import Chunk

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

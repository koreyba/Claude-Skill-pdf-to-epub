from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class TextBlock:
    """
    Represents a raw text block extracted from PDF.
    """
    text: str
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    font_name: str
    font_size: float
    flags: int # bold/italic flags from fitz

@dataclass
class SemanticBlock:
    """
    Enriched block with structural role.
    """
    original_block: TextBlock
    role: str = "paragraph"  # h1, h2, footnote, endnote, etc.
    confidence: float = 1.0
    id: Optional[str] = None  # e.g. "chapter-1"
    metadata: Dict = field(default_factory=dict)
    endnote_num: Optional[int] = None  # Parsed endnote number (e.g., 1, 2, 3)

    # Heuristic Debugging
    score: float = 0.0
    debug_signals: list = field(default_factory=list)

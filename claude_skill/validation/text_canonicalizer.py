"""
Text canonicalization module to unify text representation from different sources (PDF, EPUB).
Handles Unicode normalization, ligatures, and hyphenation.
"""

import re
import unicodedata
from typing import Optional

from ..core.utils import get_logger

logger = get_logger(__name__)

# Common PDF ligatures and their multi-character expansions
LIGATURES_MAP = {
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "æ": "ae",
    "œ": "oe",
    "Æ": "AE",
    "Œ": "OE"
}

def resolve_ligatures(text: str) -> str:
    """
    Replaces Unicode ligatures with their individual character components.
    """
    if not text:
        return ""
    
    result = text
    for ligature, expansion in LIGATURES_MAP.items():
        result = result.replace(ligature, expansion)
    return result

def remove_hyphenation(text: str) -> str:
    """
    Removes soft hyphens and end-of-line hyphens that split words.
    Example: 'biblio-\n  teca' -> 'biblioteca'
    """
    if not text:
        return ""
    
    # Remove soft hyphen (U+00AD)
    text = text.replace("\u00ad", "")
    
    # Remove hyphens followed by whitespace and a newline
    # This joins words like 'inter-\nactive' -> 'interactive'
    return re.sub(r"-\s*\n\s*", "", text)

def canonicalize(text: str, aggressive: bool = False) -> str:
    """
    Performs full canonicalization of the input text.
    
    Args:
        text: Input string.
        aggressive: If True, performs additional heavy cleanup (e.g. common OCR fixes).
        
    Returns:
        A normalized version of the text.
    """
    if text is None:
        return ""

    # 1. Basic Unicode Normalization (NFKC)
    # NFKC = Compatibility Decomposition + Canonical Composition
    # Handles things like characters with accents, subscripts, etc.
    result = unicodedata.normalize("NFKC", text)

    # 2. Ligatures
    result = resolve_ligatures(result)

    # 3. Hyphenation
    result = remove_hyphenation(result)

    # 4. Aggressive mode (if enabled)
    if aggressive:
        # Example of aggressive cleanup (e.g., common OCR errors)
        # Fix common OCR 'rn' -> 'm' (only if surrounded by lowercase for safety)
        # result = re.sub(r"([a-z])rn([a-z])", r"\1m\2", result)
        
        # Remove control characters
        result = "".join(ch for ch in result if unicodedata.category(ch)[0] != "C")
        logger.debug("Aggressive canonicalization applied.")

    return result

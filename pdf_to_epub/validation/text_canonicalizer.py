"""
Text canonicalization module to unify text representation from different sources (PDF, EPUB).
Handles Unicode normalization, ligatures, and hyphenation.
"""

import re
import unicodedata

from core.utils import get_logger

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
    "Œ": "OE",
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

def canonicalize(text: str, aggressive: bool = False, comparison: bool = False) -> str:
    """
    Performs full canonicalization of the input text.
    
    Args:
        text: Input string.
        aggressive: If True, performs additional heavy cleanup (e.g. common OCR fixes).
        comparison: If True, normalizes punctuation and hyphenation for cross-source matching.
        
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

    # 5. Comparison mode (if enabled)
    if comparison:
        result = _normalize_for_comparison(result)

    return result


def _normalize_for_comparison(text: str) -> str:
    if not text:
        return ""
    result = text
    # Remove spaces before punctuation for consistent matching
    result = re.sub(r"\s+([,.:;!?])", r"\1", result)
    # Normalize dashes to a simple hyphen
    result = result.replace("—", "-").replace("–", "-")
    # Normalize endnote number punctuation (e.g., "1." -> "1")
    result = re.sub(r"\b(\d{1,3})\.\s", r"\1 ", result)
    # Remove hyphens used as separators before whitespace (e.g., "first- and")
    result = re.sub(r"(?<=\w)-\s+", " ", result)
    # Ignore hyphenation differences in compounds
    result = re.sub(r"(?<=\w)-(?=\w)", " ", result)
    return result


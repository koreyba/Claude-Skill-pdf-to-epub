"""
PDF Extraction module using PyMuPDF (fitz) to extract text content.
Integrates with text_canonicalizer for clean output.
"""

import fitz
from pathlib import Path
from typing import Iterator, List, Dict, Any, Optional

from claude_skill.core.utils import get_logger
from claude_skill.validation.text_canonicalizer import canonicalize

logger = get_logger(__name__)

class PDFExtractor:
    """
    Handles PDF document reading and text extraction.
    Supports memory-efficient page iteration and automatic text canonicalization.
    """
    
    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.file_path}")
        
        self.doc: Optional[fitz.Document] = None

    def __enter__(self):
        try:
            self.doc = fitz.open(self.file_path)
            if self.doc.is_encrypted:
                logger.error(f"File {self.file_path.name} is encrypted and cannot be processed.")
                raise RuntimeError("Encrypted PDF files are not supported.")
            return self
        except Exception as e:
            logger.error(f"Failed to open PDF {self.file_path}: {str(e)}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.doc:
            self.doc.close()

    def get_metadata(self) -> Dict[str, Any]:
        """
        Returns document metadata (Title, Author, etc.)
        """
        if not self.doc:
            raise RuntimeError("Document is not open. Use with context manager.")
        return self.doc.metadata

    def _extract_page_content(self, page: fitz.Page) -> str:
        """
        Extracts and cleans text from a single page using block-based heuristic.
        """
        # "blocks" mode preserves reading order better than "text"
        blocks = page.get_text("blocks", sort=True)
        
        page_text = []
        for b in blocks:
            # b[4] is the text content of the block
            block_text = b[4].strip()
            if block_text:
                page_text.append(block_text)
        
        # Join blocks with double newline to signify potential paragraphs
        raw_text = "\n\n".join(page_text)
        
        # Canonicalize text immediately
        return canonicalize(raw_text)

    def iter_pages(self) -> Iterator[str]:
        """
        Yields canonicalized text for each page one by one.
        """
        if not self.doc:
            raise RuntimeError("Document is not open. Use with context manager.")
        
        for i, page in enumerate(self.doc):
            logger.debug(f"Extracting page {i+1}/{len(self.doc)}")
            yield self._extract_page_content(page)

    def get_full_text(self) -> str:
        """
        Returns the entire document text as a single canonicalized string.
        """
        return "\n\n".join(list(self.iter_pages()))

    @property
    def page_count(self) -> int:
        return len(self.doc) if self.doc else 0

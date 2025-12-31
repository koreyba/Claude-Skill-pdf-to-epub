"""
PDF Extraction module using PyMuPDF (fitz) to extract text content.
Integrates with text_canonicalizer for clean output.
"""

import re
import fitz
from pathlib import Path
from collections import Counter
from typing import Iterator, List, Dict, Any, Optional

from .utils import get_logger
from ..validation.text_canonicalizer import canonicalize

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
        self.noise_patterns: List[str] = []

    def __enter__(self):
        try:
            self.doc = fitz.open(self.file_path)
            if self.doc.is_encrypted:
                logger.error(f"File {self.file_path.name} is encrypted and cannot be processed.")
                raise RuntimeError("Encrypted PDF files are not supported.")
            
            # Automatically identify noise patterns (headers/footers)
            self._identify_noise_patterns()
            
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

    def _identify_noise_patterns(self):
        """
        Scans the document to find recurring lines (headers, footers, copyrights).
        """
        if not self.doc or len(self.doc) < 2:
            return

        line_counts = Counter()
        # Sample up to 100 pages for better statistics
        sample_pages = self.doc[:100]
        
        for page in sample_pages:
            blocks = page.get_text("blocks")
            seen_on_page = set()
            for b in blocks:
                block_lines = b[4].split('\n')
                for line in block_lines:
                    trimmed = line.strip()
                    if len(trimmed) < 10: 
                        continue
                    # Normalize digits to # to catch page numbers
                    normalized = re.sub(r'\d+', '#', trimmed)
                    if normalized not in seen_on_page:
                        line_counts[normalized] += 1
                        seen_on_page.add(normalized)

        # A line is noise if it appears in more than 20% of sampled pages
        threshold = max(2, len(sample_pages) * 0.2)
        self.noise_patterns = [
            # We use regex to match the pattern (replacing # back with \d+)
            re.compile(re.escape(p).replace("\\#", r"\d+"))
            for p, count in line_counts.items() if count >= threshold
        ]
        
        if self.noise_patterns:
            logger.info(f"Identified {len(self.noise_patterns)} noise patterns in {self.file_path.name}")

    def _extract_page_content(self, page: fitz.Page) -> str:
        """
        Extracts and cleans text from a single page, stripping embedded noise.
        """
        blocks = page.get_text("blocks", sort=True)
        
        page_text = []
        for b in blocks:
            lines = b[4].split('\n')
            clean_lines = []
            for line in lines:
                trimmed = line.strip()
                if not trimmed:
                    continue
                    
                # Remove any noise patterns found WITHIN the line
                cleaned_line = trimmed
                for pattern in self.noise_patterns:
                    cleaned_line = pattern.sub("", cleaned_line)
                
                final_line = cleaned_line.strip()
                if final_line:
                    clean_lines.append(final_line)
            
            block_text = " ".join(clean_lines)
            if block_text:
                page_text.append(block_text)
        
        raw_text = "\n\n".join(page_text)
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

    def get_structural_blocks(self) -> List['TextBlock']:
        """
        Extracts blocks with detailed font information for structure detectors.
        Uses 'dict' output from PyMuPDF.
        """
        from ..conversion.detectors.models import TextBlock
        
        if not self.doc:
            raise RuntimeError("Document is not open.")
            
        all_blocks = []
        
        for page_num, page in enumerate(self.doc):
            # "dict" format gives structure: block -> lines -> spans -> chars
            # flags decoding: 2^0=unused, 2^1=italic, 2^2=serif, 2^3=monospace, 2^4=bold
            blocks = page.get_text("dict")["blocks"]
            
            for b in blocks:
                if b["type"] != 0: # 0 = Text, 1 = Image
                    continue
                    
                block_text = ""
                # We need to determine the dominant font properties for the block
                # Strategy: Take the font of the longest span
                font_counts = Counter()
                flag_counts = Counter()
                
                # Coordinates
                x0, y0, x1, y1 = b["bbox"]
                
                for line in b["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        if not text.strip():
                            continue
                        
                        block_text += text + " "
                        
                        # Weight by length
                        weight = len(text)
                        font_key = (span["font"], span["size"])
                        font_counts[font_key] += weight
                        flag_counts[span["flags"]] += weight
                
                if not block_text.strip():
                    continue
                    
                # Find dominant font
                if font_counts:
                    dom_font, dom_size = font_counts.most_common(1)[0][0]
                    dom_flags = flag_counts.most_common(1)[0][0]
                else:
                    dom_font, dom_size, dom_flags = "Unknown", 0.0, 0
                    
                text_block = TextBlock(
                    text=block_text.strip(),
                    page=page_num + 1, # 1-based indexing for humans
                    x0=x0, y0=y0, x1=x1, y1=y1,
                    font_name=dom_font,
                    font_size=dom_size,
                    flags=dom_flags
                )
                all_blocks.append(text_block)
                
        return all_blocks

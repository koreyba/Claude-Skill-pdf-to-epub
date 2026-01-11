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
from validation.text_canonicalizer import canonicalize

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
        self.body_font_size: Optional[float] = None

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
        font_size_counts = Counter()
        # Sample up to 100 pages for better statistics
        sample_pages = self.doc[:100]
        
        for page in sample_pages:
            page_dict = page.get_text("dict")
            seen_on_page = set()
            for b in page_dict.get("blocks", []):
                if b.get("type") != 0:
                    continue
                for line in b.get("lines", []):
                    spans = line.get("spans", [])
                    line_text = "".join(span.get("text", "") for span in spans).strip()
                    if not line_text:
                        continue
                    for span in spans:
                        span_text = span.get("text", "")
                        if not span_text.strip():
                            continue
                        font_size_counts[round(span.get("size", 0.0), 1)] += len(span_text)
                    trimmed = line_text.strip()
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

        if font_size_counts:
            self.body_font_size = font_size_counts.most_common(1)[0][0]
        
        if self.noise_patterns:
            logger.info(f"Identified {len(self.noise_patterns)} noise patterns in {self.file_path.name}")

    def _extract_page_content(self, page: fitz.Page) -> str:
        """
        Extracts and cleans text from a single page, stripping embedded noise.
        """
        page_dict = page.get_text("dict")
        page_height = page.rect.height
        
        page_text = []
        for b in page_dict.get("blocks", []):
            if b.get("type") != 0:
                continue
            lines = b.get("lines", [])
            clean_lines = []
            for line in lines:
                spans = line.get("spans", [])
                line_text = "".join(span.get("text", "") for span in spans).strip()
                if not line_text:
                    continue
                max_size = max((span.get("size", 0.0) for span in spans), default=0.0)
                y0, y1 = line.get("bbox", (0, 0, 0, 0))[1], line.get("bbox", (0, 0, 0, 0))[3]
                if self._is_header_footer_line(line_text, y0, y1, page_height, max_size):
                    continue
                    
                # Remove any noise patterns found WITHIN the line
                import re
                cleaned_line = line_text
                for pattern in self.noise_patterns:
                    cleaned_line = re.sub(pattern, "", cleaned_line)
                
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

    def get_structural_blocks(self):
        """
        Extracts blocks with detailed font information for structure detectors.
        Uses 'dict' output from PyMuPDF.
        """
        from conversion.detectors.models import TextBlock
        
        if not self.doc:
            raise RuntimeError("Document is not open.")
            
        all_blocks = []
        
        for page_num, page in enumerate(self.doc):
            page_height = page.rect.height
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

                if self._is_header_footer_line(block_text, y0, y1, page_height, dom_size):
                    continue

                for pattern in self.noise_patterns:
                    block_text = pattern.sub("", block_text)
                block_text = canonicalize(block_text)
                if not block_text.strip():
                    continue
                    
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

    def _is_header_footer_line(
        self,
        text: str,
        y0: float,
        y1: float,
        page_height: float,
        font_size: float
    ) -> bool:
        if not self._is_header_footer_position(y0, y1, page_height):
            return False
        if self.body_font_size and font_size >= self.body_font_size * 1.2:
            return False
        return self._looks_like_header_footer(text)

    def _is_header_footer_position(self, y0: float, y1: float, page_height: float) -> bool:
        if page_height <= 0:
            return False
        top_limit = page_height * 0.08
        bottom_limit = page_height * 0.92
        return y1 <= top_limit or y0 >= bottom_limit

    def _looks_like_header_footer(self, text: str) -> bool:
        stripped = text.strip()
        if not stripped:
            return False
        if re.fullmatch(r"[\d\W]+", stripped):
            return True

        letters = [ch for ch in stripped if ch.isalpha()]
        upper = [ch for ch in letters if ch.isupper()]
        upper_ratio = (len(upper) / len(letters)) if letters else 0.0

        digits = sum(1 for ch in stripped if ch.isdigit())
        digit_ratio = digits / len(stripped)
        word_count = len(stripped.split())

        if digits and digit_ratio >= 0.3 and word_count <= 8:
            return True
        if digits and upper_ratio >= 0.6 and word_count <= 10:
            return True
        if upper_ratio >= 0.75 and len(stripped) <= 80:
            return True

        return False

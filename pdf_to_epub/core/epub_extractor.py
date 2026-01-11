"""
EPUB Extraction module using eBookLib and BeautifulSoup4.
Extracts clean, canonicalized text from EPUB files.
"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Iterator, Dict, Any, Optional

from .utils import get_logger
from validation.text_canonicalizer import canonicalize

logger = get_logger(__name__)

class EPUBExtractor:
    """
    Handles EPUB document reading and text extraction.
    Ensures correct chapter order and clean text markup stripping.
    """

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"EPUB file not found: {self.file_path}")
        
        self.book: Optional[epub.EpubBook] = None

    def __enter__(self):
        try:
            # ebooklib may emit warnings during unzip/parse, which we log as debug
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.book = epub.read_epub(str(self.file_path))
            return self
        except Exception as e:
            logger.error(f"Failed to open EPUB {self.file_path}: {str(e)}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        # ebooklib keeps everything in memory, no explicit close() usually needed
        # but we clear the reference for GC.
        self.book = None

    def get_metadata(self) -> Dict[str, Any]:
        """
        Extracts document metadata (Title, Creator).
        """
        if not self.book:
            raise RuntimeError("Book is not loaded. Use with context manager.")
        
        metadata = {}
        # DC:title and DC:creator are standard EPUB metadata
        titles = self.book.get_metadata("DC", "title")
        creators = self.book.get_metadata("DC", "creator")
        
        metadata["title"] = titles[0][0] if titles else "Unknown Title"
        metadata["creator"] = creators[0][0] if creators else "Unknown Creator"
        
        return metadata

    def _clean_html(self, html_content: bytes) -> str:
        """
        Strips HTML tags and returns clean text using BeautifulSoup.
        Uses a separator to prevent word clumping.
        """
        import warnings
        from bs4 import XMLParsedAsHTMLWarning
        
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
            # Using lxml parser for speed and robustness
            soup = BeautifulSoup(html_content, "lxml")
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
            
        # Get text with space separator to handle <div>Page1</div><div>Page2</div>
        text = soup.get_text(separator=" ", strip=True)
        return text

    def iter_chapters(self) -> Iterator[str]:
        """
        Yields canonicalized text for each document item in the book's spine.
        """
        if not self.book:
            raise RuntimeError("Book is not loaded. Use with context manager.")

        # In EPUB, 'spine' defines the reading order
        for item_tuple in self.book.spine:
            # item_tuple can be (idref, linear)
            item_id = item_tuple[0]
            item = self.book.get_item_with_id(item_id)
            
            if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                logger.debug(f"Extracting chapter: {item.get_name()}")
                raw_text = self._clean_html(item.get_content())
                if raw_text.strip():
                    yield canonicalize(raw_text)

    def get_full_text(self) -> str:
        """
        Returns the entire book content as a single canonicalized string.
        """
        return "\n\n".join(list(self.iter_chapters()))

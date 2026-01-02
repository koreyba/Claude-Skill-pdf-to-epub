import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from pdf_to_epub.core.epub_extractor import EPUBExtractor

class TestEPUBExtractor(unittest.TestCase):
    
    def setUp(self):
        # Real file path provided by user
        self.test_epub = Path("tests/fixtures/Excerpt_B_The_Many_Ways_We_Touch-3.epub")

    def test_clean_html_basic(self):
        # We need an instance to test private method, but it needs a valid path to init
        # So we skip init check or use a dummy that exists
        with patch("pathlib.Path.exists", return_value=True):
            extractor = EPUBExtractor(Path("dummy.epub"))
            html = b"<div>Hello<span>World</span></div><script>alert(1)</script>"
            # BeautifulSoup with separator=' ' should produce "Hello World"
            cleaned = extractor._clean_html(html)
            self.assertEqual(cleaned, "Hello World")
            self.assertNotIn("alert", cleaned)

    def test_clean_html_malformed(self):
        with patch("pathlib.Path.exists", return_value=True):
            extractor = EPUBExtractor(Path("dummy.epub"))
            # BS4 should handle unclosed tags gracefully
            html = b"<p>Hello <b>World"
            cleaned = extractor._clean_html(html)
            self.assertEqual(cleaned, "Hello World")

    def test_get_metadata_handles_missing(self):
        with patch("pathlib.Path.exists", return_value=True):
            extractor = EPUBExtractor(Path("dummy.epub"))
            mock_book = MagicMock()
            # Return empty lists for any metadata request
            mock_book.get_metadata.return_value = []
            extractor.book = mock_book
            
            meta = extractor.get_metadata()
            self.assertEqual(meta["title"], "Unknown Title")
            self.assertEqual(meta["creator"], "Unknown Creator")

    def test_iter_chapters_no_docs(self):
        with patch("pathlib.Path.exists", return_value=True):
            extractor = EPUBExtractor(Path("dummy.epub"))
            mock_book = MagicMock()
            # Spine points to an item that is NOT a document
            mock_book.spine = [("image1", "yes")]
            mock_item = MagicMock()
            mock_item.get_type.return_value = 999 # Not ITEM_DOCUMENT
            mock_book.get_item_with_id.return_value = mock_item
            extractor.book = mock_book
            
            chapters = list(extractor.iter_chapters())
            self.assertEqual(len(chapters), 0)

    def test_integration_with_real_file(self):
        """
        Integration test with the real EPUB file.
        """
        if not self.test_epub.exists():
            self.skipTest(f"Skipping integration test: {self.test_epub} not found")
            
        with EPUBExtractor(self.test_epub) as extractor:
            # Check metadata
            meta = extractor.get_metadata()
            self.assertIn("title", meta)
            print(f"\n[EPUB INFO] Title: {meta['title']}, Author: {meta['creator']}")
            
            # Extract chapters
            chapters = list(extractor.iter_chapters())
            self.assertGreater(len(chapters), 0)
            
            # Print preview of the first chapter
            print(f"[EPUB PREVIEW] Chapter 1: {chapters[0][:200]}...")

if __name__ == "__main__":
    unittest.main()

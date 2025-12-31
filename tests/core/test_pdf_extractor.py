import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from claude_skill.core.pdf_extractor import PDFExtractor

class TestPDFExtractor(unittest.TestCase):
    
    def setUp(self):
        self.test_pdf = Path("tests/fixtures/Excerpt_B_The_Many_Ways_We_Touch_Three_P.pdf")

    @patch("pathlib.Path.exists")
    @patch("fitz.open")
    def test_context_manager_and_encryption_check(self, mock_fitz_open, mock_exists):
        # Setup mock
        mock_exists.return_value = True
        mock_doc = MagicMock()
        mock_doc.is_encrypted = False
        mock_fitz_open.return_value = mock_doc
        
        # Test basic flow
        with PDFExtractor(Path("virtual.pdf")) as extractor:
            self.assertEqual(extractor.doc, mock_doc)
            
    @patch("pathlib.Path.exists")
    @patch("fitz.open")
    def test_encrypted_pdf_raises_error(self, mock_fitz_open, mock_exists):
        mock_exists.return_value = True
        mock_doc = MagicMock()
        mock_doc.is_encrypted = True
        mock_fitz_open.return_value = mock_doc
        
        extractor = PDFExtractor(Path("encrypted.pdf"))
        with self.assertRaises(RuntimeError) as cm:
            with extractor:
                pass
        self.assertIn("Encrypted", str(cm.exception))

    @patch("pathlib.Path.exists")
    @patch("fitz.open")
    def test_corrupted_pdf_raises_error(self, mock_fitz_open, mock_exists):
        mock_exists.return_value = True
        import fitz
        mock_fitz_open.side_effect = fitz.FileDataError("cannot open broken file")
        
        extractor = PDFExtractor(Path("broken.pdf"))
        with self.assertRaises(fitz.FileDataError):
            with extractor:
                pass

    @patch("pathlib.Path.exists")
    @patch("fitz.open")
    def test_empty_page_handling(self, mock_fitz_open, mock_exists):
        mock_exists.return_value = True
        mock_page = MagicMock()
        mock_page.get_text.return_value = {"blocks": []} # No blocks
        
        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.is_encrypted = False
        mock_fitz_open.return_value = mock_doc
        
        with PDFExtractor(Path("empty.pdf")) as extractor:
            text = extractor.get_full_text()
            self.assertEqual(text, "")

    @patch("pathlib.Path.exists")
    def test_header_footer_line_detection(self, mock_exists):
        mock_exists.return_value = True
        extractor = PDFExtractor(Path("virtual.pdf"))
        extractor.body_font_size = 11.0
        page_height = 800.0

        self.assertTrue(
            extractor._is_header_footer_line(
                "27 SOME EVERYDAY EXAMPLES", 0, 40, page_height, 11.0
            )
        )
        self.assertTrue(
            extractor._is_header_footer_line(
                "94", 760, 790, page_height, 11.0
            )
        )
        self.assertFalse(
            extractor._is_header_footer_line(
                "The result, as you can see in figure", 0, 40, page_height, 11.0
            )
        )
        self.assertFalse(
            extractor._is_header_footer_line(
                "Excerpt C: The Ways We Are in This Together", 0, 40, page_height, 16.0
            )
        )
        self.assertFalse(
            extractor._is_header_footer_line(
                "27 SOME EVERYDAY EXAMPLES", 200, 240, page_height, 11.0
            )
        )

    def test_integration_with_real_file(self):
        """
        This test will only run if tests/fixtures/test.pdf exists.
        It's a smoke test for the real library integration.
        """
        if not self.test_pdf.exists():
            self.skipTest(f"Skipping integration test: {self.test_pdf} not found")
            
        with PDFExtractor(self.test_pdf) as extractor:
            metadata = extractor.get_metadata()
            self.assertIsInstance(metadata, dict)
            
            # Extract first page
            pages = list(extractor.iter_pages())
            self.assertGreater(len(pages), 0)
            self.assertIsInstance(pages[0], str)
            
            logger_info = f"Processed PDF: {self.test_pdf.name}, Pages: {len(pages)}"
            print(f"\n[INFO] {logger_info}")
            print(f"[PREVIEW] {pages[0][:200]}...")

if __name__ == "__main__":
    unittest.main()

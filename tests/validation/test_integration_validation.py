import unittest
from pathlib import Path
from claude_skill.core.pdf_extractor import PDFExtractor
from claude_skill.core.epub_extractor import EPUBExtractor
from claude_skill.validation.completeness_checker import CompletenessChecker

class TestIntegrationValidation(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Extract text once for all tests in this class to save time."""
        project_root = Path(__file__).parent.parent.parent
        cls.pdf_path = project_root / "tests" / "fixtures" / "Excerpt_B_The_Many_Ways_We_Touch_Three_P.pdf"
        cls.epub_path = project_root / "tests" / "fixtures" / "Excerpt_B_The_Many_Ways_We_Touch-3.epub"
        
        if cls.pdf_path.exists() and cls.epub_path.exists():
            with PDFExtractor(cls.pdf_path) as pdf:
                cls.source_text = pdf.get_full_text()
            with EPUBExtractor(cls.epub_path) as epub:
                cls.target_text = epub.get_full_text()
        else:
            cls.source_text = None
            cls.target_text = None

    def setUp(self):
        if self.source_text is None:
            self.skipTest("Integration fixtures not found")

    def test_baseline_completeness(self):
        """Verify that the current EPUB has 100% of the PDF text."""
        checker = CompletenessChecker(self.source_text, self.target_text)
        result = checker.check()
        
        print(f"\n[INTEGRATION] Baseline Score: {result.completeness_score:.2f}%")
        self.assertGreaterEqual(result.completeness_score, 99.9, "Baseline should be near 100%")

    def test_sensitivity_small_loss(self):
        """Intentionally remove 5% of text and verify the checker catches it."""
        mid = len(self.target_text) // 2
        gap = int(len(self.target_text) * 0.05)
        corrupted_text = self.target_text[:mid] + self.target_text[mid + gap:]
        
        checker = CompletenessChecker(self.source_text, corrupted_text)
        result = checker.check()
        
        print(f"[INTEGRATION] Corrupted -5% Score: {result.completeness_score:.2f}%")
        # Score should drop significantly below 100
        self.assertLess(result.completeness_score, 97.0)
        self.assertGreater(len(result.missing_chunks), 0)

    def test_sensitivity_large_loss(self):
        """Intentionally remove 50% of text and verify the checker catches it."""
        corrupted_text = self.target_text[:len(self.target_text) // 2]
        
        checker = CompletenessChecker(self.source_text, corrupted_text)
        result = checker.check()
        
        print(f"[INTEGRATION] Corrupted -50% Score: {result.completeness_score:.2f}%")
        # Score should be around 50-60%
        self.assertLess(result.completeness_score, 70.0)
        self.assertGreater(len(result.missing_chunks), 50)

if __name__ == "__main__":
    unittest.main()

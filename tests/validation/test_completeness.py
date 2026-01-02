import unittest
from pdf_to_epub.validation.completeness_checker import CompletenessChecker

class TestCompletenessChecker(unittest.TestCase):
    
    def test_identical_text(self):
        text = "This is a simple text."
        checker = CompletenessChecker(text, text)
        result = checker.check(chunk_size=10, overlap=0)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.completeness_score, 100.0)

    def test_missing_significant_content(self):
        source = "CHUNK_ONE_UNIQUE CHUNK_TWO_MISSING CHUNK_THREE_UNIQUE"
        target = "CHUNK_ONE_UNIQUE CHUNK_THREE_UNIQUE"
        
        checker = CompletenessChecker(source, target, min_significant_len=1)
        result = checker.check(chunk_size=10, overlap=2)
        
        self.assertFalse(result.is_valid)
        self.assertLess(result.completeness_score, 100.0)
        self.assertGreater(len(result.missing_chunks), 0)

    def test_noise_handling(self):
        # We want "CONTENT " to be found, and "GARBAGE" to be ignored noise.
        source = "CONTENT GARBAGE"
        target = "CONTENT"
        
        # chunk_size=7 matches "CONTENT" exactly.
        checker = CompletenessChecker(source, target, min_significant_len=10)
        result = checker.check(chunk_size=7, overlap=0)
        
        self.assertTrue(result.is_valid) 
        self.assertLess(result.completeness_score, 100.0) 
        self.assertEqual(len(result.missing_chunks), 0)

    def test_reordering(self):
        source = "Part1 Part2"
        target = "Part2 Part1"
        
        checker = CompletenessChecker(source, target)
        result = checker.check(chunk_size=5, overlap=0)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.completeness_score, 100.0)
        
    def test_empty_inputs(self):
        # Empty source
        checker = CompletenessChecker("", "Target")
        result = checker.check()
        self.assertTrue(result.is_valid)
        self.assertEqual(result.completeness_score, 100.0)
        
        # Empty target
        checker = CompletenessChecker("Source text longer than chunk", "", min_significant_len=1)
        # Explicit overlap=0 to avoid ValueError with small chunk_size
        result = checker.check(chunk_size=5, overlap=0)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.completeness_score, 0.0)

if __name__ == "__main__":
    unittest.main()

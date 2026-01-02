import unittest
from pdf_to_epub.core.text_segmenter import segment_text, normalize_whitespace, Chunk

class TestTextSegmenter(unittest.TestCase):
    
    def test_normalize_whitespace(self):
        self.assertEqual(normalize_whitespace("  hello   world  "), "hello world")
        self.assertEqual(normalize_whitespace("line\nbreak\ttab"), "line break tab")
        self.assertEqual(normalize_whitespace("   "), "")
        self.assertEqual(normalize_whitespace(None), "")

    def test_segment_empty_string(self):
        self.assertEqual(segment_text(""), [])
        self.assertEqual(segment_text("    "), [])

    def test_segment_short_string(self):
        # chunk_size=10, text len=5
        text = "12345"
        chunks = segment_text(text, chunk_size=10, overlap=2)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].text, "12345")
        self.assertEqual(chunks[0].start_index, 0)
        self.assertEqual(chunks[0].end_index, 5)
        self.assertTrue(chunks[0].is_partial)

    def test_segment_exact_size(self):
        text = "1234567890"
        chunks = segment_text(text, chunk_size=10, overlap=2)
        self.assertEqual(len(chunks), 1)
        self.assertFalse(chunks[0].is_partial)

    def test_segment_multiple_chunks(self):
        # text="1234567890", chunk_size=6, overlap=2
        # Expected chunks:
        # 1: "123456" (0-6)
        # 2: "567890" (start = 6-2=4, end = 4+6=10)
        text = "1234567890"
        chunks = segment_text(text, chunk_size=6, overlap=2)
        
        self.assertEqual(len(chunks), 2)
        
        self.assertEqual(chunks[0].text, "123456")
        self.assertEqual(chunks[0].start_index, 0)
        self.assertEqual(chunks[0].end_index, 6)
        
        self.assertEqual(chunks[1].text, "567890")
        self.assertEqual(chunks[1].start_index, 4)
        self.assertEqual(chunks[1].end_index, 10)

    def test_segment_with_is_partial_flag(self):
        # text size 8, chunk 6, overlap 2
        # C1: 0-6 "123456"
        # C2: 4-8 "5678" (partial)
        text = "12345678"
        chunks = segment_text(text, chunk_size=6, overlap=2)
        self.assertEqual(len(chunks), 2)
        self.assertFalse(chunks[0].is_partial)
        self.assertTrue(chunks[1].is_partial)
        self.assertEqual(chunks[1].text, "5678")

    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            segment_text("some text", chunk_size=10, overlap=10)
        with self.assertRaises(ValueError):
            segment_text("some text", chunk_size=10, overlap=11)

if __name__ == "__main__":
    unittest.main()

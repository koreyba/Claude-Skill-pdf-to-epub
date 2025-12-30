import unittest
from claude_skill.validation.lis import calculate_lis_length
from claude_skill.validation.order_checker import OrderChecker
from claude_skill.validation.models import FoundChunk
from claude_skill.core.text_segmenter import Chunk

class TestLIS(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(calculate_lis_length([]), 0)
        
    def test_single(self):
        self.assertEqual(calculate_lis_length([10]), 1)
        
    def test_strictly_increasing(self):
        self.assertEqual(calculate_lis_length([1, 2, 3, 4, 5]), 5)
        
    def test_strictly_decreasing(self):
        # LIS is just 1 element (e.g., [5], or [4], ...)
        self.assertEqual(calculate_lis_length([5, 4, 3, 2, 1]), 1)
        
    def test_mixed(self):
        # [1, 3, 2, 4] -> 1, 3, 4 OR 1, 2, 4 (Length 3)
        self.assertEqual(calculate_lis_length([1, 3, 2, 4]), 3)
        
    def test_duplicates(self):
        # Strictly increasing means duplicates don't extend length?
        # Our implementation uses bisect_left, which handles >=.
        # Let's verify behavior. [1, 2, 2, 3] -> 1, 2, 3 (Length 3)?
        # Actually bisect_left replaces the first element >= x.
        # If we have [1, 2] and next is 2: idx of 2 is 1 (index of '2'). tails[1] become 2.
        # So it stays length 2. Correct for STRICTLY increasing.
        self.assertEqual(calculate_lis_length([1, 2, 2, 3]), 3)

class TestOrderChecker(unittest.TestCase):
    def _make_found_chunks(self, positions):
        """Helper to create dummy found chunks with given positions."""
        # Chunk text doesn't matter for order check
        dummy_chunk = Chunk(text="dummy", start_index=0, end_index=10)
        return [
            FoundChunk(chunk=dummy_chunk, start_pos=pos, match_type="exact")
            for pos in positions
        ]

    def test_perfect_order(self):
        chunks = self._make_found_chunks([100, 200, 300, 400])
        checker = OrderChecker(chunks)
        self.assertAlmostEqual(checker.check(), 100.0)

    def test_empty_input(self):
        checker = OrderChecker([])
        # We decided to return 100.0 for empty to avoid false negatives
        self.assertEqual(checker.check(), 100.0)

    def test_worst_case_reversed(self):
        # [400, 300, 200, 100] -> LIS is 1. Total 4. Score 25%.
        chunks = self._make_found_chunks([400, 300, 200, 100])
        checker = OrderChecker(chunks)
        self.assertAlmostEqual(checker.check(), 25.0)

    def test_minor_swap(self):
        # [100, 300, 200, 400] -> LIS 3 ([100, 200, 400] or [100, 300, 400]). 
        # Total 4. Score 75%.
        chunks = self._make_found_chunks([100, 300, 200, 400])
        checker = OrderChecker(chunks)
        self.assertAlmostEqual(checker.check(), 75.0)

if __name__ == "__main__":
    unittest.main()

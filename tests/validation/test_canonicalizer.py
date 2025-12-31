import unittest
from claude_skill.validation.text_canonicalizer import canonicalize, resolve_ligatures, remove_hyphenation

class TestTextCanonicalizer(unittest.TestCase):
    
    def test_resolve_ligatures(self):
        self.assertEqual(resolve_ligatures("ﬁ"), "fi")
        self.assertEqual(resolve_ligatures("ﬂ"), "fl")
        self.assertEqual(resolve_ligatures("ﬀ"), "ff")
        self.assertEqual(resolve_ligatures("ﬃ"), "ffi")
        self.assertEqual(resolve_ligatures("ﬄ"), "ffl")
        self.assertEqual(resolve_ligatures("æ"), "ae")
        self.assertEqual(resolve_ligatures("œ"), "oe")
        self.assertEqual(resolve_ligatures("Æ"), "AE")
        self.assertEqual(resolve_ligatures("No ligatures here"), "No ligatures here")

    def test_remove_hyphenation(self):
        # Soft hyphen U+00AD
        self.assertEqual(remove_hyphenation("soft\u00adhyphen"), "softhyphen")
        
        # End of line hyphenation
        self.assertEqual(remove_hyphenation("inter-\nnational"), "international")
        self.assertEqual(remove_hyphenation("inter-  \n  national"), "international")
        
        # Normal hyphen should stay
        self.assertEqual(remove_hyphenation("long-term"), "long-term")
        # Hyphen followed by space but NO newline should stay (conservative)
        self.assertEqual(remove_hyphenation("word- word"), "word- word")

    def test_unicode_normalization(self):
        # 'e' + 'combining acute accent' (U+0301)
        # NFKC should compose them into single 'é'
        text = "e\u0301"
        self.assertEqual(canonicalize(text), "\u00e9")

    def test_full_canonicalize_combo(self):
        # Mixture of ligature, hyphenation across line and unicode
        input_text = "Thﬃs is a long-\nterm project æsthetic."
        # Expected:
        # Thffis (ligature) 
        # is a long-term (hyphen stay because it is not split to NEXT line by newline) 
        # Wait, my logic for hyphen: if it is "long-\nterm", it gets joined.
        # "long-term" project.
        expected = "Thffis is a longterm project aesthetic."
        self.assertEqual(canonicalize(input_text), expected)

    def test_aggressive_mode(self):
        # Control character \u0007 (BEL) should be removed in aggressive mode
        text = "Clean\u0007This"
        self.assertEqual(canonicalize(text, aggressive=False), "Clean\u0007This")
        self.assertEqual(canonicalize(text, aggressive=True), "CleanThis")

    def test_edge_cases(self):
        self.assertEqual(canonicalize(""), "")
        self.assertEqual(canonicalize(None), "")

    def test_comparison_mode_normalization(self):
        text = "Excerpt F : Integral Post-Metaphysics and third-person"
        expected = "Excerpt F: Integral Post Metaphysics and third person"
        self.assertEqual(canonicalize(text, comparison=True), expected)

if __name__ == "__main__":
    unittest.main()

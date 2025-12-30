"""Compare original EPUB with our conversion."""
from pathlib import Path
from claude_skill.core.pdf_extractor import PDFExtractor
from claude_skill.core.epub_extractor import EPUBExtractor
from claude_skill.validation.completeness_checker import CompletenessChecker

pdf_path = Path("tests/fixtures/Excerpt_B_The_Many_Ways_We_Touch_Three_P.pdf")
epub_original = Path("tests/fixtures/Excerpt_B_The_Many_Ways_We_Touch-3.epub")
epub_ours = Path("output/excerpt_b_ours.epub")

print("=" * 60)
print("COMPARISON: Original EPUB vs Our Conversion")
print("=" * 60)

# Extract PDF text
with PDFExtractor(str(pdf_path)) as extractor:
    pdf_blocks = extractor.get_structural_blocks()
    pdf_text = " ".join(block.text for block in pdf_blocks)

print(f"\nPDF source: {len(pdf_text)} chars, {len(pdf_blocks)} blocks")

# Analyze ORIGINAL EPUB
print("\n--- ORIGINAL EPUB (from fixtures) ---")
with EPUBExtractor(str(epub_original)) as epub:
    orig_text = epub.get_full_text()
    orig_meta = epub.get_metadata()

print(f"Text length: {len(orig_text)} chars")
print(f"Title: {orig_meta.get('title', 'N/A')}")
print(f"Creator: {orig_meta.get('creator', 'N/A')}")

orig_checker = CompletenessChecker(pdf_text, orig_text)
orig_result = orig_checker.check()
print(f"Completeness: {orig_result.completeness_score:.1f}%")
print(f"Order score: {orig_result.order_score:.1f}%")

# Analyze OUR EPUB
print("\n--- OUR EPUB (new conversion) ---")
with EPUBExtractor(str(epub_ours)) as epub:
    ours_text = epub.get_full_text()
    ours_meta = epub.get_metadata()

print(f"Text length: {len(ours_text)} chars")
print(f"Title: {ours_meta.get('title', 'N/A')}")
print(f"Creator: {ours_meta.get('creator', 'N/A')}")

ours_checker = CompletenessChecker(pdf_text, ours_text)
ours_result = ours_checker.check()
print(f"Completeness: {ours_result.completeness_score:.1f}%")
print(f"Order score: {ours_result.order_score:.1f}%")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"                    Original    Ours")
print(f"Completeness:       {orig_result.completeness_score:6.1f}%    {ours_result.completeness_score:.1f}%")
print(f"Order:              {orig_result.order_score:6.1f}%    {ours_result.order_score:.1f}%")
print(f"Text chars:         {len(orig_text):6d}     {len(ours_text)}")
print(f"File size:          {epub_original.stat().st_size/1024:6.1f} KB   {epub_ours.stat().st_size/1024:.1f} KB")

diff_complete = ours_result.completeness_score - orig_result.completeness_score
diff_order = ours_result.order_score - orig_result.order_score
print(f"\nDifference: Completeness {diff_complete:+.1f}%, Order {diff_order:+.1f}%")

if diff_complete > 0:
    print("\n>>> OUR conversion is MORE COMPLETE")
elif diff_complete < 0:
    print("\n>>> ORIGINAL is MORE COMPLETE")
else:
    print("\n>>> EQUAL completeness")

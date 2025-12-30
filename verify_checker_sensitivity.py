from pathlib import Path
from claude_skill.core.pdf_extractor import PDFExtractor
from claude_skill.core.epub_extractor import EPUBExtractor
from claude_skill.validation.completeness_checker import CompletenessChecker

def verify_sensitivity():
    project_root = Path("c:/Projects/Pdf-to-epub-skill")
    pdf_path = project_root / "tests" / "fixtures" / "Excerpt_B_The_Many_Ways_We_Touch_Three_P.pdf"
    epub_path = project_root / "tests" / "fixtures" / "Excerpt_B_The_Many_Ways_We_Touch-3.epub"
    
    print("--- Sensitivity Test: Loading Data ---")
    with PDFExtractor(pdf_path) as pdf:
        source_text = pdf.get_full_text()
    with EPUBExtractor(epub_path) as epub:
        original_target = epub.get_full_text()

    # Baseline check
    checker_base = CompletenessChecker(source_text, original_target)
    base_result = checker_base.check()
    print(f"Baseline Score: {base_result.completeness_score:.2f}% (Expected ~100%)")

    # Case 1: Remove 5% of text from the middle (simulating a lost paragraph or page)
    mid = len(original_target) // 2
    gap_5 = int(len(original_target) * 0.05)
    corrupted_5 = original_target[:mid] + original_target[mid + gap_5:]
    
    checker_5 = CompletenessChecker(source_text, corrupted_5)
    res_5 = checker_5.check()
    print(f"Corrupted -5% Score: {res_5.completeness_score:.2f}% (Expected ~95%)")
    print(f"Failures found: {len(res_5.missing_chunks)}")

    # Case 2: Remove 50% of text (simulating a massive conversion failure)
    corrupted_50 = original_target[:len(original_target) // 2]
    
    checker_50 = CompletenessChecker(source_text, corrupted_50)
    res_50 = checker_50.check()
    print(f"Corrupted -50% Score: {res_50.completeness_score:.2f}% (Expected ~50%)")
    print(f"Failures found: {len(res_50.missing_chunks)}")

    # Final verdict
    if res_5.completeness_score < 98 and res_50.completeness_score < 60:
        print("\n✅ VERDICT: The Checker is SENSITIVE and reliable.")
    else:
        print("\n❌ VERDICT: The Checker is BLIND. Something is wrong.")

if __name__ == "__main__":
    verify_sensitivity()

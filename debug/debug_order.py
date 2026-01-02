from pathlib import Path
from pdf_to_epub.core.pdf_extractor import PDFExtractor
from pdf_to_epub.core.epub_extractor import EPUBExtractor
from pdf_to_epub.validation.completeness_checker import CompletenessChecker
from pdf_to_epub.validation.lis import calculate_lis_length

def debug_order():
    project_root = Path("c:/Projects/Pdf-to-epub-skill")
    pdf_path = project_root / "tests" / "fixtures" / "Excerpt_B_The_Many_Ways_We_Touch_Three_P.pdf"
    epub_path = project_root / "tests" / "fixtures" / "Excerpt_B_The_Many_Ways_We_Touch-3.epub"
    
    print("--- Debugging Order... ---")
    with PDFExtractor(pdf_path) as pdf:
        source_text = pdf.get_full_text()
    with EPUBExtractor(epub_path) as epub:
        original_target = epub.get_full_text()

    checker = CompletenessChecker(source_text, original_target)
    result = checker.check()
    
    print(f"Completeness Score: {result.completeness_score:.2f}%")
    print(f"Order Score: {result.order_score:.2f}%")
    
    found_chunks = result.found_chunks
    if not found_chunks:
        print("No chunks found!")
        return

    # Let's inspect the sequence of positions
    positions = [fc.start_pos for fc in found_chunks]
    
    # Simple check for drops
    print("\n--- Identifying Order Violations ---")
    prev_pos = -1
    violations = 0
    
    for i, fc in enumerate(found_chunks):
        current_pos = fc.start_pos
        
        # If current position dropped significantly compared to previous max, it's a jump back
        if current_pos < prev_pos:
            # Only print significant jumps backwards
            if (prev_pos - current_pos) > 100: 
                print(f"[Jump Back] Chunk #{i} (PDF Order) found at EPUB pos {current_pos} (Previous was {prev_pos})")
                print(f"   Text: '{fc.chunk.text[:50]}...'")
                violations += 1
                if violations >= 10:
                    print("... (stopping after 10 violations)")
                    break
        else:
            prev_pos = current_pos

if __name__ == "__main__":
    debug_order()

from pathlib import Path
from claude_skill.core.pdf_extractor import PDFExtractor
from claude_skill.core.epub_extractor import EPUBExtractor
from claude_skill.validation.completeness_checker import CompletenessChecker

def generate_detailed_report():
    project_root = Path("c:/Projects/Pdf-to-epub-skill")
    pdf_path = project_root / "tests" / "fixtures" / "Excerpt_B_The_Many_Ways_We_Touch_Three_P.pdf"
    epub_path = project_root / "tests" / "fixtures" / "Excerpt_B_The_Many_Ways_We_Touch-3.epub"
    
    if not pdf_path.exists() or not epub_path.exists():
        print("Error: Fixtures not found.")
        return

    print("Extracting and validating... please wait.")
    
    with PDFExtractor(pdf_path) as pdf:
        pdf_text = pdf.get_full_text()
    with EPUBExtractor(epub_path) as epub:
        epub_text = epub.get_full_text()
        
    checker = CompletenessChecker(pdf_text, epub_text)
    result = checker.check()
    
    report_path = project_root / "missing_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"COMPLETENESS REPORT\n")
        f.write(f"Score: {result.completeness_score:.2f}%\n")
        f.write(f"Total Chunks: {result.total_chunks}\n")
        f.write(f"Missing Chunks: {len(result.missing_chunks)}\n")
        f.write("="*50 + "\n\n")
        
        for i, failure in enumerate(result.missing_chunks):
            f.write(f"CHUNK #{i+1} (Range: {failure.chunk.start_index}-{failure.chunk.end_index})\n")
            f.write(f"CONTENT:\n{failure.chunk.text}\n")
            f.write("-" * 30 + "\n\n")
            
    print(f"Report generated: {report_path}")
    print(f"Open it to see exactly what is missing.")

if __name__ == "__main__":
    generate_detailed_report()

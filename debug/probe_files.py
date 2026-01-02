from pathlib import Path
from pdf_to_epub.core.pdf_extractor import PDFExtractor
from pdf_to_epub.core.epub_extractor import EPUBExtractor

def probe():
    project_root = Path("c:/Projects/Pdf-to-epub-skill")
    pdf_path = project_root / "tests" / "fixtures" / "Excerpt_B_The_Many_Ways_We_Touch_Three_P.pdf"
    epub_path = project_root / "tests" / "fixtures" / "Wilber_The_Ways_We_Are_in_This_Together_WITH_IMAGES.epub"
    
    print("\n--- PDF CONTENT PREVIEW ---")
    with PDFExtractor(pdf_path) as pdf:
        text = pdf.get_full_text()
        print(text[:500])
        
    print("\n--- EPUB CONTENT PREVIEW ---")
    with EPUBExtractor(epub_path) as epub:
        text = epub.get_full_text()
        print(text[:500])

if __name__ == "__main__":
    probe()

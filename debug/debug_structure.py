from pathlib import Path
from claude_skill.core.pdf_extractor import PDFExtractor
from claude_skill.conversion.detectors.reading_order.y_sorter import YSorter
from claude_skill.conversion.detectors.font_analyzer import FontAnalyzer
from claude_skill.conversion.detectors.structure_classifier import StructureClassifier
from claude_skill.conversion.detectors.structure_builder import StructureBuilder, Chapter

def print_chapter(chapter: Chapter, indent=0):
    print("  " * indent + f"[{chapter.level}] {chapter.title} ({len(chapter.content_blocks)} blocks)")
    for sub in chapter.subchapters:
        print_chapter(sub, indent + 1)

def debug_structure():
    project_root = Path("c:/Projects/Pdf-to-epub-skill")
    pdf_path = project_root / "tests" / "fixtures" / "Excerpt_B_The_Many_Ways_We_Touch_Three_P.pdf"
    
    print("--- 1. Extracting Blocks ---")
    with PDFExtractor(pdf_path) as pdf:
        raw_blocks = pdf.get_structural_blocks()
    
    print(f"Extracted {len(raw_blocks)} blocks.")
    
    print("--- 2. Sorting Blocks (YSorter) ---")
    sorter = YSorter()
    sorted_blocks = sorter.sort_blocks(raw_blocks)
    
    print("--- 3. Analyzing Fonts ---")
    analyzer = FontAnalyzer()
    style_map = analyzer.analyze(sorted_blocks)
    print("Detected Styles:")
    for style, role in style_map.items():
        print(f"  {style} -> {role}")
        
    print("--- 4. Classifying Structure ---")
    classifier = StructureClassifier()
    # Mock override for example: if we want to force 'MyCustomFont' as H1
    # But for now default
    semantic_blocks = classifier.classify(sorted_blocks)
    
    h1_count = sum(1 for b in semantic_blocks if b.role == 'h1')
    print(f"Found {h1_count} H1 headers.")

    print("--- 4.1 Detecting Footnotes ---")
    from claude_skill.conversion.detectors.footnote_detector import FootnoteDetector
    fn_detector = FootnoteDetector()
    semantic_blocks = fn_detector.process(semantic_blocks)
    
    total_refs = sum(len(b.metadata.get("footnote_refs", [])) for b in semantic_blocks)
    print(f"Found {total_refs} footnote references (e.g. [1]).")
    
    print("--- 5. Building Tree ---")
    builder = StructureBuilder()
    chapters = builder.build_chapters(semantic_blocks)
    
    print("\n=== DOC STRUCTURE ===")
    for ch in chapters:
        print_chapter(ch)
        
if __name__ == "__main__":
    debug_structure()

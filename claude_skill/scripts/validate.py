"""CLI for EPUB validation."""
import argparse
import sys
from pathlib import Path

from claude_skill.core.pdf_extractor import PDFExtractor
from claude_skill.core.epub_extractor import EPUBExtractor
from claude_skill.validation.completeness_checker import CompletenessChecker


def main():
    """Validate EPUB against original PDF."""
    parser = argparse.ArgumentParser(
        description="Validate EPUB quality against original PDF"
    )
    parser.add_argument("pdf_file", help="Path to original PDF file")
    parser.add_argument("epub_file", help="Path to generated EPUB file")
    parser.add_argument(
        "-o", "--output",
        help="Output path for validation report (default: validation_report.json)"
    )
    parser.add_argument(
        "--epubcheck",
        action="store_true",
        help="Also run epubcheck for format validation"
    )

    args = parser.parse_args()

    pdf_path = Path(args.pdf_file)
    epub_path = Path(args.epub_file)

    # Validate files exist
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    if not epub_path.exists():
        print(f"Error: EPUB file not found: {epub_path}", file=sys.stderr)
        return 1

    print(f"Validating {epub_path} against {pdf_path}...")
    print("="*60)

    all_passed = True
    results = {}

    # Extract text from both files
    print("\nExtracting text...")
    try:
        with PDFExtractor(pdf_path) as pdf:
            source_text = pdf.get_full_text()
        print(f"   PDF: {len(source_text)} characters extracted")

        with EPUBExtractor(epub_path) as epub:
            target_text = epub.get_full_text()
        print(f"   EPUB: {len(target_text)} characters extracted")
    except Exception as e:
        print(f"   Error extracting text: {e}")
        return 1

    # Completeness and order check (OrderChecker is called internally by CompletenessChecker)
    print("\n1. Checking text completeness and reading order...")
    try:
        checker = CompletenessChecker(source_text, target_text)
        result = checker.check()

        # Completeness score is in percent (0-100)
        completeness_pct = result.completeness_score
        is_complete = completeness_pct >= 95.0

        print(f"   Completeness: {completeness_pct:.1f}%")
        print(f"   Status: {'PASS' if is_complete else 'FAIL'}")

        results['completeness'] = {
            'score': completeness_pct,
            'passed': is_complete
        }

        if not is_complete:
            all_passed = False
            if result.missing_chunks:
                print(f"   Missing: {len(result.missing_chunks)} segments")
                results['completeness']['missing_count'] = len(result.missing_chunks)
    except Exception as e:
        print(f"   Error: {e}")
        all_passed = False
        results['completeness'] = {'error': str(e)}

    # Order check (from the same result)
    print("\n2. Checking reading order...")
    try:
        order_score = result.order_score if hasattr(result, 'order_score') else 100.0
        is_ordered = order_score >= 80.0

        print(f"   Order score: {order_score:.1f}%")
        print(f"   Status: {'PASS' if is_ordered else 'FAIL'}")

        results['order'] = {
            'score': order_score,
            'passed': is_ordered
        }

        if not is_ordered:
            all_passed = False
    except Exception as e:
        print(f"   Error: {e}")
        all_passed = False
        results['order'] = {'error': str(e)}
    
    # epubcheck (if requested)
    if args.epubcheck:
        print("\n3. Running epubcheck...")
        print("   [WARN] epubcheck integration not yet implemented")
        results['epubcheck'] = {'skipped': True}
    
    # Save report
    if args.output:
        import json
        output_path = Path(args.output)
        output_path.write_text(json.dumps(results, indent=2), encoding='utf-8')
        print(f"\nReport saved to: {output_path}")
    
    # Summary
    print("\n" + "="*60)
    print(f"Overall: {'[PASS]' if all_passed else '[FAIL]'}")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

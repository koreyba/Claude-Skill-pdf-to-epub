"""CLI for EPUB validation."""
import argparse
import sys
from pathlib import Path

from claude_skill.validation.completeness_checker import CompletenessChecker
from claude_skill.validation.order_checker import OrderChecker


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
    
    # Completeness check
    print("\n1. Checking text completeness...")
    try:
        checker = CompletenessChecker()
        result = checker.check(str(pdf_path), str(epub_path))
        
        print(f"   Completeness: {result.completeness_score:.2%}")
        print(f"   Status: {'✓ PASS' if result.is_complete else '✗ FAIL'}")
        
        results['completeness'] = {
            'score': result.completeness_score,
            'passed': result.is_complete
        }
        
        if not result.is_complete:
            all_passed = False
            if hasattr(result, 'missing_text'):
                print(f"   Missing: {len(result.missing_text)} segments")
                results['completeness']['missing_count'] = len(result.missing_text)
    except Exception as e:
        print(f"   ✗ Error: {e}")
        all_passed = False
        results['completeness'] = {'error': str(e)}
    
    # Order check
    print("\n2. Checking reading order...")
    try:
        checker = OrderChecker()
        result = checker.check(str(pdf_path), str(epub_path))
        
        print(f"   Correctness: {result.correctness_score:.2%}")
        print(f"   Status: {'✓ PASS' if result.is_correct else '✗ FAIL'}")
        
        results['order'] = {
            'score': result.correctness_score,
            'passed': result.is_correct
        }
        
        if not result.is_correct:
            all_passed = False
            if hasattr(result, 'out_of_order_count'):
                print(f"   Out of order: {result.out_of_order_count} segments")
                results['order']['errors'] = result.out_of_order_count
    except Exception as e:
        print(f"   ✗ Error: {e}")
        all_passed = False
        results['order'] = {'error': str(e)}
    
    # epubcheck (if requested)
    if args.epubcheck:
        print("\n3. Running epubcheck...")
        print("   ⚠️  epubcheck integration not yet implemented")
        results['epubcheck'] = {'skipped': True}
    
    # Save report
    if args.output:
        import json
        output_path = Path(args.output)
        output_path.write_text(json.dumps(results, indent=2), encoding='utf-8')
        print(f"\nReport saved to: {output_path}")
    
    # Summary
    print("\n" + "="*60)
    print(f"Overall: {'✓ PASS' if all_passed else '✗ FAIL'}")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

"""CLI for EPUB validation."""
import argparse
import sys
from pathlib import Path

from validation.validator import Validator


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

    print("\nRunning validation...")
    validator = Validator(pdf_path, epub_path)
    report = validator.validate(run_epubcheck=args.epubcheck)

    if report["status"] == "error":
        print(f"Error: {report['summary']}", file=sys.stderr)
        return 1

    completeness = report["details"].get("completeness", {})
    order = report["details"].get("order", {})

    print("\n1. Checking text completeness...")
    print(f"   Completeness: {completeness.get('score', 0.0):.1f}%")
    print(f"   Status: {'PASS' if completeness.get('passed') else 'FAIL'}")
    if completeness.get("missing_count"):
        print(f"   Missing: {completeness['missing_count']} segments")
        missing = completeness.get("missing", [])
        if missing:
            print("   Missing examples:")
            for i, item in enumerate(missing[:5], 1):
                snippet = item.get("snippet", "").strip()
                print(f"     {i}. {snippet}")
    approx = completeness.get("approximate", [])
    if approx:
        print(f"   Approximate matches: {len(approx)} segments")
        for i, item in enumerate(approx[:5], 1):
            snippet = item.get("snippet", "").strip()
            coverage = item.get("coverage")
            suffix = f" (coverage {coverage:.2%})" if coverage is not None else ""
            print(f"     {i}. {snippet}{suffix}")
    found = completeness.get("found")
    if found:
        print(f"   Found: {found.get('count', 0)} (exact: {found.get('exact', 0)}, fuzzy: {found.get('fuzzy', 0)})")

    print("\n2. Checking reading order...")
    print(f"   Order score: {order.get('score', 0.0):.1f}%")
    print(f"   Status: {'PASS' if order.get('passed') else 'FAIL'}")

    if args.epubcheck:
        print("\n3. Running epubcheck...")
        print("   [WARN] epubcheck integration not yet implemented")

    # Save report
    if args.output:
        import json
        output_path = Path(args.output)
        output_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(f"\nReport saved to: {output_path}")

    # Summary
    all_passed = report["status"] == "pass"
    print("\n" + "="*60)
    print(f"Overall: {'[PASS]' if all_passed else '[FAIL]'}")
    print("="*60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

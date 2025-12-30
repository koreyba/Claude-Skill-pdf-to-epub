"""CLI for EPUB validation."""
import argparse
import sys
from pathlib import Path


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
    
    # TODO: Implement validation
    # from claude_skill.validation.validator import Validator
    # validator = Validator(args.pdf_file, args.epub_file)
    # report = validator.validate()
    
    print(f"Validating {args.epub_file} against {args.pdf_file}...")
    print("⚠️  Validator not yet implemented (Phase 3 - partially done)")
    print("Current status:")
    print("  ✓ completeness_checker - implemented")
    print("  ✓ order_checker - implemented")
    print("  ✗ validator orchestrator - not implemented")
    print("\nThis will check:")
    print("  - Text completeness (shingles, anchors)")
    print("  - Reading order correctness")
    if args.epubcheck:
        print("  - EPUB format validity (epubcheck)")
    return 1


if __name__ == "__main__":
    sys.exit(main())

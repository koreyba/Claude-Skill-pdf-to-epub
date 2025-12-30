"""CLI for PDF to EPUB conversion."""
import argparse
import sys
from pathlib import Path


def main():
    """Convert PDF to EPUB."""
    parser = argparse.ArgumentParser(
        description="Convert PDF to EPUB with automatic validation"
    )
    parser.add_argument("pdf_file", help="Path to PDF file to convert")
    parser.add_argument(
        "-o", "--output",
        help="Output path for EPUB file (default: <pdf_name>.epub)"
    )
    parser.add_argument(
        "-c", "--config",
        help="Path to conversion config JSON file"
    )
    parser.add_argument(
        "-s", "--strategy",
        choices=["simple", "academic", "nonfiction"],
        default="simple",
        help="Conversion strategy (default: simple)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Run validation after conversion (default: True)"
    )
    parser.add_argument(
        "--no-validate",
        action="store_false",
        dest="validate",
        help="Skip validation"
    )
    
    args = parser.parse_args()
    
    # TODO: Implement conversion
    # from claude_skill.conversion.converter import Converter
    # converter = Converter(strategy=args.strategy)
    # result = converter.convert(args.pdf_file, args.output, config=args.config)
    
    print(f"Converting {args.pdf_file} to EPUB...")
    print(f"Strategy: {args.strategy}")
    print("⚠️  Converter not yet implemented (Phase 5)")
    print("This will:")
    print("  1. Extract text blocks from PDF")
    print("  2. Order blocks by reading order")
    print("  3. Detect structure (chapters, footnotes)")
    print("  4. Build EPUB file")
    if args.validate:
        print("  5. Validate result")
    return 1


if __name__ == "__main__":
    sys.exit(main())

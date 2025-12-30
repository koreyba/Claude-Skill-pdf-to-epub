"""CLI for PDF to EPUB conversion."""
import argparse
import sys
from pathlib import Path

from claude_skill.conversion.converter import Converter


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
        choices=["simple"],  # TODO: add "academic" when implemented
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
    
    # Convert paths
    pdf_path = Path(args.pdf_file)
    output_path = Path(args.output) if args.output else pdf_path.with_suffix('.epub')
    config_path = Path(args.config) if args.config else None
    
    # Validate input
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}", file=sys.stderr)
        return 1
    
    # Create converter
    print(f"Converting {pdf_path} to EPUB...")
    print(f"Strategy: {args.strategy}")
    
    try:
        converter = Converter(strategy=args.strategy)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    # Run conversion
    result = converter.convert(
        pdf_path=pdf_path,
        output_path=output_path,
        config_path=config_path
    )
    
    # Print results
    print(f"\n{'='*60}")
    print(f"Status: {result.status.upper()}")
    print(f"{'='*60}")
    
    if result.status in ["success", "warning"]:
        print(f"[OK] EPUB created: {result.epub_path}")
        print(f"[OK] Reading order confidence: {result.reading_order_confidence:.2%}")
    
    if result.log.warnings:
        print(f"\nWarnings:")
        for warning in result.log.warnings:
            print(f"  [!] {warning}")
    
    if result.log.errors:
        print(f"\nErrors:")
        for error in result.log.errors:
            print(f"  [X] {error}")
    
    # Validation
    if args.validate and result.status in ["success", "warning"]:
        print("\n" + "="*60)
        print("Running validation...")
        print("="*60)
        # TODO: Implement validation call
        print("[!] Validation not yet integrated")
    
    return 0 if result.status != "failed" else 1


if __name__ == "__main__":
    sys.exit(main())

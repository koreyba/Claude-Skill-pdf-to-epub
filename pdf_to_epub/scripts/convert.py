"""CLI for PDF to EPUB conversion."""
import argparse
import sys
from pathlib import Path

from conversion.converter import Converter
from conversion.report import ConversionReporter


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
    parser.add_argument(
        "--report",
        action="store_true",
        default=True,
        help="Generate detailed conversion report (default: True)"
    )
    parser.add_argument(
        "--no-report",
        action="store_false",
        dest="report",
        help="Skip detailed report"
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
    print(f"Converting {pdf_path.name} to EPUB...")
    print(f"Strategy: {args.strategy}")
    print()

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

    # Handle failure
    if result.status == "failed":
        print(f"\n{'='*60}")
        print("STATUS: FAILED")
        print(f"{'='*60}")
        for error in result.log.errors:
            print(f"  [X] {error}")
        return 1

    # Generate and print report
    if args.report:
        reporter = ConversionReporter()
        stats = reporter.generate_report(
            result, pdf_path, include_validation=args.validate
        )
        print(reporter.format_report(stats))
    else:
        # Brief output
        print(f"\n{'='*60}")
        print(f"STATUS: {result.status.upper()}")
        print(f"{'='*60}")
        print(f"EPUB created: {result.epub_path}")
        print(f"Reading order confidence: {result.reading_order_confidence:.2%}")

    # Print warnings
    if result.log.warnings:
        print("\nWarnings:")
        for warning in result.log.warnings:
            print(f"  [!] {warning}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

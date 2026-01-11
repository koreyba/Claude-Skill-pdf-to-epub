"""CLI for PDF structure analysis."""
import argparse
import sys
import json
from pathlib import Path

from conversion.pdf_analyzer import PDFAnalyzer


def main():
    """Analyze PDF structure without converting."""
    parser = argparse.ArgumentParser(
        description="Analyze PDF structure and output detailed report"
    )
    parser.add_argument("pdf_file", help="Path to PDF file to analyze")
    parser.add_argument(
        "-o", "--output",
        help="Output path for analysis JSON (default: stdout)"
    )
    parser.add_argument(
        "-c", "--config",
        help="Path to conversion config JSON file"
    )
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_file)
    config_path = Path(args.config) if args.config else None
    
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}", file=sys.stderr)
        return 1
    
    print(f"Analyzing {pdf_path}...")
    
    try:
        analyzer = PDFAnalyzer(pdf_path)
        analysis = analyzer.analyze()
        suggested_config = analyzer.generate_config()

        report = {
            "pdf_file": str(pdf_path),
            "analysis": analysis,
            "suggested_config": suggested_config,
        }

        if config_path:
            override = json.loads(Path(config_path).read_text(encoding="utf-8"))
            report["config_override"] = override
            report["effective_config"] = _deep_merge(suggested_config, override)

        output_json = json.dumps(report, indent=2)

        if args.output:
            Path(args.output).write_text(output_json, encoding="utf-8")
            print(f"Analysis saved to: {args.output}")
        else:
            print("\nAnalysis Result:")
            print(output_json)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def _deep_merge(base: dict, override: dict) -> dict:
    if not isinstance(override, dict):
        return override

    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


if __name__ == "__main__":
    sys.exit(main())



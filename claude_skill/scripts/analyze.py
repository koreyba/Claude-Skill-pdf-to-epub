"""CLI for PDF structure analysis."""
import argparse
import sys
import json
from pathlib import Path

from ..conversion.converter import Converter


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
        converter = Converter(strategy="simple")
        
        # Create temp EPUB to get structured content
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        result = converter.convert(
            pdf_path=pdf_path,
            output_path=tmp_path,
            config_path=config_path
        )
        
        # Build analysis report
        analysis = {
            "pdf_file": str(pdf_path),
            "status": result.status,
            "reading_order_confidence": result.reading_order_confidence,
            "metadata": {
                "title": result.metadata.title if result.metadata else None,
                "author": result.metadata.author if result.metadata else None,
                "language": result.metadata.language if result.metadata else None,
            },
            "chapter_count": len(result.structured_content.chapters) if result.structured_content else 0,
            "chapters": [
                {
                    "title": ch.title,
                    "level": ch.level,
                    "has_content": bool(ch.content_blocks)
                }
                for ch in (result.structured_content.chapters if result.structured_content else [])
            ],
            "image_count": len(result.structured_content.images) if result.structured_content else 0,
            "warnings": result.log.warnings,
            "errors": result.log.errors,
        }
        
        # Output
        output_json = json.dumps(analysis, indent=2)
        
        if args.output:
            Path(args.output).write_text(output_json, encoding='utf-8')
            print(f"✓ Analysis saved to: {args.output}")
        else:
            print("\nAnalysis Result:")
            print(output_json)
        
        # Cleanup temp file
        tmp_path.unlink(missing_ok=True)
        
        return 0 if result.status != "failed" else 1
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())


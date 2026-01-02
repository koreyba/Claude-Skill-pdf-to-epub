# PDF to EPUB Converter

A Claude Code skill for converting PDF books to high-quality EPUB format with automatic chapter detection, image optimization, and footnote hyperlinking.

## Features

- **Chapter Detection** — Automatically detects headings based on font analysis
- **Image Extraction & Optimization** — Extracts and compresses images for e-readers
- **Footnote/Endnote Hyperlinks** — Converts footnote references to clickable links
- **Reading Order Detection** — Handles single-column and multi-column layouts
- **Quality Validation** — Verifies text completeness and reading order preservation

## Installation

### As Claude Code Skill

The skill is located in the `pdf_to_epub/` folder. Copy it to your Claude skills directory:

```bash
# Personal skills (available in all projects)
cp -r pdf_to_epub ~/.claude/skills/pdf-to-epub

# Or project-specific
cp -r pdf_to_epub /path/to/project/.claude/skills/pdf-to-epub
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

## Quick Start

Once installed, Claude will automatically use this skill when you ask to convert PDFs:

> "Convert my-book.pdf to EPUB format"

Or run manually:

```bash
cd pdf_to_epub
python -m scripts.convert input.pdf output.epub
python -m scripts.validate input.pdf output.epub
```

## Workflow

The skill follows a 4-phase process:

1. **Analyze** — Examine PDF structure (columns, fonts, images)
2. **Convert** — Apply configuration and build EPUB
3. **Validate** — Check text completeness and reading order
4. **Adapt** — Tune configuration if validation fails

## Configuration Examples

### Fiction Book (single column)

```json
{
  "page_ranges": {"skip": [1, 2], "content": [3, -3]},
  "reading_order_strategy": "y_sort",
  "heading_detection": {"font_size_threshold": 1.2}
}
```

### Academic Paper (multi-column)

```json
{
  "reading_order_strategy": "xy_cut",
  "multi_column": {"enabled": true, "threshold": 0.4}
}
```

More examples in [pdf_to_epub/examples/](pdf_to_epub/examples/).

## Project Structure

```
.
├── pdf_to_epub/              # Claude Skill (copy this folder)
│   ├── SKILL.md              # Skill definition
│   ├── requirements.txt      # Python dependencies
│   ├── core/                 # Core algorithms (FROZEN)
│   ├── conversion/           # Conversion logic
│   ├── validation/           # Quality checking
│   ├── scripts/              # CLI entry points
│   ├── reference/            # Documentation
│   └── examples/             # Example configurations
│
├── tests/                    # Test suite
├── docs/                     # Development documentation
└── requirements.txt          # All dependencies (including dev)
```

## Documentation

- [Workflow Guide](pdf_to_epub/reference/workflow.md) — Complete conversion process
- [Architecture](pdf_to_epub/reference/architecture.md) — Three-layer system design
- [Configuration](pdf_to_epub/reference/config-tuning.md) — All parameters explained
- [Troubleshooting](pdf_to_epub/reference/troubleshooting.md) — Common issues and fixes
- [Code Adaptation](pdf_to_epub/reference/code-adaptation.md) — When and how to modify code

## Quality Metrics

After conversion, the skill validates:

| Metric | Good | Warning | Bad |
|--------|------|---------|-----|
| Text completeness | > 98% | 95-98% | < 95% |
| Reading order | > 90% | 80-90% | < 80% |

## Development

### Running Tests

```bash
python -m pytest tests/ -v
```

### Requirements

- Python 3.10+
- pymupdf, pdfplumber, lxml, beautifulsoup4, Pillow, ebooklib

## License

MIT License — see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please note the architecture:

- **FROZEN** files (core/, validation/) — Do not modify
- **CONFIGURABLE** — Try configuration changes first
- **ADAPTABLE** files (strategies/, detectors/) — Can be extended

## Related

- [Claude Code Skills Documentation](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/skills)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)

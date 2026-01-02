# PDF to EPUB Converter

A Claude Code skill for converting PDF books to high-quality EPUB format with automatic chapter detection, image optimization, and footnote hyperlinking.

## Features

- **Chapter Detection** — Automatically detects headings based on font analysis
- **Image Extraction & Optimization** — Extracts and compresses images for e-readers
- **Footnote/Endnote Hyperlinks** — Converts footnote references to clickable links
- **Reading Order Detection** — Handles single-column and multi-column layouts
- **Quality Validation** — Verifies text completeness and reading order preservation

## Installation

### For Claude Code CLI

Copy the skill folder to your Claude skills directory:

```bash
# Personal skills (available in all projects)
cp -r . ~/.claude/skills/pdf-to-epub

# Or project-specific (available only in that project)
cp -r . /path/to/project/.claude/skills/pdf-to-epub
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

## Quick Start

Once installed, Claude will automatically use this skill when you ask to convert PDFs to EPUB:

> "Convert my-book.pdf to EPUB format"

Or manually invoke the conversion:

```bash
# From skill directory
python -m scripts.convert input.pdf output.epub

# Validate the result
python -m scripts.validate input.pdf output.epub
```

## Workflow

The skill follows a 4-phase process:

1. **Analyze** — Examine PDF structure (columns, fonts, images)
2. **Convert** — Apply configuration and build EPUB
3. **Validate** — Check text completeness and reading order
4. **Adapt** — Tune configuration if validation fails

See [reference/workflow.md](reference/workflow.md) for details.

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

More examples in [examples/](examples/).

## Project Structure

```
.
├── SKILL.md              # Claude skill definition
├── requirements.txt      # Python dependencies
├── core/                 # Core algorithms (FROZEN)
├── conversion/           # Conversion logic
│   ├── strategies/       # Conversion strategies (ADAPTABLE)
│   └── detectors/        # Structure detection (ADAPTABLE)
├── validation/           # Quality checking (FROZEN)
├── scripts/              # CLI entry points
├── reference/            # Documentation
└── examples/             # Example configurations
```

## Documentation

- [Workflow Guide](reference/workflow.md) — Complete conversion process
- [Architecture](reference/architecture.md) — Three-layer system design
- [Configuration](reference/config-tuning.md) — All parameters explained
- [Troubleshooting](reference/troubleshooting.md) — Common issues and fixes
- [Code Adaptation](reference/code-adaptation.md) — When and how to modify code

## Quality Metrics

After conversion, the skill validates:

| Metric | Good | Warning | Bad |
|--------|------|---------|-----|
| Text completeness | > 98% | 95-98% | < 95% |
| Reading order | > 90% | 80-90% | < 80% |

## Requirements

- Python 3.10+
- Dependencies: pymupdf, pdfplumber, lxml, beautifulsoup4, Pillow, ebooklib

## License

MIT License — see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read the architecture documentation before modifying code:

- **FROZEN** files (core/, validation/) — Do not modify
- **CONFIGURABLE** — Try configuration changes first
- **ADAPTABLE** files (strategies/, detectors/) — Can be extended

## Related

- [Claude Code Skills Documentation](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/skills)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)

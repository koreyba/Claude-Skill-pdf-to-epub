# Debug Scripts

Development and debugging utilities for PDF to EPUB converter.

## Overview

These scripts are development tools for testing and debugging individual components. They are **not part of the production skill** - use scripts in `scripts/` for actual conversion.

## Available Scripts

### `analyze_missing.py`
Analyzes missing text between PDF and EPUB using CompletenessChecker.

**Usage:**
```bash
python debug/analyze_missing.py
```

Generates detailed report in `missing_report.txt` showing:
- Missing text chunks
- Anchor analysis
- Shingles statistics

---

### `debug_completeness.py`
Debug and test the completeness checker component.

**Usage:**
```bash
python debug/debug_completeness.py
```

Tests:
- Shingle-based recall calculation
- Anchor detection (numbers, dates, URLs)
- Rare word preservation

---

### `debug_order.py`
Debug and test the order checker component.

**Usage:**
```bash
python debug/debug_order.py
```

Tests:
- LIS (Longest Increasing Subsequence) algorithm
- Chunk ordering detection
- Misplaced content identification

---

### `debug_structure.py`
Debug PDF structure analysis pipeline.

**Usage:**
```bash
python debug/debug_structure.py
```

Tests end-to-end structure detection:
1. Extract text blocks from PDF
2. Sort blocks (Y-sorter)
3. Analyze fonts
4. Classify structure (H1, H2, body, footnotes)
5. Build chapter tree

---

### `probe_files.py`
Explore PDF and EPUB file structure.

**Usage:**
```bash
python debug/probe_files.py
```

Utility for inspecting:
- PDF metadata
- EPUB spine structure
- Text extraction results

---

### `verify_checker_sensitivity.py`
Verify sensitivity and accuracy of validation checkers.

**Usage:**
```bash
python debug/verify_checker_sensitivity.py
```

Tests validation thresholds:
- False positive rates
- False negative rates
- Optimal threshold values

---

## Development Workflow

1. **Test individual components** with debug scripts
2. **Validate changes** don't break existing functionality
3. **Profile performance** for large files
4. **Document findings** in implementation docs

## Notes

- All scripts use fixtures from `tests/fixtures/`
- Hard-coded paths point to `c:/Projects/Pdf-to-epub-skill`
- Update paths if working in different environment
- These are temporary utilities - may be removed or refactored

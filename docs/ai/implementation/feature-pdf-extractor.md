---
phase: implementation
title: Implementation - PDF Extractor
description: Technical implementation notes for PDF extraction.
---

# Implementation Guide

## Code Structure
**How is the code organized?**

- `pdf_to_epub/core/pdf_extractor.py`

## Implementation Notes
**Key technical details to remember:**

### PyMuPDF Usage
```python
import fitz
doc = fitz.open(path)
for page in doc:
    text = page.get_text("text", sort=True)
```
Setting `sort=True` is vital for correct reading order.

### Paragraph Joining
PDF text often has extra newlines. We should join lines that end without "sentence-ending" punctuation or lines that look like parts of the same flow.

## Error Handling
**How do we handle failures?**

- Catch `fitz.FileDataError` for corrupted files.
- Catch `RuntimeError` for encrypted files without password.

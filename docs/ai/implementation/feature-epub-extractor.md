---
phase: implementation
title: Implementation - EPUB Extractor
description: Technical implementation notes for EPUB extraction.
---

# Implementation Guide

## Code Structure
**How is the code organized?**

- `pdf_to_epub/core/epub_extractor.py`

## Implementation Notes
**Key technical details to remember:**

### EbookLib Snippet
```python
import ebooklib
from ebooklib import epub

book = epub.read_epub(path)
for item in book.get_items():
    if item.get_type() == ebooklib.ITEM_DOCUMENT:
        # process html
```

### BeautifulSoup Cleaning
Use `soup.get_text(separator=' ', strip=True)` to ensure words don't stick together after tag removal.

## Error Handling
**How do we handle failures?**

- Catch errors if the file is not a valid ZIP or missing `mimetype`.

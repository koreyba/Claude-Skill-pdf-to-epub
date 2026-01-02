---
phase: implementation
title: Implementation - Text Canonicalizer
description: Technical implementation notes for text normalization.
---

# Implementation Guide

## Code Structure
**How is the code organized?**

- `pdf_to_epub/validation/text_canonicalizer.py`

## Implementation Notes
**Key technical details to remember:**

### Unicode
Use python's `unicodedata` module.

### Ligatures Mapping
Include at least:
- `ﬁ` -> `fi`
- `ﬂ` -> `fl`
- `ﬀ` -> `ff`
- `ﬃ` -> `ffi`
- `ﬄ` -> `ffl`
- `æ` -> `ae`
- `œ` -> `oe`

### Hyphenation Regex
`r"-\s*\n\s*"` should be replaced with `""` (empty string) to join words.

## Error Handling
**How do we handle failures?**

- Ensure it handles `None` input.
- Log instances where aggressive mode makes "destructive" changes if possible.

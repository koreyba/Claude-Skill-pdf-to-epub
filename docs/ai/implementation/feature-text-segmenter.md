---
phase: implementation
title: Implementation - Text Segmenter
description: Technical implementation notes for text segmentation.
---

# Implementation Guide

## Code Structure
**How is the code organized?**

- `pdf_to_epub/core/text_segmenter.py`

## Implementation Notes
**Key technical details to remember:**

### Sliding Window Formula
For a text of length `L`, `chunk_size` `S`, and `overlap` `O`:
- Chunk 1: `[0 : S]`
- Chunk 2: `[S - O : (S - O) + S]`
- ...and so on until the end of the string.

### Metadata
Ensure `end_index` is exclusive (standard Python slicing).

## Error Handling
**How do we handle failures?**

- Raise `ValueError` if `overlap >= chunk_size`.
- Handle `None` or empty string gracefully.

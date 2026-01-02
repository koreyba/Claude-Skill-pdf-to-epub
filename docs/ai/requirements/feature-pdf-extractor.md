---
phase: requirements
title: Requirements - PDF Extractor
description: Define requirements for high-quality text extraction from PDF files.
---

# Requirements & Problem Understanding

## Problem Statement
**What problem are we solving?**

- PDF files are fixed-layout documents where text is often stored as individual characters or lines with coordinates rather than semantic paragraphs.
- Extracting text in the correct reading order is difficult for multi-column or complex layouts.
- We need a reliable way to extract text that closely matches how a human would read it, to enable fair comparison with EPUB.

## Goals & Objectives
**What do we want to achieve?**

- **High Accuracy:** Correct reading order for standard book layouts.
- **Paragraph Preservation:** Attempt to reconstruct paragraphs rather than returning a list of disconnected lines.
- **Canonical Integration:** Every piece of extracted text must be piped through `text_canonicalizer`.
- **Resource Efficiency:** Handle large PDF books without memory exhaustion.

## User Stories & Use Cases
**How will users interact with the solution?**

- As a validator, I want to get the "clean" text of a PDF file to compare it with EPUB chunks.
- As a developer, I want to know if extraction failed due to encryption or corrupted file structure.
- As a system, I want to handle PDF files with bookmarks and TOC (optional/future).

## Success Criteria
**How will we know when we're done?**

- `pdf_to_epub/core/pdf_extractor.py` is implemented using `PyMuPDF` (fitz).
- Successfully extracts text from test PDF files.
- Text is normalized and cleaned automatically.
- Errors (missing file, encrypted PDF without password) are handled gracefully.
- Image-only PDFs (no text layer) return an empty string or trigger a warning without crashing.

## Constraints & Assumptions
**What limitations do we need to work within?**

- We assume the PDF has a text layer (not purely scanned images without OCR).
- Encrypted PDFs are considered out of scope for auto-decryption in v1.
- We use `PyMuPDF` as the primary engine.

## Questions & Open Items
**What do we still need to clarify?**

- Should we handle multi-column layouts explicitly? (Decision: Use PyMuPDF's built-in heuristic/sorting first).
- Do we need images? (Decision: No, text-only for now).

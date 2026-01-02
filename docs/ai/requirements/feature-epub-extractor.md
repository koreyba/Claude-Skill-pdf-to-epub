---
phase: requirements
title: Requirements - EPUB Extractor
description: Define requirements for extracting clean text from EPUB files for validation.
---

# Requirements & Problem Understanding

## Problem Statement
**What problem are we solving?**

- EPUB files are ZIP archives containing multiple XHTML files, images, and metadata.
- To validate conversion quality, we need a single stream of text that represents the book's content.
- We must remove all markup (HTML tags) and technical noise without losing the actual content or changing its order.

## Goals & Objectives
**What do we want to achieve?**

- **Markup Stripping:** Efficiently remove all HTML tags, leaving only human-readable text.
- **Chapter Ordering:** Extract text from chapters in the correct sequence as defined by the EPUB spine.
- **Canonicalization:** Mandatory integration with `text_canonicalizer`.
- **Metadata extraction:** Extract basic info like Title and Creator.

## User Stories & Use Cases
**How will users interact with the solution?**

- As a validator, I want to get the full book text from an EPUB to check for missing segments.
- As a developer, I want to handle EPUB 2 and EPUB 3 formats consistently.
- As a system, I want to ignore non-content files (CSS, images, font files) automatically.

## Success Criteria
**How will we know when we're done?**

- `pdf_to_epub/core/epub_extractor.py` is implemented using `ebooklib` and `BeautifulSoup4`.
- Text is extracted in the correct reading order.
- No HTML tags remain in the output.
- All extracted text is canonicalized.

## Constraints & Assumptions
**What limitations do we need to work within?**

- We assume the EPUB is not DRM-protected (encrypted).
- We use `ebooklib` as the primary parsing engine.

## Questions & Open Items
**What do we still need to clarify?**

- How to handle footnotes that might appear mid-text in the XHTML? (Decision: For v1, extract them as they appear in the flow. This remains a known limitation for comparison accuracy).
- How to handle images? (Decision: Images and their alt-texts are ignored in v1 to focus on pure text body).

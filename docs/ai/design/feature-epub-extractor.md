---
phase: design
title: System Design - EPUB Extractor
description: Technical design for the EPUB extraction module.
---

# System Design & Architecture

## Architecture Overview
**What is the high-level system structure?**

The `epub_extractor` mirrors the `pdf_extractor` in interface, providing a unified way to get "clean" text from a book file.

```mermaid
graph LR
    EPUB[EPUB File] --> EbookLib[EbookLib]
    EbookLib --> BeautifulSoup[BeautifulSoup4]
    BeautifulSoup --> Extractor[epub_extractor.py]
    Extractor --> Canonicalizer[text_canonicalizer.py]
    Canonicalizer --> Output[Clean Text]
```

## Data Models
**What data do we need to manage?**

- **EPUBContent:** The resulting string of clean text.
- **Metadata:** Dictionary containing title, author, and publisher.

## API Design
**How do components communicate?**

### Primary Interface
- `class EPUBExtractor`:
    - `__init__(file_path: Path)`
    - `get_full_text() -> str`
    - `iter_chapters() -> Iterator[str]` (Yields cleaned text per chapter)
    - `get_metadata() -> dict`

## Component Breakdown
**What are the major building blocks?**

- **EPUB Reader:** Wrapper around `ebooklib` to navigate the spine. Must explicitly filter for `ITEM_DOCUMENT` to avoid binary files.
- **HTML Purifier:** Uses `BeautifulSoup` with `get_text(separator=' ', strip=True)` to ensure words don't stick together after tag removal.
- **Bridge to Canonicalizer:** Pipe every chapter through the `canonicalize` function.

## Design Decisions
**Why did we choose this approach?**

- **EbookLib:** The most robust library for handling EPUB spine and manifest.
- **BeautifulSoup4:** Superior to regex for HTML stripping, handles malformed markup gracefully.
- **Character-based comparison:** By canonicalizing both PDF and EPUB to the same string format, we can use the same `CompletenessChecker`.

## Non-Functional Requirements
**How should the system perform?**

- **Robustness:** Gracefully handle missing manifest items or malformed XHTML.
- **Memory:** Process chapters as an iterator to avoid loading huge books entirely into memory if needed.

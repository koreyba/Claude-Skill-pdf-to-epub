---
phase: requirements
title: Requirements - Text Canonicalizer
description: Define requirements for text normalization to ensure consistent comparison between PDF and EPUB.
---

# Requirements & Problem Understanding

## Problem Statement
**What problem are we solving?**

- PDF and EPUB files often represent the same text using different character sequences (e.g., ligatures like "ﬁ" instead of "fi").
- Text extraction from PDF often includes soft hyphens or end-of-line hyphens ("word- \n wrap") that break word comparison.
- To perform accurate validation (completeness and order checks), we need a "canonical" version of the text that is identical regardless of the source file's quirks.

## Goals & Objectives
**What do we want to achieve?**

- **Unicode Normalization:** Use NFKC to unify character representations.
- **Ligature Resolution:** Decompose ligatures (e.g., "ﬂ" -> "fl", "æ" -> "ae").
- **Hyphenation Cleanup:** Remove end-of-line hyphens and unify various hyphen characters.
- **Whitespace Handling:** While `text_segmenter` handles basic whitespace, the canonicalizer should ensure consistent encoding.
- **Idempotency:** Running the canonicalizer multiple times should not change the output after the first run.

## User Stories & Use Cases
**How will users interact with the solution?**

- As a developer, I want to pass "extact-from-pdf" text and get "clean-compare-ready" text.
- As a validator, I want to be sure that `canonicalize(pdf_text) == canonicalize(epub_text)` if the words are the same.
- As a system, I want two modes: `conservative` (safe) and `aggressive` (for heavy OCR/PDF artifacts).

## Success Criteria
**How will we know when we're done?**

- `pdf_to_epub/validation/text_canonicalizer.py` is implemented.
- Ligatures are correctly expanded.
- End-of-line hyphens are removed.
- 100% test coverage including complex Unicode edge cases.

## Constraints & Assumptions
**What limitations do we need to work within?**

- Must be fast enough for large texts.
- Should not remove meaningful punctuation (unless specified in aggressive mode).
- Assumption: Input is UTF-8 encoded string.

## Questions & Open Items
**What do we still need to clarify?**

- Do we need to handle specific OCR artifacts like "rn" instead of "m"? (Decision: Keep it for 'aggressive' mode only).
- Should we lowercase by default? (Decision: No, let the specific checker decide on case-sensitivity).

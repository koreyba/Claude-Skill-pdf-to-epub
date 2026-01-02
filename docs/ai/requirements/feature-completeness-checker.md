---
phase: requirements
title: Requirements - Completeness Checker
description: Define requirements for verifying text completeness between PDF and EPUB.
---

# Requirements & Problem Understanding

## Problem Statement
**What problem are we solving?**

- During PDF to EPUB conversion, content can be lost due to parsing errors, hidden layers in PDF, or bugs in the conversion software.
- Manual checking is error-prone and slow.
- We need an automated way to say: "Every word from PDF is definitely in the EPUB."

## Goals & Objectives
**What do we want to achieve?**

- **High Precision:** Detect missing segments as small as a few sentences.
- **Robustness:** Use sliding window chunks to ensure overlap and avoid boundary misses.
- **Actionable Reports:** List specific missing chunks with their original PDF indices.
- **Speed:** Efficiently search for thousands of chunks in a large text body.

## User Stories & Use Cases
**How will users interact with the solution?**

- As a developer, I want a list of `ValidationFailure` objects if segments are missing.
- As a QA, I want a percentage score of completeness.
- As a system, I want the checker to use `text_segmenter` for input and `text_canonicalizer` for pre-processing.

## Success Criteria
**How will we know when we're done?**

- `pdf_to_epub/validation/completeness_checker.py` is implemented.
- The checker ignores "noise" (chunks shorter than a configurable threshold, e.g., 20 chars) to avoid false alerts on page numbers.
- The checker successfully finds 100% of significant chunks in an identical text.
- The checker identifies specific missing text and provides its context from PDF.

## Constraints & Assumptions
**What limitations do we need to work within?**

- We assume both texts are already canonicalized.
- We focus on text only (not images or formatting).
- Memory constraint: Should handle books up to 5MB of raw text efficiently.

## Questions & Open Items
**What do we still need to clarify?**

- **Noise Handling:** Page numbers and short headers/footers in PDF that are removed in EPUB will be flagged as "low-confidence" or ignored if they are shorter than `MIN_SIGNIFICANT_LEN`.
- **Thresholds:** Validation score will distinguish between "Missing Content" and "Minor Differences".

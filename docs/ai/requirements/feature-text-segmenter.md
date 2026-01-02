---
phase: requirements
title: Requirements - Text Segmenter
description: Define the requirements for the deterministic text segmentation module.
---

# Requirements & Problem Understanding

## Problem Statement
**What problem are we solving?**

- Validating PDF to EPUB conversion requires comparing the text content of both files.
- Directly comparing long strings is brittle due to minor formatting differences, OCR artifacts, or layout-induced reordering.
- We need a way to break down long text into manageable, reproducible "chunks" to calculate metrics like text recall and reading order score.

## Goals & Objectives
**What do we want to achieve?**

- **Deterministic Segmentation:** Given the same input text, the output chunks must always be the same.
- **Support for Overlap:** Chunks should overlap to ensure that tokens/words potentially split at a boundary are fully present in at least one (or both) adjacent chunks.
- **Metadata preservation:** Each chunk must know its relative position in the original text.
- **Normalization:** Minimize noise by normalizing whitespace before segmentation.

## User Stories & Use Cases
**How will users interact with the solution?**

- As a developer, I want to call a `segment_text` function with a string and get a list of segments.
- As a validator, I want the segments to be represented as objects containing the text and index metadata.
- As a system, I want to use standard constants for chunk size (600) and overlap (100).

## Success Criteria
**How will we know when we're done?**

- `pdf_to_epub/core/text_segmenter.py` is implemented.
- The segmentation logic handles strings shorter than the chunk size correctly.
- Overlap logic correctly recalculates the start position of subsequent chunks.
- 100% test coverage with 0 bugs in boundary conditions.

## Constraints & Assumptions
**What limitations do we need to work within?**

- Must be extremely performant as it will process entire books.
- Must use the constants defined in `core/utils.py`.
- Assumption: The input text is already canonicalized (normalized Unicode, etc.) by a previous step, but basic whitespace normalization should happen here too.

## Questions & Open Items
**What do we still need to clarify?**

- Should we segment by characters or tokens (words)? (Decision: Character-based for simplicity and predictability in Level 0).
- How to handle very small overlaps vs large ones?

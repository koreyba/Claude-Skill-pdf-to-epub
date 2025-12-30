---
phase: testing
title: Testing Strategy - PDF Extractor
description: Testing approach for the PDF extraction module.
---

# Testing Strategy

## Test Coverage Goals
**What level of testing do we aim for?**

- 90%+ coverage. Difficult to hit 100% without real complex PDFs, but we will mock the Fitz library for core logic.

## Unit Tests
**What individual components need testing?**

### Metadata Extraction
- [ ] Handles empty metadata.
- [ ] Correctly reads Title/Author.

### Text Extraction
- [ ] Verifies `canonicalize` is called for each page.
- [ ] Verifies pages are joined with proper spacing.

## Manual Verification
- [ ] Run extractor on a few known PDF books and check the first 1000 characters.

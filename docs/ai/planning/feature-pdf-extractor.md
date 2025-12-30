---
phase: planning
title: Planning - PDF Extractor
description: Task breakdown for PDF extraction module.
---

# Project Planning & Task Breakdown

## Milestones
**What are the major checkpoints?**

- [ ] Milestone 1: Library integration and basic extraction.
- [ ] Milestone 2: Paragraph reconstruction and canonicalization.
- [ ] Milestone 3: Unit tests with mock/sample PDFs.

## Task Breakdown
**What specific work needs to be done?**

### Phase 1: Foundation
- [ ] Task 1.1: Install `pymupdf` in `.venv`. (Done)
- [ ] Task 1.2: Implement `PDFExtractor` class skeleton with resource management (context manager).
- [ ] Task 1.3: Implement text extraction using `page.get_text("blocks")`.
- [ ] Task 1.4: Add `iter_pages` for memory-efficient processing.

### Phase 2: Refinement
- [ ] Task 2.1: Implement smart block joining logic for paragraphs.
- [ ] Task 2.2: Integrate `canonicalize` from `validation.text_canonicalizer`.
- [ ] Task 2.3: Extract metadata and handle encryption/corruption errors.

### Phase 3: Testing
- [ ] Task 3.1: Write unit tests. Note: we might need a small sample PDF or use mocks for fitz objects.

## Dependencies
**What needs to happen in what order?**

- Depends on `PyMuPDF` library.
- Depends on `text_canonicalizer` (Completed).

## Timeline & Estimates
**When will things be done?**

- Tasks 1.1-1.3: 1 hour.
- Tasks 2.1-2.3: 2 hours.
- Testing: 1.5 hours.

## Risks & Mitigation
**What could go wrong?**

- **Risk:** Poor reading order in multi-column PDFs.
- **Mitigation:** Use `page.get_text("blocks")` to respect layout blocks.

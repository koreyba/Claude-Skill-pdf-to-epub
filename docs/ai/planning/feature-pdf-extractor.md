---
phase: completed
title: Planning - PDF Extractor
description: Task breakdown for PDF extraction module.
---

# Project Planning & Task Breakdown

## Milestones
**What are the major checkpoints?**

- [x] Milestone 1: Library integration and basic extraction (Done).
- [x] Milestone 2: Paragraph reconstruction and canonicalization (Done).
- [x] Milestone 3: Unit tests and integration with real fixtures (Done).
- [x] Milestone 4: Smart Noise Removal (Headers/Footers) (Done).

## Task Breakdown
**What specific work needs to be done?**

### Phase 1: Foundation
- [x] Task 1.1: Install `pymupdf` in `.venv`. (Done)
- [x] Task 1.2: Implement `PDFExtractor` class skeleton with resource management (context manager).
- [x] Task 1.3: Implement text extraction using `page.get_text("blocks")`.
- [x] Task 1.4: Add `iter_pages` for memory-efficient processing.

### Phase 2: Refinement
- [x] Task 2.1: Implement smart block joining logic for paragraphs.
- [x] Task 2.2: Integrate `canonicalize` from `validation.text_canonicalizer`.
- [x] Task 2.3: Extract metadata and handle encryption/corruption errors.

### Phase 3: Advanced Extraction (Added during Phase 3 Validation)
- [x] Task 3.1: Implement `_identify_noise_patterns` using statistical analysis of repeated lines.
- [x] Task 3.2: Implement regex-based stripping of page numbers and copyrights.
- [x] Task 3.3: Strip noise patterns from within text blocks to handle embedded artifacts.

### Phase 4: Testing
- [x] Task 4.1: Unit tests for basic extraction logic.
- [x] Task 4.2: Integration test showing 100% text recovery after noise removal.

## Timeline & Estimates
- Completed 2025-12-30.

## Risks & Mitigation
- **Risk:** Poor reading order in multi-column PDFs.
- **Mitigation:** Used `page.get_text("blocks", sort=True)` to respect layout blocks.
- **Risk:** Recurrent noise (headers/footers) breaking validation.
- **Mitigation:** Implemented heuristic-based identification and removal of recurring lines.

---
phase: planning
title: Planning - EPUB Extractor
description: Task breakdown for EPUB extraction module.
---

# Project Planning & Task Breakdown

## Milestones
**What are the major checkpoints?**

- [ ] Milestone 1: Library integration and basic EPUB reading.
- [ ] Milestone 2: HTML cleaning and canonicalization.
- [ ] Milestone 3: Unit tests and integration with a real EPUB.

## Task Breakdown
**What specific work needs to be done?**

### Phase 1: Foundation
- [x] Task 1.1: Install `ebooklib` and `beautifulsoup4` in `.venv`.
- [x] Task 1.2: Implement `EPUBExtractor` skeleton with `fitz`-like context manager.
- [x] Task 1.3: Implement chapter iteration (filtering for `ITEM_DOCUMENT` only).

### Phase 2: Refinement
- [x] Task 2.1: Implement `_clean_html` using BeautifulSoup with proper spacing.
- [x] Task 2.2: Integrate `canonicalize` for each chapter.
- [x] Task 2.3: Extract metadata (Title, Creator) with fallback for missing fields.

### Phase 3: Testing
- [ ] Task 3.1: Write unit tests (mocks for ebooklib).
- [ ] Task 3.2: Integration test with a real EPUB file in `tests/fixtures`.

## Dependencies
**What needs to happen in what order?**

- Depends on `text_canonicalizer` (Completed).
- Requires an EPUB file for testing.

## Timeline & Estimates
**When will things be done?**

- Implementation: 2 hours.
- Testing: 1.5 hours.

## Risks & Mitigation
**What could go wrong?**

- **Risk:** Variations in EPUB structure (non-standard internal paths).
- **Mitigation:** Rely on EbookLib's internal manifest mapping.

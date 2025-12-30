---
phase: planning
title: Planning - Text Canonicalizer
description: Task breakdown for implementing the text canonicalizer.
---

# Project Planning & Task Breakdown

## Milestones
**What are the major checkpoints?**

- [x] Milestone 1: Basic Unicode and ligature resolution.
- [x] Milestone 2: Hyphenation cleanup and aggressive mode.
- [x] Milestone 3: Full test coverage.

## Task Breakdown
**What specific work needs to be done?**

### Phase 1: Foundation
- [ ] Task 1.1: Implement `resolve_ligatures` with a mapping of common PDF ligatures.
- [ ] Task 1.2: Implement `remove_hyphenation` (handling `-\n` scenarios).
- [ ] Task 1.3: Wrap them into a main `canonicalize` function using `unicodedata.nfkc`.

### Phase 2: Refinement
- [ ] Task 2.1: Add "aggressive" mode for OCR artifacts (optional common fixes).
- [ ] Task 2.2: Character-level logging for debugging canonicalization gaps.

### Phase 3: Testing
- [ ] Task 3.1: Write unit tests covering:
    - [ ] Unicode normalization (different forms).
    - [ ] Ligatures (ff, fi, fl, ffi, ffl, ae, oe).
    - [ ] Hyphenation across lines.
    - [ ] Combination of all effects.

## Dependencies
**What needs to happen in what order?**

- Safe to build in parallel with `text_segmenter`, but `segmenter` will eventually receive canonicalized text.

## Timeline & Estimates
**When will things be done?**

- Implementation: 1.5 hours
- Testing: 1 hour

## Risks & Mitigation
**What could go wrong?**

- **Risk:** Removing a hyphen that was actually part of a word (e.g. "semi-detached").
- **Mitigation:** Only remove hyphens followed by whitespace/newlines.

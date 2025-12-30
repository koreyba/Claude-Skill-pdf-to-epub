---
phase: testing
title: Testing Strategy - Text Canonicalizer
description: Testing approach for the text normalization module.
---

# Testing Strategy

## Test Coverage Goals
**What level of testing do we aim for?**

- 100% coverage.

## Unit Tests
**What individual components need testing?**

### resolve_ligatures
- [ ] Test multiple ligatures in one string.
- [ ] Test non-ligature text remains unchanged.

### remove_hyphenation
- [ ] Test word split across lines: `biblio-\nteca` -> `biblioteca`.
- [ ] Test that regular hyphens `word-word` are NOT removed.

### Full canonicalize
- [ ] Test normalization of Unicode (combined characters).
- [ ] Test end-to-end flow with all features enabled.

## Test Reporting & Coverage
**How do we verify and communicate test results?**

- `npm test`

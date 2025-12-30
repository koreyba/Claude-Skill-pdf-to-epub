---
phase: testing
title: Testing Strategy - EPUB Extractor
description: Testing approach for the EPUB extraction module.
---

# Testing Strategy

## Test Coverage Goals
**What level of testing do we aim for?**

- 90%+.

## Unit Tests
**What individual components need testing?**

### HTML Cleaning
- [ ] Test with nested tags.
- [ ] Test with `<script>` and `<style>` blocks (should be ignored).
- [ ] Test spacing between elements (e.g. `<div>A</div><div>B` should be `A B`, not `AB`).

### Spine Ordering
- [ ] Verify that items are returned in the order specified by the book spine.

## Manual Verification
- [ ] Compare EPUB extraction against a known text source to ensure no content loss.

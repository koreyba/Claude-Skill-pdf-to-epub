---
title: Testing - Structure Analyzer
description: Test strategy for structure detection.
---

# Test Plan

## Unit Tests
- `test_ysort`: Ensure blocks are sorted top-down.
- `test_heading_detection`: Feed mock blocks with different font sizes, verify H1/H2 classification.
- `test_toc_generation`: Verify tree structure building.

## Integration Tests
- **Fixture:** `simple_chapter.pdf` (Clear headers).
- **Assertion:** ToC contains "Chapter 1", "Chapter 2".
- **Fixture:** `footnote_page.pdf`.
- **Assertion:** Link exists from `[1]` to bottom text.

## Edge Cases
- **No Headers:** Book is one giant chapter?
- **All Bold:** If entire book is bold, no headers detected.
- **Floating Images:** Interrupted text flow.

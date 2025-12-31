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
- **Fixture:** `Excerpt C The Ways We Are in This Together.pdf`.
- **Assertion:** "Excerpt C..." and "Part I..." are H1; "Important" is H2; "Overview" is H3; specific body sentences are not headings.

## Edge Cases
- **No Headers:** Book is one giant chapter?
- **All Bold:** If entire book is bold, no headers detected.
- **Floating Images:** Interrupted text flow.

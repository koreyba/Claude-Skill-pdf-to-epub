---
phase: planning
title: Planning - Structure Analyzer
description: Task breakdown for implementing structure detection.
---

# Project Planning & Task Breakdown

## Milestones
**What are the major checkpoints?**

- [ ] Milestone 1: Reading Order Logic (Sorting)
- [ ] Milestone 2: Heading Detection & ToC
- [ ] Milestone 3: Footnote Processing
- [ ] Milestone 4: Integration with Converter

## Task Breakdown
**What specific work needs to be done?**

### Phase 1: Reading Order
- [x] Task 1.1: Implement `YSorter` (simple).
- [x] Task 1.2: Implement `XYCutSorter` (advanced/multi-column).
- [x] Task 1.3: Column detector (auto-select strategy). (Deferred: Manual selection used for now)

### Phase 2: Headings & Structure
- [x] Task 2.1: Implement `FontAnalyzer` (identify dominant styles).
- [x] Task 2.2: Implement `HeadingDetector` (classify H1-H3). (Implemented as `StructureClassifier` with heuristic scoring).
- [x] Task 2.3: Implement `StructureBuilder` (flat blocks -> nested chapters).

### Phase 3: Footnotes (Complex)
- [x] Task 3.1: Detect Footnote Markers in body (regex).
- [ ] Task 3.2: Identify Footnote Bodies at page bottom. (Deferred: Using inline markers for now).
- [ ] Task 3.3: Linker logic. (Deferred).

## Timeline & Estimates
- Reading Order: 2 hours.
- Headings: 2 hours.
- Footnotes: 3 hours.
- Total: ~1 day.

## Risks & Mitigation
- **Risk:** Footnote detection is notoriously hard (false positives).
- **Mitigation:** Strict heuristics (bottom 15% of page, font size < body).
- **Fallback:** Treat failed footnotes as regular small text (don't lose data).

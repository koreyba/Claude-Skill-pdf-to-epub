---
phase: testing
title: Testing Strategy - Completeness Checker
description: Testing approach for completeness checker.
---

# Testing Strategy

## Test Coverage Goals
**What level of testing do we aim for?**

- 100% coverage of branching logic (found vs not found).

## Unit Tests
**What individual components need testing?**

- [ ] Identical text (Check = 100%).
- [ ] Completely different text (Check = 0%).
- [ ] Text with one missing paragraph (Identifies specific chunk).
- [ ] Boundary conditions (empty strings).

## Manual Verification
- [ ] Run on real book fixtures and examine the "Missing Chunks" list. Identify if they are truly missing or just headers/footers.

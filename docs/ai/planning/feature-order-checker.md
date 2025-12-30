---
phase: planning
title: Planning - Order Checker
description: Task breakdown for implementing the order checker.
---

# Project Planning & Task Breakdown

## Milestones
**What are the major checkpoints?**

- [x] Milestone 1: LIS Algorithm Implementation
- [x] Milestone 2: Integration with Validation Result
- [x] Milestone 3: Unit & Integration Tests

## Task Breakdown
**What specific work needs to be done?**

### Phase 1: Core Logic
- [x] Task 1.1: Implement `calculate_lis_length` utility.
- [x] Task 1.2: Implement `OrderChecker` class.
    - Input: List of found chunks (from completeness checker) with their positions.
    - Logic: Extract the sequence of observed positions. Check how long the increasing subsequence is.
- [x] Task 1.3: Integrate order metrics into `ValidationResult`.

### Phase 2: Testing
- [x] Task 2.1: Unit tests for specific reordering scenarios (A B C -> A C B).
- [x] Task 2.2: Add order check to standard `Validator` flow.

## Timeline & Estimates
- Implementation: 1.5 hours.

## Risks & Mitigation
- **Risk:** LCS is slow O(N^2).
- **Mitigation:** Use pylib `difflib.SequenceMatcher` or optimized O(N log N) LIS (Longest Increasing Subsequence) since chunk indices are unique.

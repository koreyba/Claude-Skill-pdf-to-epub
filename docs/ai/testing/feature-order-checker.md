---
phase: testing
title: Testing - Order Checker
description: Test plan for the order checker.
---

# Test Plan

## Unit Tests
- `test_perfect_order`: [0, 100, 200] -> Score 100.
- `test_reversed_order`: [200, 100, 0] -> Score Low.
- `test_interleaved`: [0, 200, 100, 300] -> Score ~75%.

## Integration Tests
- Use `test_integration_validation.py` to confirm the real fixture has good order.

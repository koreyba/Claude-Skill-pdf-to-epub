---
phase: implementation
title: Implementation - Completeness Checker
description: Technical implementation notes for completeness verification.
---

# Implementation Guide

## Code Structure
**How is the code organized?**

- `pdf_to_epub/validation/completeness_checker.py`
- `pdf_to_epub/validation/models.py` (New file for results structure)

## Implementation Notes
**Key technical details to remember:**

### Search Algorithm
```python
for chunk in chunks:
    if chunk.text not in target_text:
        failures.append(ValidationFailure(chunk=chunk))
```

### Result Calculation
`Score = (Chunks_Found / Total_Chunks) * 100`

## Error Handling
**How do we handle failures?**

- Handle empty source or target texts (return 0 or 100 score appropriately).

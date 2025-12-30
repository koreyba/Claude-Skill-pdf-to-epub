---
phase: implementation
title: Implementation - Core Utils
description: Technical details of core utilities implementation.
---

# Implementation Guide

## Development Setup
**How do we get started?**

- Python 3.10+
- Standard library dependencies only.

## Code Structure
**How is the code organized?**

- `core/utils.py`: Main entry point for utilities.

## Implementation Notes
**Key technical details to remember:**

### Logging
- Use `logging.StreamHandler` for CLI output.
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

### Path Handling
- Always use `pathlib.Path` objects.

## Error Handling
**How do we handle failures?**

- File operations should catch `OSError` and log it via the custom logger.

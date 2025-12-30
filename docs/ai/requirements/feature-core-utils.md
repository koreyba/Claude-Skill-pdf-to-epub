---
phase: requirements
title: Requirements - Core Utils
description: Define the requirements for the common utilities module.
---

# Requirements & Problem Understanding

## Problem Statement
**What problem are we solving?**

- Currently, the project lacks a centralized place for shared logic, which can lead to code duplication as more modules are added.
- Common tasks like logging, file path manipulation, and shared constants need a consistent implementation across the codebase.
- The project follows a "Separation of Concerns" principle, and `core/utils` is the foundation (Level 0) for all other modules.

## Goals & Objectives
**What do we want to achieve?**

- Primary goals: Provide a stable, tested library of utility functions.
- Secondary goals: Ensure consistent logging, simplify path operations, use mandatory type hints.
- Non-goals: Domain-specific logic (PDF/EPUB) is out of scope.

## User Stories & Use Cases
**How will users interact with the solution?**

- As a developer, I want to use a standard logging utility so that all logs follow the same format and level.
- As a developer, I want helper functions for path manipulation to avoid repetitive `os.path` logic.
- As a developer, I want access to global constants (like default chunk sizes or magic numbers) from a single source.

## Success Criteria
**How will we know when we're done?**

- `core/utils.py` created with logging (env-var support) and path helpers.
- Module has 100% test coverage and uses strict type hints.
- Successfully integrated into the development workflow.

## Constraints & Assumptions
**What limitations do we need to work within?**

- Must use only standard libraries or very stable third-party dependencies (if any).
- API must be simple and well-documented.

## Questions & Open Items
**What do we still need to clarify?**

- All questions resolved.
- Logging levels: INFO by default, configurable via `LOG_LEVEL` env var.
- Versioning: `VERSION` will be hardcoded in `core/utils.py` for v1.
- OS Compatibility: `pathlib` will be used for cross-platform support.

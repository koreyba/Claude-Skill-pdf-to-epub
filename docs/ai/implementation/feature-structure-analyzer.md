---
title: Implementation - Structure Analyzer
description: Implementation notes and technical debt tracking for structure analyzer.
---

# Implementation Notes

## Current Architecture
- Will reside in `claude_skill/analysis/` or `claude_skill/conversion/structure/`.
- Entry point: `StructureAnalyzer.analyze(pages: List[Page])`.

## Decisions Log
- **Date**: [Today]
- **Decision**: Separating "Font Analysis" from "Heading Detection". 
  - *Reasoning*: First pass gathers statistics (what is "Body Text"?). Second pass applies rules relative to Body Text.

## Technical Debt
- [ ] XY-Cut algorithm can be optimized.
- [ ] No machine learning yet; rule-based only.

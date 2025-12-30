---
phase: requirements
title: PDF to EPUB Conversion - Requirements
description: Core conversion pipeline for transforming PDF documents into valid EPUB files
feature: pdf-to-epub-conversion
---

# Requirements & Problem Understanding

## Problem Statement
**What problem are we solving?**

- **Core Problem:** Existing PDF to EPUB converters are "black boxes" - users don't know what went wrong when conversion fails, and results are unpredictable
- **Who is affected:** Power users converting 10+ books who need predictability and control over the conversion process
- **Current situation:** Users must manually fix EPUB files after conversion, or accept poor quality results. No transparency in the conversion process means no way to improve results systematically

**Specific pain points:**
1. No visibility into reading order detection confidence
2. Unknown text completeness - did we lose content?
3. No structured approach to handling different book types (fiction vs academic vs multi-column)
4. Failed conversions provide no actionable diagnostics

## Goals & Objectives
**What do we want to achieve?**

### Primary Goals
1. **Implement conversion orchestration** that coordinates all components (extract → order → detect → build)
2. **Create strategy pattern** for different book types with clear extension points
3. **Provide confidence scores** for reading order and structure detection
4. **Enable automatic validation** of conversion results

### Secondary Goals
1. Support custom strategies for specialized book types
2. Generate detailed conversion logs for debugging
3. Preserve rich formatting (bold, italic, footnotes)
4. Handle multi-column layouts with graceful degradation

### Non-Goals
- **Out of scope for Phase 5:**
  - Interactive PDF analysis (that's Phase 4 - already done)
  - Advanced CLI features (batch processing, watch mode, progress bars) - Phase 6
  - GUI interface
  - Cloud/API deployment
  
**Note:** Basic CLI scripts (analyze.py, convert.py, validate.py) ARE in Phase 5 scope as entry points for the skill.

## User Stories & Use Cases

### Story 1: Simple Book Conversion (Happy Path)
**As a** user with a simple single-column PDF book,  
**I want to** convert it to EPUB with one command and automatic validation,  
**So that** I get a ready-to-read EPUB file without manual intervention.

**Acceptance:**
- Conversion completes successfully
- Validation shows >99.5% text completeness
- Validation shows >98% reading order correctness
- EPUB opens correctly in e-readers

### Story 2: Recovery from Failed Conversion
**As a** user with a complex multi-column PDF,  
**I want to** receive clear diagnostics when conversion fails,  
**So that** I can adjust configuration and retry with better results.

**Acceptance:**
- System provides confidence score for reading order
- Validation report includes one-line summary of issues
- Suggested fixes are actionable (e.g., "adjust exclude_regions.top")
- EPUB is created even when confidence is low (with warning)

### Story 3: Academic Book with Endnotes
**As a** user converting academic PDFs with endnotes and multi-level headings,  
**I want to** use an academic strategy that handles footnotes correctly,  
**So that** footnote references are preserved and linked properly.

**Acceptance:**
- Footnotes detected and assigned unique IDs
- Multi-level headings (H1, H2, H3) properly structured
- Endnotes section correctly identified and processed

### Story 4: Custom Strategy Development (Extension)
**As a** power user with a specialized book format,  
**I want to** create my own conversion strategy by extending base_strategy,  
**So that** I can handle my specific book type without modifying core code.

**Acceptance:**
- Clear interface defined in BaseStrategy
- Documentation for creating custom strategies
- Example custom strategy provided
- Custom strategies can override individual steps (extract/order/detect/build)

## Success Criteria
**How will we know when we're done?**

### Functional Criteria
- [ ] Simple PDF converts to valid EPUB with validation passing
- [ ] Academic PDF with footnotes converts correctly
- [ ] Multi-column PDF converts with confidence warnings (not failures)
- [ ] Conversion generates detailed log file
- [ ] Failed conversions provide actionable diagnostics

### Quality Criteria
- [ ] 90%+ of same-type books convert with same config
- [ ] Validation pass rate: 85%+ for books of same type
- [ ] Reading order confidence: >0.9 for single-column, >0.7 for multi-column
- [ ] Text completeness: 99.5%+ recall for non-OCR PDFs

### Technical Criteria
- [ ] BaseStrategy provides clear extension points
- [ ] SimpleStrategy implements full workflow
- [ ] Converter orchestrates all components
- [ ] All modules have >90% test coverage
- [ ] Integration test covers full PDF → EPUB → validation flow

### Performance Benchmarks
- [ ] Convert single-column 300-page book in <30 seconds
- [ ] Memory usage <500MB for books up to 1000 pages
- [ ] No performance degradation for books 100-1000 pages
- [ ] Image extraction adds <5 seconds overhead for 20-image book

## Constraints & Assumptions

### Technical Constraints
- Must use existing components (pdf_extractor, detectors, epub_builder)
- Must integrate with existing validation pipeline
- EPUB output must be EPUB3 format
- Conversion must be single-threaded (no parallel processing in v1)

### Business Constraints
- Focus on text-based PDFs (OCR PDFs require pre-processing)
- Support only standard EPUB format (no KF8, MOBI, etc.)
- Command-line interface only (no GUI)

### Assumptions
1. **PDF has text layer** - image-only PDFs will fail early with clear error
2. **Detectors are already implemented** - we're orchestrating, not reimplementing
3. **epub_builder stub exists and will be fully implemented in this phase** - it's part of Phase 5 deliverables
4. **Config format is stable** - using conversion_config.json from Vision Plan
5. **Validation is separate** - converter doesn't run validation, that's orchestrated at CLI level
6. **PDF metadata is accessible** - most PDFs have title/author in info dict (fallback to "Unknown" if missing)

## Questions & Open Items

### Resolved
- ✅ Which strategies to implement first? → **Simple strategy for MVP, academic/nonfiction later**
- ✅ Should converter run validation? → **No, validation is separate concern (Phase 6 CLI)**
- ✅ How to handle epub_builder? → **It's a stub, implement as part of this phase**

### Open Questions
- ✅ **Metadata extraction:** Extract title, author, language, publisher, ISBN from PDF info dict; fallback to "Unknown" if missing; allow override via ConversionConfig.metadata
- ✅ **Image handling:** Extract all images (PNG/JPEG/GIF) from PDF, save to EPUB OEBPS/images/, update XHTML with <img> tags
- ✅ **Config validation:** Fail-fast approach - validate all fields in Converter.__init__() before starting conversion
- ✅ **Conversion log format:** JSON with structure: {timestamp, strategy_used, config, steps_completed: List[str], warnings: List[str], errors: List[str]}

### Items Requiring Stakeholder Input
- None (this is Phase 5 of planned roadmap)

### Research Needed
- EPUB3 specification for proper structure
- Best practices for EPUB metadata
- How to handle tables in EPUB (convert to images vs. HTML tables)

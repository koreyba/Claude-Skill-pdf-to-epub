# Implementation Plan - Advanced Heuristic Heading Detection

## Goal
Replace the naive font-size-based heading detector with a robust **probabilistic scoring system**. This will allow detecting headings that share the same font size as body text but differ in style (bold), spacing, or formatting (no punctuation).

## User Review Required
> [!IMPORTANT]
> This change moves from deterministic rules ("Size > 14pt = H1") to probabilistic heuristics. While more powerful, it may require tuning thresholds for specific books.

## Proposed Changes

### 1. [MODIFY] `pdf_to_epub/analysis/detectors/structure_classifier.py`

Refactor the `classify` method to use a **Scoring Engine** instead of a static map lookup.

#### New Logic: `calculate_heading_score(block, prev_block, next_block, body_style)`
The classifier will iterate through sorted blocks and assign a "Heading Score" (0-100) based on weighted signals:

| Signal | Condition | Weight (Draft) |
| :--- | :--- | :--- |
| **Style Distinction** | Font is **Bold** (and Body is not) | +30 |
| **Style Distinction** | Font is *Italic* (and Body is not) | +10 |
| **Size Distinction** | Size > Body Size | +10 per pt diff |
| **Format** | **No** terminal punctuation (`.`, `:`, `;`) | +20 |
| **Format** | Length < 150 chars | +10 |
| **Format** | All Uppercase | +10 |
| **Formatting** | "Standalone" (Isolated block) | +10 |
| **Spacing** | Top Margin > Bottom Margin * 1.5 | +20 |

**Thresholds:**
- Score > **50**: Low-level Heading (H3/H2)
- Score > **75**: Distinct Heading (H1)

### 2. [MODIFY] `pdf_to_epub/analysis/models.py`
Add fields to `SemanticBlock` to store debug info:
- `score`: float (The calculated probability)
- `debug_signals`: List[str] (Which heuristics triggered, e.g. ["Bold", "No-Dot"])

### 3. [NEW] `pdf_to_epub/analysis/utils/geometry.py` (Optional)
Utility to calculate vertical distances between blocks reliably.

## Verification Plan

### Automated Tests
1. **Unit Test**: Create a mock sequence of blocks:
   - Body paragraph.
   - **Bold Line** (No dot).
   - Body Paragraph.
   - Verify **Bold Line** is detected as Header.
2. **Spacing Test**: Verify that a line with large top margin is favored as a header.

### Visual Verification
Run `debug_structure.py` on `Excerpt_B...pdf`.
- **Success Criteria**: Detection of headings from the user provided Table of Contents (e.g., "The Essence of Integral Metatheory").
- **Check**: Verify they are assigned correct levels (H2 or H1).

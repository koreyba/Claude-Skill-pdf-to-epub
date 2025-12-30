---
phase: requirements
title: Requirements - Order Checker
description: Define requirements for detecting text order violations between PDF and EPUB.
---

# Requirements & Problem Understanding

## Problem Statement
**What problem are we solving?**

- PDF documents do not store text as a continuous stream but as positioned blocks. Extraction can often result in incorrect reading orders (e.g., mixing columns or skipping to page footers prematurely). 
- A standard completeness check (presence of text) does not catch these "scrambled" text scenarios.
- Users need a guarantee that the book remains readable and the logical flow is preserved.

## Goals & Objectives
**What do we want to achieve?**

- **Primary Goal:** Calculate a numerical `order_score` representing how well the sequence of text in EPUB follows the sequence in PDF.
- **Secondary Goal:** Identify specific chunks of text that are out of order for debugging.
- **Non-goal:** Automatic fixing of the order (that belongs to the `converter` and its `strategies`).

## User Stories & Use Cases
**How will users interact with the solution?**

- As a developer, I want to receive an `order_score` after conversion so I can decide if the result is acceptable.
- As a conversion strategy developer, I want to see which chunks are misplaced to identify logic errors in my `reading_order` detector.
- As a user, I want the validation report to fail if the text order is significantly broken (>2% displacement).

## Success Criteria
**How will we know when we're done?**

- The system correctly identifies identical sequences as 100% order score.
- The system correctly flags swapped paragraphs with a score < 100%.
- **Definition of Pass:** A score >= 98% is considered a successful order validation (allowing for minor noise/shifts).
- Performance: Must be able to process a 300-page book in seconds using chunk-based LCS.

## Constraints & Assumptions
**What limitations do we need to work within?**

- **Assumption:** Both PDF and EPUB texts are already canonicalized and segmented into chunks.
- **Constraint:** Must use the `text_segmenter` outputs to ensure consistency.

## Questions & Open Items
**What do we still need to clarify?**

- What is the best mathematical approach for `order_score`? (LCS vs Kendall Tau distance). Product vision suggests LCS.

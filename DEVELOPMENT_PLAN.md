# План разработки PDF to EPUB Converter

## Фаза 1: Фундамент (Foundation) — ЗАВЕРШЕНО ✅
- [x] Создать `pdf_to_epub/core/utils.py` (общие утилиты)
- [x] Создать `pdf_to_epub/core/text_segmenter.py` (сегментация текста)
- [x] Создать `pdf_to_epub/validation/text_canonicalizer.py` (нормализация текста)
- [x] Протестировать базовую сегментацию и канонизацию текста.

## Фаза 2: Экстракция (Extraction) — ЗАВЕРШЕНО ✅
- [x] Создать `pdf_to_epub/core/pdf_extractor.py` (извлечение данных из PDF)
    - [x] Реализовать умное удаление шума (колонтитулы, номера страниц).
- [x] Создать `pdf_to_epub/core/epub_extractor.py` (извлечение данных из EPUB)
- [x] Протестировать извлечение на реальных файлах.

### Phase 3: Validation & Checking (Status: **COMPLETED**)
- [x] **Completeness Checker**
    - [x] Comparison Algorithm (Sliding Window + Fuzzy Match).
    - [x] Robustness Tests (Sensitivity checks).
- [x] **Order Checker**
    - [x] LIS Algorithm for sequence validation.
    - [x] Integration into Completeness Checker.
- [x] **Validator Orchestrator**
    - [x] Integrate Completeness and Order checkers.
    - [x] Comprehensive validation on real fixtures.

### Phase 4: Content Analysis (Structure Analyzer) - **COMPLETED**
- **Goal:** Intelligent structure detection (Chapters, Footnotes).
- **Tasks:**
    - [x] Implement Heading Detection (Font size & weight analysis). (Implemented probabilistic scoring).
    - [x] Implement Reading Order (XY-Cut algorithm).
    - [x] Implement Footnote/Citation detection baseline.
- [x] Создать `pdf_to_epub/conversion/detectors/reading_order.py` (алгоритмы порядка чтения)
- [x] Создать `pdf_to_epub/conversion/detectors/heading_detector.py` (определение заголовков)
- [x] Создать `pdf_to_epub/conversion/pdf_analyzer.py` (анализ PDF и генерация конфига)
- [x] Протестировать автоматический анализ структуры PDF.

## Фаза 5: Конвертация (Conversion) — ЗАВЕРШЕНО ✅
- [x] Создать `pdf_to_epub/conversion/strategies/base_strategy.py` (базовый класс стратегий)
- [x] Создать `pdf_to_epub/conversion/strategies/simple_strategy.py` (стратегия для художественной литературы)
- [x] Создать `pdf_to_epub/conversion/converter.py` (главный оркестратор конвертации)
- [x] Создать `pdf_to_epub/core/epub_builder.py` (EPUB3 builder)
- [x] Создать все 12 data models (models.py)
- [ ] Протестировать полный цикл конвертации PDF -> EPUB.

## Фаза 6: Интерфейс и Интеграция (CLI) — ЗАВЕРШЕНО ✅
- [x] Создать `scripts/analyze.py` (CLI для анализа)
- [x] Создать `scripts/convert.py` (CLI для конвертации)
- [x] Создать `scripts/validate.py` (CLI для валидации)

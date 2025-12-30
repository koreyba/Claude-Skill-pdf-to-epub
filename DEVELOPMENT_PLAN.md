# План разработки PDF to EPUB Converter

## Фаза 1: Фундамент (Foundation) — ЗАВЕРШЕНО ✅
- [x] Создать `claude_skill/core/utils.py` (общие утилиты)
- [x] Создать `claude_skill/core/text_segmenter.py` (сегментация текста)
- [x] Создать `claude_skill/validation/text_canonicalizer.py` (нормализация текста)
- [x] Протестировать базовую сегментацию и канонизацию текста.

## Фаза 2: Экстракция (Extraction) — ЗАВЕРШЕНО ✅
- [x] Создать `claude_skill/core/pdf_extractor.py` (извлечение данных из PDF)
    - [x] Реализовать умное удаление шума (колонтитулы, номера страниц).
- [x] Создать `claude_skill/core/epub_extractor.py` (извлечение данных из EPUB)
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

## Фаза 4: Анализ структуры (Analysis)
- [ ] Создать `claude_skill/conversion/detectors/reading_order.py` (алгоритмы порядка чтения)
- [ ] Создать `claude_skill/conversion/detectors/heading_detector.py` (определение заголовков)
- [ ] Создать `claude_skill/conversion/pdf_analyzer.py` (анализ PDF и генерация конфига)
- [ ] Протестировать автоматический анализ структуры PDF.

## Фаза 5: Конвертация (Conversion)
- [ ] Создать `claude_skill/conversion/strategies/base_strategy.py` (базовый класс стратегий)
- [ ] Создать `claude_skill/conversion/strategies/simple_strategy.py` (стратегия для художественной литературы)
- [ ] Создать `claude_skill/conversion/converter.py` (главный оркестратор конвертации)
- [ ] Протестировать полный цикл конвертации PDF -> EPUB.

## Фаза 6: Интерфейс и Интеграция (CLI)
- [ ] Создать `scripts/analyze.py` (CLI для анализа)
- [ ] Создать `scripts/convert.py` (CLI для конвертации)
- [ ] Создать `scripts/validate.py` (CLI для валидации)

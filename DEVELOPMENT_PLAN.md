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

## Фаза 3: Валидация (Validation) — В ПРОЦЕССЕ 🔄
- [x] Создать `claude_skill/validation/completeness_checker.py` (проверка полноты текста)
    - [x] Реализовать нечеткий поиск (Fuzzy Match) для устойчивости к артефактам.
    - [x] Достичь 100% покрытия текста на реальных фикстурах.
- [ ] Создать `claude_skill/validation/order_checker.py` (проверка порядка текста)
- [ ] Создать `claude_skill/validation/validator.py` (главный оркестратор валидации)

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

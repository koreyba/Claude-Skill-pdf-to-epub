# План разработки PDF to EPUB Converter

## Фаза 1: Фундамент (Foundation)
- [x] Создать `claude_skill/core/utils.py` (общие утилиты)
- [ ] Создать `claude_skill/core/text_segmenter.py` (сегментация текста)
- [ ] Создать `claude_skill/validation/text_canonicalizer.py` (нормализация текста)
- [ ] Протестировать базовую сегментацию и канонизацию текста.

## Фаза 2: Экстракция (Extraction)
- [ ] Создать `claude_skill/core/pdf_extractor.py` (извлечение данных из PDF)
- [ ] Создать `claude_skill/core/epub_extractor.py` (извлечение данных из EPUB)
- [ ] Создать `claude_skill/core/epub_builder.py` (сборка EPUB файла)
- [ ] Протестировать чтение PDF и создание простейшего EPUB.

## Фаза 3: Валидация (Validation)
- [ ] Создать `claude_skill/validation/completeness_checker.py` (проверка полноты текста)
- [ ] Создать `claude_skill/validation/order_checker.py` (проверка порядка текста)
- [ ] Создать `claude_skill/validation/validator.py` (главный оркестратор валидации)
- [ ] Протестировать флоу валидации на синтетических данных.

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
- [ ] Протестировать сквозной флоу через командную строку.

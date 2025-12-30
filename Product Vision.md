# PDF to EPUB Converter - Product Design Document

## Executive Summary

**Продукт:** Инструмент для конвертации PDF в EPUB с автоматическим анализом структуры и валидацией качества.

**Проблема:** Существующие конвертеры работают как "черный ящик" - пользователь не знает, что пошло не так и как исправить. Результат непредсказуем.

**Решение:** Трёхэтапный подход с прозрачностью на каждом этапе:
1. **Analyze** - понять структуру PDF, задать вопросы, сгенерировать конфиг
2. **Convert** - конвертировать с выбранной стратегией
3. **Validate** - проверить качество, дать понятную диагностику

**Целевая аудитория:** Пользователи, конвертирующие 10+ книг, которым нужна предсказуемость и контроль.

---

## System Overview

### Архитектурные принципы

1. **Separation of Concerns**
   - Стабильное ядро (редко меняется)
   - Адаптируемые стратегии (под конкретные книги)
   
2. **Best-Effort + Honesty**
   - Система не обещает 100% точность
   - Confidence scores показывают уверенность
   - Валидация обязательна
   
3. **Configuration Over Code**
   - Поведение управляется через config файлы
   - Кастомизация без правки кода (где возможно)
   
4. **Fail Fast, Fail Clear**
   - Ошибки детектятся рано (analyze phase)
   - Диагностика понятна человеку (one-line summary)

---

## Business Flows

### Flow 1: Первая конвертация (Happy Path)

```
User: У меня есть academic.pdf, хочу EPUB

1. ANALYZE PHASE
   Input: academic.pdf
   System: Анализирует структуру
   System: Задает вопросы:
           - "Страницы 1-10 это оглавление? Пропустить?"
           - "Верхние 50px - колонтитул?"
           - "16pt шрифт - заголовки глав?"
   User: Отвечает на вопросы
   Output: academic_config.json + analysis_report.json
   
2. CONVERT PHASE
   Input: academic.pdf + academic_config.json
   User: Выбирает стратегию --strategy academic
   System: Конвертирует
   Output: academic.epub + conversion_log.json
   
3. VALIDATE PHASE (automatic)
   Input: academic.pdf + academic.epub
   System: Проверяет полноту текста
   System: Проверяет порядок текста
   System: Проверяет формальную валидность (опционально)
   Output: validation_report.json
   Status: ✅ PASSED
   Summary: "All checks passed. EPUB ready."

User: Открывает academic.epub → всё корректно
```

### Flow 2: Конвертация failed (Recovery Path)

```
User: У меня есть complex.pdf (2 колонки + врезки)

1. ANALYZE PHASE
   Output: complex_config.json
   Warning: "Multi-column layout detected. Reading order may be challenging."
   
2. CONVERT PHASE
   Strategy: academic (default для multi-column)
   Output: complex.epub + conversion_log.json
   
3. VALIDATE PHASE
   Status: ❌ FAILED
   Summary: "Reading order confidence 0.42 (threshold 0.6).
            Order score 0.85 (threshold 0.98). 15 paragraphs misplaced.
            Try: adjust exclude_regions or use custom strategy."
   
4. RECOVERY OPTIONS
   Option A: Adjust config
           - Увеличить exclude_regions.top (больше убрать сверху)
           - Поменять reading_order_strategy
           
   Option B: Custom strategy
           - customize_strategy.py academic my_complex_book
           - Ручная правка логики для этой книги
           
   Option C: Manual review
           - Принять результат, исправить в EPUB редакторе

User: Выбирает Option A → перезапускает → PASSED
```

### Flow 3: Пакетная конвертация (Scale Path)

```
User: У меня 50 книг одного типа (научпоп серия)

1. ANALYZE первой книги
   Output: series_config.json (шаблон)
   
2. CONVERT всех книг
   for book in books:
       convert(book, series_config.json, --strategy nonfiction)
       
3. VALIDATE всех
   Output: batch_validation_report.json
   
4. REVIEW failures
   Filter: status != "passed"
   → Ручная правка конфигов для проблемных
   
5. RE-CONVERT failures
   → Final batch готов
```

---

## Module Architecture

### Структура

```
pdf-epub-converter/
│
├── core/                   # Стабильное ядро
│   ├── pdf_extractor       # Извлечение данных из PDF
│   ├── epub_extractor      # Извлечение данных из EPUB
│   ├── epub_builder        # Создание EPUB файла
│   ├── text_segmenter      # Нормализация сегментации
│   └── utils               # Общие утилиты
│
├── conversion/             # Модуль конвертации
│   ├── pdf_analyzer        # Анализ структуры PDF
│   ├── detectors/          # Детекция элементов
│   ├── strategies/         # Стратегии конвертации
│   └── converter           # Оркестратор конвертации
│
├── validation/             # Модуль валидации
│   ├── text_canonicalizer  # Нормализация текста
│   ├── completeness_checker # Проверка полноты
│   ├── order_checker       # Проверка порядка
│   ├── validator           # Оркестратор валидации
│   └── epubcheck_wrapper   # Формальная валидность
│
└── scripts/                # CLI интерфейсы
    ├── analyze.py
    ├── convert.py
    ├── validate.py
    └── customize_strategy.py
```

### Роли модулей

#### Core (Стабильное ядро)

**pdf_extractor**
- **Роль:** Извлечь сырые данные из PDF
- **Вход:** PDF файл + config (exclude_regions, page_ranges)
- **Выход:** Структурированные блоки текста с метаданными
- **Ключевая фича:** Reading order с confidence score

**epub_extractor**
- **Роль:** Извлечь текст из EPUB для валидации
- **Вход:** EPUB файл
- **Выход:** Текст по порядку spine
- **Особенность:** Поддержка EPUB2 и EPUB3

**epub_builder**
- **Роль:** Создать валидный EPUB файл
- **Вход:** Главы с контентом + метаданные
- **Выход:** EPUB файл (EPUB3 + EPUB2 compat)
- **Ответственность:** Корректная структура, ID для сносок

**text_segmenter**
- **Роль:** ЕДИНАЯ сегментация для PDF и EPUB
- **Вход:** Текст (из PDF или EPUB)
- **Выход:** Chunks фиксированного размера (600 chars, overlap 100)
- **Критично:** Детерминированность → стабильные метрики валидации

#### Conversion (Модуль конвертации)

**pdf_analyzer**
- **Роль:** Понять структуру PDF, задать вопросы
- **Вход:** PDF файл
- **Выход:** Расширенный config.json + analysis_report.json
- **Интерактивность:** Задаёт вопросы пользователю, не угадывает
- **Детекты:** OCR presence, multi-column, problematic regions

**detectors/** (Библиотека детекторов)
- **heading_detector:** Находит заголовки (по размеру/жирности/паттерну)
- **footnote_detector:** Находит сноски, создаёт ID (scope-aware)
- **structure_detector:** Находит параграфы, цитаты, списки
- **reading_order:** Упорядочивает блоки (single/multi-column стратегии)

**strategies/** (Стратегии конвертации)
- **Роль:** Реализация логики для типа книги
- **Типы:** simple (fiction), academic (endnotes, 3+ headings), nonfiction
- **Кастомизация:** User может создать свою через customize_strategy.py
- **Архитектура:** Наследование от base_strategy, переопределение методов

**converter**
- **Роль:** Оркестратор процесса конвертации
- **Вход:** PDF + config + выбранная стратегия
- **Workflow:** extract → order → detect → build
- **Выход:** EPUB + conversion_log.json

#### Validation (Модуль валидации)

**text_canonicalizer**
- **Роль:** Нормализовать текст для сравнения
- **Что делает:** Unicode NFKC, склейка переносов, лигатуры, OCR артефакты
- **Режимы:** conservative (default), aggressive (для OCR PDF)
- **Критично:** Одинаковая нормализация для PDF и EPUB

**completeness_checker**
- **Роль:** Проверить что весь текст сохранился
- **Методы:** 
  - Shingles (n-граммы слов) → recall
  - Якоря (числа, даты, URL) → все должны быть
  - Rare words → терминология сохранена
- **Обработка ложных провалов:** Игнорирует переносы, лигатуры

**order_checker**
- **Роль:** Проверить что порядок текста не нарушен
- **Метод:** LCS на chunks из text_segmenter
- **Выход:** Order score + список переставленных chunks
- **Преимущество:** Независимость от разницы в абзацах PDF vs EPUB

**validator**
- **Роль:** Оркестратор всех проверок
- **Workflow:** extract → canonicalize → segment → check completeness → check order → epubcheck (optional) → report
- **Выход:** validation_report.json с one-line summary
- **Логика:** Сравнивает с thresholds, генерирует диагностику

**epubcheck_wrapper**
- **Роль:** Формальная валидация EPUB (опционально)
- **Best-effort:** Если нет → warning, не fail
- **Выход:** Добавляет epubcheck результаты в report или skip_reason

---

## Data Contracts

### Between Modules

#### 1. PDF → pdf_extractor → TextBlocks

```
Input: PDF file path + config
Output: List of TextBlocks

TextBlock = {
  text: string,                    // Текст блока
  font_size: number,               // Размер шрифта
  is_bold: boolean,                // Жирный или нет
  position: {
    x: number,                     // X координата
    y: number,                     // Y координата
    page: number                   // Номер страницы
  }
}
```

#### 2. TextBlocks → reading_order → OrderedBlocks + Confidence

```
Input: List of TextBlocks + strategy
Output: {
  blocks: List of TextBlocks (ordered),
  confidence: number (0.0-1.0),
  signals: {                       // Для диагностики
    column_separation: number,
    boundary_violations: number,
    y_consistency: number
  }
}
```

#### 3. OrderedBlocks → detectors → StructuredContent

```
Input: List of OrderedBlocks + config
Output: {
  chapters: [
    {
      title: string,
      level: number (1-3),
      content: string,
      footnotes: [
        {
          marker: string,
          id: string (fn-scope-slug),
          text: string
        }
      ]
    }
  ]
}
```

#### 4. StructuredContent → epub_builder → EPUB

```
Input: StructuredContent + metadata
Output: EPUB file

Metadata = {
  title: string,
  author: string,
  language: string,
  epub_version: "3.0"
}
```

#### 5. PDF/EPUB → text_segmenter → Chunks

```
Input: Text string
Output: List of Chunks

Chunk = {
  text: string,                    // 600 chars
  start_pos: number,               // Начало в оригинале
  end_pos: number,                 // Конец в оригинале
  overlap_prev: boolean            // Есть ли overlap с предыдущим
}

Config: chunk_size=600, overlap=100
```

#### 6. Chunks (PDF + EPUB) → validators → Metrics

```
Input: {
  pdf_chunks: List of Chunks,
  epub_chunks: List of Chunks
}

Output: {
  completeness: {
    shingle_recall: number (0.0-1.0),
    missing_anchors: List of strings,
    rare_words_missing: number
  },
  order: {
    order_score: number (0.0-1.0),
    misplaced_chunks: List of {
      pdf_pos: number,
      epub_pos: number,
      text_preview: string
    }
  }
}
```

#### 7. Metrics + Thresholds → validator → Report

```
Input: Metrics + validation_thresholds.json

Output: {
  status: "passed" | "failed" | "warning",
  summary: string,                 // One-line diagnostic
  timestamp: ISO timestamp,
  details: {
    completeness: {...},
    order: {...},
    epubcheck: {...} | skip_reason
  },
  thresholds_used: {...}
}
```

### Configuration Formats

#### conversion_config.json

```json
{
  "page_ranges": {
    "skip": [start, end],          // Страницы пропустить
    "content": [start, end],       // Основной контент
    "endnotes": [start, end]       // Сноски (optional)
  },
  "exclude_regions": {
    "top": 0.08,                   // % высоты страницы
    "bottom": 0.12,
    "left": 0.0,
    "right": 0.0
  },
  "multi_column": {
    "enabled": boolean,
    "column_count": number,
    "full_width_threshold": 0.8    // 80% ширины = full-width
  },
  "reading_order_strategy": "xy_sort" | "column_based" | "custom",
  "heading_detection": {
    "strategy": "font_size" | "bold" | "hybrid",
    "levels": number               // Уровней заголовков
  },
  "footnote_processing": {
    "enabled": boolean,
    "scope": "page" | "chapter" | "book",
    "marker_normalization": boolean
  }
}
```

#### validation_thresholds.json

```json
{
  "shingle_recall_min": 0.995,     // 99.5% текста сохранено
  "order_score_min": 0.98,         // 98% порядок правильный
  "reading_order_confidence_min": 0.6,
  "max_missing_anchors": 0,        // Якоря не теряются
  "max_rare_words_missing": 5
}
```

---

## System Data Flow

```
┌─────────────┐
│  USER       │
│  book.pdf   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 1: ANALYZE                                       │
│                                                         │
│  pdf_analyzer.py                                        │
│    ├─> Extract metadata                                │
│    ├─> Detect text layer (OCR check)                   │
│    ├─> Analyze font statistics                         │
│    ├─> Detect multi-column                             │
│    ├─> Ask user questions                              │
│    └─> Generate config                                 │
│                                                         │
│  Output: config.json + analysis_report.json            │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 2: CONVERT                                       │
│                                                         │
│  converter.py (with selected strategy)                 │
│                                                         │
│  Step 1: Extract                                        │
│    pdf_extractor                                        │
│      └─> TextBlocks (text, font, position)             │
│                                                         │
│  Step 2: Order                                          │
│    reading_order (strategy from config)                │
│      └─> OrderedBlocks + confidence                    │
│                                                         │
│  Step 3: Detect Structure                              │
│    heading_detector                                     │
│      └─> Chapters                                       │
│    footnote_detector                                    │
│      └─> Footnotes with IDs                            │
│    structure_detector                                   │
│      └─> Paragraphs, quotes, lists                     │
│                                                         │
│  Step 4: Build                                          │
│    epub_builder                                         │
│      └─> EPUB file                                      │
│                                                         │
│  Output: book.epub + conversion_log.json               │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 3: VALIDATE                                      │
│                                                         │
│  validator.py                                           │
│                                                         │
│  Step 1: Extract texts                                  │
│    pdf_extractor(book.pdf)    ──┐                      │
│                                  ├─> pdf_text           │
│    epub_extractor(book.epub)  ──┘    epub_text         │
│                                                         │
│  Step 2: Canonicalize                                   │
│    text_canonicalizer                                   │
│      └─> normalized_pdf_text                           │
│      └─> normalized_epub_text                          │
│                                                         │
│  Step 3: Segment                                        │
│    text_segmenter (SAME for both!)                     │
│      └─> pdf_chunks (600 chars, overlap 100)           │
│      └─> epub_chunks (600 chars, overlap 100)          │
│                                                         │
│  Step 4: Check Completeness                            │
│    completeness_checker                                 │
│      ├─> Shingles recall                               │
│      ├─> Missing anchors                               │
│      └─> Rare words                                     │
│                                                         │
│  Step 5: Check Order                                    │
│    order_checker (LCS on chunks)                       │
│      ├─> Order score                                    │
│      └─> Misplaced chunks                              │
│                                                         │
│  Step 6: Format Validation (optional)                  │
│    epubcheck_wrapper                                    │
│      └─> EPUB validity or skip_reason                  │
│                                                         │
│  Step 7: Generate Report                               │
│    Compare with thresholds                             │
│    Generate summary (one-line)                         │
│                                                         │
│  Output: validation_report.json                        │
│           ├─> status (passed/failed/warning)           │
│           ├─> summary (diagnostic)                     │
│           └─> details (metrics)                        │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │  USER REVIEW  │
              │               │
              │  If passed:   │
              │    ✓ DONE     │
              │               │
              │  If failed:   │
              │    Adjust     │
              │    config →   │
              │    Re-convert │
              └───────────────┘
```

---

## Development Roadmap

### Dependencies Graph

```
Level 0 (No dependencies):
  - utils
  - text_segmenter

Level 1 (Depends on Level 0):
  - text_canonicalizer (uses utils)
  - pdf_extractor (uses utils)
  - epub_extractor (uses utils)
  
Level 2 (Depends on Level 1):
  - detectors/* (uses pdf_extractor output)
  - epub_builder (standalone but needs format spec)
  - completeness_checker (uses text_segmenter + canonicalizer)
  - order_checker (uses text_segmenter)
  
Level 3 (Depends on Level 2):
  - pdf_analyzer (uses pdf_extractor + detectors)
  - strategies/* (uses detectors + epub_builder)
  - validator (uses all checkers + epubcheck_wrapper)
  
Level 4 (Depends on Level 3):
  - converter (uses strategies)
  - scripts/* (CLI wrappers)
```

### Recommended Development Order

**Phase 1: Foundation** (независимые модули)
1. `utils.py` - общие утилиты
2. `text_segmenter.py` - критичен для валидации
3. `text_canonicalizer.py` - нормализация текста

**Checkpoint:** Можем нормализовать и сегментировать текст

**Phase 2: Extraction** (работа с файлами)
4. `pdf_extractor.py` - извлечение из PDF
5. `epub_extractor.py` - извлечение из EPUB
6. `epub_builder.py` - создание EPUB

**Checkpoint:** Можем читать PDF/EPUB и создавать EPUB

**Phase 3: Validation** (проверка качества)
7. `completeness_checker.py` - полнота текста
8. `order_checker.py` - порядок текста
9. `epubcheck_wrapper.py` - формальная валидность
10. `validator.py` - оркестратор

**Checkpoint:** Можем валидировать готовые EPUB

**Phase 4: Analysis** (понимание структуры)
11. `detectors/reading_order.py` - упорядочивание
12. `detectors/heading_detector.py` - заголовки
13. `detectors/footnote_detector.py` - сноски
14. `detectors/structure_detector.py` - структура
15. `pdf_analyzer.py` - интерактивный анализ

**Checkpoint:** Можем анализировать PDF и генерировать конфиг

**Phase 5: Conversion** (создание EPUB)
16. `strategies/base_strategy.py` - базовый класс
17. `strategies/simple_strategy.py` - для fiction
18. `strategies/academic_strategy.py` - для academic
19. `strategies/nonfiction_strategy.py` - для nonfiction
20. `converter.py` - оркестратор

**Checkpoint:** Можем конвертировать PDF → EPUB

**Phase 6: CLI & Integration** (пользовательский интерфейс)
21. `scripts/analyze.py` - CLI для анализа
22. `scripts/convert.py` - CLI для конвертации
23. `scripts/validate.py` - CLI для валидации
24. `scripts/customize_strategy.py` - создание custom стратегий

**Checkpoint:** Полный workflow работает

**Phase 7: Testing & Documentation**
25. Тесты для core/ (обязательно)
26. Тесты для validation/ (обязательно)
27. Интеграционные тесты
28. Документация спецификаций

---

## Quality Gates

### Per Module

**Каждый модуль должен иметь:**
1. **Clear Interface** - понятные входы/выходы
2. **Data Contract** - форматы данных задокументированы
3. **Error Handling** - явные ошибки с понятными сообщениями
4. **Unit Tests** (для core/ и validation/ - обязательно)

### Per Phase

**Phase 1 (Foundation):**
- ✓ text_segmenter даёт одинаковый результат для одного текста
- ✓ text_canonicalizer идемпотентен

**Phase 2 (Extraction):**
- ✓ pdf_extractor извлекает текст из sample_books/simple.pdf
- ✓ epub_builder создаёт валидный EPUB (открывается в ридере)

**Phase 3 (Validation):**
- ✓ validator correctly identifies identical texts (score ~1.0)
- ✓ validator correctly identifies missing text (low recall)
- ✓ validator correctly identifies reordered text (low order_score)

**Phase 4 (Analysis):**
- ✓ pdf_analyzer генерирует валидный config.json
- ✓ detectors работают на sample_books/academic.pdf

**Phase 5 (Conversion):**
- ✓ Full pipeline: simple.pdf → EPUB → validation passes
- ✓ Full pipeline: academic.pdf → EPUB → validation passes

**Phase 6 (CLI):**
- ✓ analyze.py работает интерактивно
- ✓ convert.py с --validate автоматически проверяет результат

### System-wide

**Integration Tests:**
1. Simple book (fiction) → должен пройти с minimal config
2. Academic book (endnotes, multi-level headings) → должен пройти
3. Multi-column book → может быть warning о confidence, но конвертируется
4. Image-based PDF (no OCR) → должен fail early с понятной ошибкой

**Success Criteria:**
- 90%+ книг одного типа конвертируются с одним конфигом
- Validation report всегда понятен (summary в одну строку)
- Failed случаи имеют actionable диагностику

---

## Edge Cases & Boundaries

### What System Handles

✅ **Single-column PDF** - высокая точность
✅ **2-column PDF** - хорошая точность (confidence ~0.7-0.8)
✅ **Endnotes** - с правильным конфигом
✅ **Multi-level headings** (1-3 levels)
✅ **Footnotes** (page/chapter/book scope)
✅ **Bold/Italic** - сохраняется
✅ **Images** - вставляются
✅ **OCR artifacts** - обрабатываются канонизацией

### What System Does NOT Handle

❌ **Image-based PDF без текстового слоя** - требуется OCR сначала
❌ **3+ column layouts** - низкая точность (confidence <0.5)
❌ **Complex tables** - конвертируются как изображения
❌ **Mathematical formulas** - как изображения
❌ **Нестандартные шрифты** - могут быть проблемы с лигатурами
❌ **DRM-protected PDF** - не открывается

### Graceful Degradation

**When confidence < 0.6:**
- Система НЕ отказывается конвертировать
- Выдаёт warning
- Рекомендует ручную проверку
- Валидация покажет проблемы

**When validation fails:**
- Система НЕ удаляет EPUB
- Даёт понятную диагностику (summary)
- Предлагает actionable шаги (adjust config, custom strategy)

**When optional tools missing:**
- epubcheck not installed → skip с explanation, не fail
- Конвертация продолжается

---

## Success Metrics

### Technical Metrics

1. **Validation Pass Rate**
   - Target: 85%+ для книг одного типа с одним конфигом
   
2. **Reading Order Confidence**
   - Single-column: >0.9
   - 2-column: >0.7
   - 3+ column: >0.5 (с предупреждением)
   
3. **Text Completeness**
   - Target: 99.5%+ recall для non-OCR PDF
   
4. **Order Accuracy**
   - Target: 98%+ order_score для single-column

### User Experience Metrics

1. **Time to First Success**
   - Новый пользователь → первый качественный EPUB: <30 минут
   
2. **Config Reusability**
   - Один конфиг для серии книг: 90%+ случаев
   
3. **Diagnostic Clarity**
   - Failed cases: пользователь понимает проблему без чтения документации
   
4. **Recovery Time**
   - Failed → исправлен config → passed: <10 минут

---

## Future Considerations (Out of Scope v1)

**Возможные расширения (не сейчас):**
- GUI интерфейс (сейчас только CLI)
- Batch processing с очередями
- Cloud/API версия
- ML для автоматического детекта структуры (сейчас rule-based)
- Поддержка DOCX → EPUB
- Редактор EPUB (сейчас только конвертация)

**Почему не сейчас:**
- v1 фокус: качественная конвертация PDF → EPUB для power users
- CLI достаточен для целевой аудитории
- Rule-based подход понятнее и контролируемее

---

## Glossary

**TextBlock** - блок текста из PDF с метаданными (font, position)

**Chunk** - сегмент текста фиксированного размера (600 chars) с overlap

**Confidence** - оценка уверенности системы (0.0-1.0) в правильности reading order

**Scope** - область действия маркера сноски (page/chapter/book)

**Reading Order** - последовательность чтения текстовых блоков в PDF

**Strategy** - класс с логикой конвертации для типа книги

**Canonicalization** - нормализация текста для корректного сравнения

**Shingles** - n-граммы слов для проверки полноты текста

**LCS** - Longest Common Subsequence для проверки порядка

**Anchor** - обязательный элемент (число, URL, дата), который не должен потеряться

---

**Document Version:** 3.0 Final  
**Status:** Ready for Development  
**Last Updated:** 2025-12-30
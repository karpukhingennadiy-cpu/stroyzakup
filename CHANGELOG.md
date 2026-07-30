# Changelog

## [Unreleased] — v2.0.0-dev (2026-07-30)

### QA (блок A)
- **A2**: +48 автотестов (78 total): негативные ветки parse/match/send_rfq/public_quote/competitive_sheet/geocode, IDOR, SQLi/XSS-устойчивость, throttle 429
- **A3**: нагрузочный sanity (`backend/scripts/load_sanity.py`): p95 создания 0.75с, подбора 0.47с, без 5xx и дедлоков SQLite → `docs/QA_LOAD.md`
- **A4**: матрица парсинга 20 формулировок → 100% (20/20) после доработки whitelist'ов и промта → `docs/QA_PARSE_MATRIX.md`
- **A6**: аудит безопасности → `docs/QA_SECURITY.md`; закрыты кодом: IDOR в `/quotes/` и `competitive_sheet`, XSS в HTML-письмах, валидация цен в public_quote (0/отрицательные/нечисло/пусто → 400), 404 вместо 500 на чужой/несуществующей заявке

### Фичи (блок B)
- **B9**: LLM-переписка с поставщиками — `apps/emails/prompts.py` (8 сценариев) + `llm_writer.py` (JSON-валидация, кэш по хэшу контекста, пост-проверка запрещённых формулировок, fallback на статичные шаблоны). Письма с `needs_review` не отправляются. Eval-набор: 21 тест
- **B10**: `manage.py send_deadline_reminders` — напоминания неответившим за 24ч и 2ч до дедлайна, идемпотентно (`reminder_24h_sent_at`/`reminder_2h_sent_at`)
- **B7**: уведомления заказчику о каждом КП («Поставщик X прислал КП на Y ₽») и о готовности конкурентного листа (N из M)
- **B1**: приём ответов по email — `manage.py fetch_inbound` (IMAP-polling) + `inbound_parser.py` (LLM извлекает цены из текста письма → QuoteItem; вопросы → авто-ответ llm_writer). Инструкция: `docs/INBOUND_SETUP.md`
- **B4**: модерация поставщиков — `rejected` исключён из подбора, `unverified` ×0.9 + бейдж в UI; staff-эндпоинты `moderate`/`bulk_verify`; кнопки в `/lk/suppliers`
- **B5**: ручное добавление поставщика — форма (название, email, адрес, категории, тип) + автообогащение каталога и геокодинг
- **B6**: UX мастера — индикаторы этапов («ИИ анализирует материал…»), уточняющие вопросы LLM с ответами в spec (новое поле `RequestItem.clarification_question`), баннер «найдено N новых поставщиков», автосохранение черновика в localStorage

### Данные (блок C)
- **C2**: дедупликация — `backend/scripts/dedupe_suppliers.py` (INN/сайт/fuzzy-имя с потокенной проверкой); слиты 2×KNAUF Gips и 2×Kerama Marazzi, дублей не осталось → `docs/DEDUP_REPORT.md`

### Документация (блок D)
- README переписан; добавлены `docs/API.md`, `docs/OPERATIONS.md`, `docs/INBOUND_SETUP.md`

### Миграции
- `quotes.0006`: `RfqInvitation.reminder_24h_sent_at`, `reminder_2h_sent_at`
- `requests.0005`: `RequestItem.clarification_question`

## [1.1.0] — AI-препроцессинг материалов + автодiscovery поставщиков

## [1.0.0] — Полный рабочий цикл закупок

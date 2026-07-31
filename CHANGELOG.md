# Changelog

## [2.0.0] — 2026-07-31

### QA (блок A)
- **A1**: E2E почтовый контур на реальной почте (Mail.ru): регистрация/логин/выход, заявка с уточнениями ИИ, RFQ → письмо → КП по ссылке → ответ письмом → LLM обновил КП; протокол `docs/QA_E2E_PROTOCOL.md`. Найден и закрыт дефект: LLM терял позиции заявки в письмах (пост-проверка фактов + регресс-тесты)
- **A2**: +50 автотестов (80 total): негативные ветки parse/match/send_rfq/public_quote/competitive_sheet/geocode, IDOR, SQLi/XSS-устойчивость, throttle 429
- **A3**: нагрузочный sanity (`backend/scripts/load_sanity.py`): p95 создания 0.75с, подбора 0.47с, без 5xx и дедлоков SQLite → `docs/QA_LOAD.md`
- **A4**: матрица парсинга 20 формулировок → 100% (20/20) после доработки whitelist'ов и промта → `docs/QA_PARSE_MATRIX.md`
- **A6**: аудит безопасности → `docs/QA_SECURITY.md`; закрыты кодом: IDOR в `/quotes/` и `competitive_sheet`, XSS в HTML-письмах, валидация цен в public_quote, 404 вместо 500 на чужой/несуществующей заявке

### Фичи (блок B)
- **B9**: LLM-переписка с поставщиками — `apps/emails/prompts.py` (8 сценариев) + `llm_writer.py` (JSON-валидация, кэш, пост-проверка запрещённых формулировок и полноты фактов, fallback на шаблоны). Письма с `needs_review` не отправляются. Eval-набор: 23 теста
- **B10**: `manage.py send_deadline_reminders` — напоминания неответившим за 24ч и 2ч, идемпотентно
- **B7**: уведомления заказчику о каждом КП и о готовности конкурентного листа
- **B1**: приём ответов по email — `manage.py fetch_inbound` (IMAP) + `inbound_parser.py` (LLM извлекает цены из текста письма → QuoteItem; вопросы → авто-ответ). Инструкция: `docs/INBOUND_SETUP.md`
- **B2**: `USE_CELERY` — parse/match/send_rfq через Celery (202 + task_id) при включении, sync fallback по умолчанию; `Request.match_results` для чтения результатов async-подбора; polling в UI мастера
- **B4**: модерация поставщиков — `rejected` исключён из подбора, `unverified` ×0.9 + бейдж; staff-эндпоинты `moderate`/`bulk_verify`; кнопки в `/lk/suppliers`
- **B5**: ручное добавление поставщика — форма + автообогащение каталога и геокодинг
- **B6**: UX мастера — индикаторы этапов, уточняющие вопросы LLM с ответами в spec (`RequestItem.clarification_question`), баннер «найдено N новых», автосохранение черновика

### Данные (блок C)
- **C1**: `backend/scripts/seed_regions.py` — 10 регионов × 10 категорий: 192 поставщика, **134 верифицированы DaData** (≥100 ✓); найден и закрыт баг `DADATA_URL` и None-safe разбор в enricher.py
- **C2**: дедупликация — `backend/scripts/dedupe_suppliers.py` (INN/сайт/fuzzy-имя с потокенной проверкой); слиты дубли KNAUF, Kerama Marazzi и др. → `docs/DEDUP_REPORT.md`

### Документация (блок D)
- README переписан; `docs/API.md`, `docs/OPERATIONS.md`, `docs/INBOUND_SETUP.md`
- Презентация: +слайды MaterialIntel и «База поставщиков и результаты QA»

### Осознанно перенесено (нужна инфраструктура)
- **B3** (PostgreSQL-контур), **B8** (prod-деплой, TLS, бэкапы) — нужен Docker/сервер; код готов (prod-настройки, docker-compose.prod.yml)
- **A5** (скриншоты в Gmail) — почтовый контур проверен в Mail.ru
- MX-запись `in.минитендер.рф` — настраивается у хостера по `docs/INBOUND_SETUP.md`

### Миграции
- `quotes.0006`: `RfqInvitation.reminder_24h_sent_at`, `reminder_2h_sent_at`
- `requests.0005`: `RequestItem.clarification_question`
- `requests.0006`: `Request.match_results`

## [1.1.0] — AI-препроцессинг материалов + автодiscovery поставщиков

## [1.0.0] — Полный рабочий цикл закупок


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

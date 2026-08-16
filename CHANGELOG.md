# Changelog

## [2.4.0] — unreleased (2026-08-16)

### Релизная подготовка
- Версии синхронизированы: frontend/backend → 2.4.0 (было 0.1.0)
- CI: `workflow_dispatch` для backend.yml (ручной запуск)
- Скрипт бэкапа БД `scripts/backup_db.sh` (pg_dump + retention 14 дней)
- Пагинация поставщиков (10/стр)

## [2.3.0] — 2026-08-16

### Редизайн интерфейса (REDESIGN_TASK)
- **Дизайн-система:** консолидация акцентов (янтарный = CTA, синий = интерактив), статус-токены, тёмные поверхности, glow-тень; исправлен баг Tailwind 4 (конфиг-маппинги перенесены в `@theme inline`)
- **Лендинг:** trust bar, янтарный бейдж MVP, статистика 56px, стрелки-коннекторы шагов, иконки фич, секция отзывов, CTA-градиент, футер
- **ЛК:** янтарный активный пункт сайдбара, плашка «Новая заявка», аватар, empty states виджетов, табы-фильтры, цветные бейджи, пагинация 10/стр, sticky header, баннер Sparkles
- **Мастер:** stepper (янтарный/зелёный/серый + подписи), светлая таблица, валидация с подсветкой, sticky CTA на мобильных
- **Поставщики:** чипсы статусов, зебра-таблица, иконки контактов
- **Авторизация:** тёмный градиент, контрастные поля (WCAG AA), «Запомнить меня», Google-вход (заглушка)

## [2.2.0] — 2026-08-04

### Frontend (KC-01..03)
- Редизайн страниц E2-E9 (конкурентный лист, заявки, поставщики, КП)
- Структурные оптимизации (web-vitals, image formats)
- PostHog-аналитика: Django SDK, consent banner (152-ФЗ), полная интеграция

### Backend
- Статусный поток `ready`/`completed` (G2)

### CI/CD
- GitHub Actions: backend + frontend + docker workflow
- Staging deploy workflow

## [2.1.0] — 2026-08-04

- Docs: регенерация после мержа PR #1-#5
- Backend review: фиксы протокола победителя (status в экспорте), человекочитаемый срок доставки в XLSX
- Kimi Work Blueprint: сквозные автоматизации цикла закупки

## [2.0.0] — 2026-07-31

### QA (блок A)
- **A1**: полный E2E в браузере (WebBridge, реальная почта Mail.ru): все 10 сценариев PASS — регистрация/логин/выход, мастер (1/5 позиций, мусор «asdf 123»), уточняющие вопросы ИИ, адрес, фильтры и score_breakdown, RFQ из UI, КП по ссылке → ответ письмом → LLM обновил КП, конкурентный лист, истёкшая сессия → /login, мобильная 375px. Найдены и закрыты кодом: LLM терял позиции в письмах (пост-проверка фактов), экран «Тендер запущен» не показывался (`result.sent` vs `results[]`), сайдбар ЛК не адаптивен (бургер-меню) → `docs/QA_E2E_PROTOCOL.md`
- **A2**: +50 автотестов (84 total): негативные ветки, IDOR, SQLi/XSS, throttle 429, Celery-режим
- **A3**: нагрузочный sanity: p95 создания 0.75с, подбора 0.47с, без 5xx и дедлоков → `docs/QA_LOAD.md`
- **A4**: матрица парсинга 100% (20/20) → `docs/QA_PARSE_MATRIX.md`
- **A6**: аудит безопасности; закрыты: IDOR, XSS в письмах, валидация цен → `docs/QA_SECURITY.md`

### Фичи (блок B)
- **B9**: LLM-переписка — 8 сценариев промтов, пост-проверка запрещённых формулировок и полноты фактов, fallback на шаблоны, `needs_review` не отправляется; eval 23 теста
- **B10**: напоминания неответившим за 24ч/2ч, идемпотентно
- **B7**: уведомления заказчику о КП и готовности конкурентного листа
- **B1**: inbound email — `fetch_inbound` (IMAP) + LLM-извлечение цен из писем; авто-ответы на вопросы. Инструкция: `docs/INBOUND_SETUP.md`
- **B2**: `USE_CELERY` — 202 + task_id, `Request.match_results`, polling в UI; sync fallback
- **B3**: PostgreSQL-проверка: контейнер PostGIS, миграции, тесты **84/84 на PG**, перенос демо-данных (dumpdata/loaddata); найден и закрыт баг multipart-списков в send_rfq (маскировался на SQLite)
- **B4**: модерация — rejected исключён, unverified ×0.9 + бейдж, staff-эндпоинты, кнопки в UI
- **B5**: ручное добавление поставщика + автообогащение/геокодинг
- **B6**: UX мастера — этапы, уточнения LLM в spec, discovered-баннер, черновик (проверен в браузере)
- **B8**: prod-контур в Docker поднят и прошёл smoke (health 200, login JWT через nginx→backend→PG); исправлены дефекты сборки (Dockerfile ENV/FROM, .dockerignore, GDAL, env-проброс, JSON CMD); чек-лист сервера: `docs/GO_LIVE_CHECKLIST.md`

### Данные (блок C)
- **C1**: `seed_regions.py` — 192 поставщика (10 регионов × 10 категорий), **134 верифицированы DaData**; баги `DADATA_URL`/None-safe в enricher закрыты
- **C2**: дедупликация слияниями → `docs/DEDUP_REPORT.md`

### Документация (блок D)
- README, `docs/API.md`, `docs/OPERATIONS.md`, `docs/INBOUND_SETUP.md`, `docs/GO_LIVE_CHECKLIST.md`
- Презентация: +слайды MaterialIntel и «База поставщиков и результаты QA»

### Осталось на стороне инфраструктуры (не код)
- MX `in.минитендер.рф` + catch-all (Beget, `docs/INBOUND_SETUP.md`)
- TLS Let's Encrypt, cron-бэкапы, серверный .env — по `docs/GO_LIVE_CHECKLIST.md`
- Скриншоты письма в Gmail (контур проверен в Mail.ru)

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

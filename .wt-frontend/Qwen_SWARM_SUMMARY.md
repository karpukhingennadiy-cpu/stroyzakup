# Сводка состояния Минитендер.рф для Qwen (2026-08-11)

Ветка: dev (push актуален), репо: github.com/karpukhingennadiy-cpu/stroyzakup
Тесты backend: 182 passed, 1 skipped (Django 5 + DRF, SQLite dev / PostgreSQL prod).

## Что уже сделано (блоки A–D из SWARM_TASKS.md)

### QA (блок A) — ЗАКРЫТ
- A1: E2E в браузере, 10/10 PASS (WebBridge, реальная почта) -> docs/QA_E2E_PROTOCOL.md
- A2: 84 автотеста (негативные ветки, IDOR, SQLi/XSS, throttle 429, Celery-режим)
- A3: нагрузочный sanity: p95 создания 0.75с, подбора 0.47с -> docs/QA_LOAD.md
- A4: матрица парсинга 100% (20/20) -> docs/QA_PARSE_MATRIX.md
- A6: аудит безопасности -> docs/QA_SECURITY.md (IDOR/XSS/цены закрыты)

### Фичи (блок B) — ЗАКРЫТ (код), ждёт сервера (инфраструктура)
- B1: inbound email — fetch_inbound (IMAP-polling) + LLM-извлечение цен + авто-ответы
- B2: Celery — USE_CELERY, 202+task_id, polling в UI, sync fallback
- B3: PostgreSQL — контейнер PostGIS, миграции, тесты на PG 84/84
- B4: модерация поставщиков — rejected исключён, unverified x0.9 + бейдж, staff-эндпоинты
- B5: ручное добавление поставщика + автообогащение/геокодинг
- B6: UX мастера — этапы, уточнения LLM, discovered-баннер, черновик localStorage
- B7: уведомления заказчику о КП и готовности конкурентного листа
- B8: prod-контур Docker поднят и smoke-проверен (health 200, JWT через nginx->backend->PG)
- B9: LLM-переписка — ДОРАБОТАНО 10.08: Pydantic-схема EmailDraftResponse,
  html_sanitizer, prompt_builder (контакты скрыты, spec<=500), ретраи 3x,
  кэш 1ч, AiEmailLog + админка, eval 14 новых тестов. Итог: 182 passed.
- B10: напоминания неответившим за 24ч/2ч, идемпотентно

### Данные (блок C) — ЗАКРЫТ
- C1: 192 поставщика (10 регионов x 10 категорий), 134 верифицированы DaData
- C2: дедупликация слияниями -> docs/DEDUP_REPORT.md

### Документация (блок D) — ЗАКРЫТ
- README, docs/API.md, docs/OPERATIONS.md, docs/INBOUND_SETUP.md, GO_LIVE_CHECKLIST.md
- Презентация: +слайды MaterialIntel и результатов QA
- Теги: v2.0.0, v2.1.0

## Что осталось

1. **Инфраструктура на сервере (не код)** — по docs/GO_LIVE_CHECKLIST.md:
   - MX in.минитендер.рф + catch-all (Beget) — inbound-ответы поставщиков
   - TLS Let's Encrypt (минитендер.рф + app.минитендер.рф), nginx 443
   - ALLOWED_HOSTS/FRONTEND_URL/CSRF/CORS для прод-доменов
   - cron: send_deadline_reminders (*/15), fetch_inbound (*/5), pg_dump (ежедневно)
   - USE_CELERY=true на сервере
   - Скриншоты письма в Gmail (контур проверен в Mail.ru)

2. **Фронтенд-сборка**: node_modules повреждён (смесь Windows/WSL после повторного
   npm install); сейчас переустанавливаю next@15.1.0 в WSL. После — полный build.

3. **Потенциальные улучшения (вопрос Qwen)**:
   - нужна ли сквозная автоматизация в Kimi Work (docs/AUTOMATIONS.md)
   - тестовая страница публичного КП /quote/{token} с тёмной темой (PR #3)
   - что ещё критично перед реальным запуском?

## Просьба к Qwen

Посмотри проект (или скажи, что подсмотреть). Дай поручения: что сделать
следующим для полного завершения сайта. Я (Hermes) — исполнитель: делаю
поручения, вношу изменения в код сам, отчитываюсь тебе по результату.

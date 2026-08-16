# Отчёт: Backend Code Review + экспорт конкурентного листа

Дата: 2026-08-03. Ветка: `feature/backend-review` → PR в `dev`.

## 1. Статус проекта

- **Репозиторий склонирован**: да (рабочая копия уже была локально). ⚠️ В ТЗ указан репозиторий `github.com/karpukhingennadiy-cpu/minitender` — такого репозитория не существует; фактический репозиторий проекта «Минитендер»: `karpukhingennadiy-cpu/stroyzakup`. Ветки `dev` на GitHub не было — создана от актуального `main` (включая 8 локальных коммитов v2.0.0, которые не были запушены).
- **Тесты**: **96 из 96 пройдено** (+1 skipped). В ТЗ упоминались 78 — фактически в репозитории было 84; добавлено 12 новых тестов. Ни один существующий тест не сломан.
- **Критические баги**: найдены и исправлены — IDOR в `update_item`, открытый generic inbound webhook (подробности ниже).

## 2. Результаты Code Review

### Исправлено в этом PR

| Файл | Проблема | Серьёзность | Рекомендация / Фикс |
|---|---|---|---|
| `apps/requests/views.py` (`update_item`) | **IDOR**: action брал `RequestItem` по `request_id` из URL без проверки владельца — любой авторизованный пользователь мог править позиции чужой заявки | **High** | scope `request__customer=request.user` → 404; регресс-тест `test_update_item_other_users_request_404` |
| `apps/emails/views.py` (`generic_inbound_webhook`) | Вебхук без аутентификации: любой мог подделать входящее письмо для известного `reply_code` (создание КП/EmailMessage, триггер LLM-ответов) | **High** | shared-secret `INBOUND_GENERIC_WEBHOOK_SECRET` + заголовок `X-Webhook-Secret` (опционально, как у Mailgun-вебхука); тесты 403/200 |
| `apps/requests/tasks.py` (`match_suppliers_task`) | Аргумент `limit` молча терялся: view просил N поставщиков, задача всегда возвращала 20 | Medium | `match_suppliers(req, limit)` |
| `apps/requests/tasks.py` | Невалидные статусы `parse_failed`/`match_failed` (отсутствуют в `STATUS_CHOICES`): заявка в `parse_failed` никогда не могла быть распарсена повторно (view допускает только `draft`/`parsing`) — «кирпич» | Medium | failure-пути → `draft` (parse, зеркалит sync FIX-K1) и `confirmed` (match); успешный async-статус `parsed` добавлен в choices + миграция `0007_alter_request_status` |
| `apps/quotes/views.py` (`competitive_sheet`) | N+1: по запросу на каждое КП (`items.all()`, `request_item`, `supplier`) | Medium | `select_related('supplier')` + `prefetch_related('items__request_item')` |
| `apps/suppliers/views.py` (`search_radius`) | `float()` на query-параметрах без обработки — 500 на `?lat=abc` | Low | валидация → 400 |
| `apps/requests/services/parser.py` | `validate_items` (JSON Schema, заявлена как FIX-M3 в зависимостях) определена, но нигде не вызывалась — невалидные позиции LLM шли прямо в БД | Medium | валидация подключена к LLM-пути, отклонённые позиции логируются |

### Зафиксировано (НЕ исправлено — требует решения владельца)

| Файл | Проблема | Серьёзность | Рекомендация |
|---|---|---|---|
| `apps/emails/tasks.py`, `apps/requests/tasks.py` | Мёртвый код: `send_rfq_email_task`, `geocode_address_task`, `discover_suppliers_task` нигде не вызываются. При этом `send_rfq_email_task` игнорирует флаг `needs_review` — если его когда-нибудь подключат, LLM-письма с флагом модерации уйдут без проверки (обход политики B9) | Medium | Удалить или подключить с проверкой `needs_review` |
| `apps/requests/middleware/rate_limit.py` | Rate-limit middleware (100/мин на IP) написан, но не подключён в `MIDDLEWARE` ни в одном settings | Low | Подключить в prod после нагрузочного теста (в тестах даст ложные 429) |
| `apps/suppliers/views.py` | `SupplierViewSet` — ModelViewSet с `IsAuthenticated`: любой заказчик может создавать/править/удалять записи глобального каталога поставщиков (moderate/bulk_verify уже IsStaff). Оставлено как есть: ручное добавление поставщиков (B5) — осознанная фича, смена прав сломает тесты и UI | Medium | Рассмотреть: create — всем, update/delete — IsStaff |
| `config/settings/base.py` | `SECRET_KEY="dev-secret-key"` и пароль БД `minitender` хардкодом (только dev/test; prod требует env) — уже в QA_SECURITY.md как SEC-5 | Low | Вынести в env с dev-default |
| `apps/accounts/urls.py` | `/api/auth/login/` без throttle (брутфорс) — уже в QA_SECURITY.md как SEC-7 | Low | Добавить `AnonRateThrottle` на login |
| `apps/requests/serializers.py` (`RequestCreateSerializer`) | Поле `address` writable — можно привязать чужой `Address` по id (IDOR-lite: утечка текста адреса через `address_detail`) | Low | Фильтровать `address` по `customer=request.user` в `validate_address` |
| `apps/quotes/views.py` (`public_quote`) | Ссылка КП не имеет срока действия: deadline (+3 дня) только в тексте письма, технически не enforced | Low | Проверять `invitation.created_at + N дней` при POST |
| `apps/emails/services.py` / `apps/quotes/views.py` | Дублирование `_quote_total` и расчёта `grand_total` в 3 местах | Low | Вынести в `apps/quotes/exporters.get_competitive_rows` (уже частично) |
| `apps/requests/views.py` (`confirm`) | Синхронный `match_suppliers` в HTTP-запросе (нет Celery-ветки, в отличие от parse/match) — при росте каталога будет таймаутить | Low | Добавить Celery-ветку по аналогии с `match_suppliers` |

## 3. Покрытие тестами

Общее покрытие `--cov=apps`: **66%** (2377 stmts, 812 miss).

Недостаточно покрытые модули:

| Модуль | Покрытие | Что добавить |
|---|---|---|
| `apps/emails/inbound_parser.py` | **0%** | Тесты `extract_prices_to_quote`: извлечение цен (mock `llm.chat`), ветка `is_question` → `_answer_supplier_question`, невалидный JSON, `price <= 0`, длинный HTML (`_strip_html`) |
| `apps/emails/services.py` | **40%** | `process_inbound_email_reply` (создание Quote, статус replied, unknown reply_code → None), `_maybe_notify_sheet_ready` (порог 2+, маркер-дедупликация), `notify_customer_quote_received` |
| `apps/emails/tasks.py` | **0%** | См. выше — мёртвый код; сначала решить судьбу задачи |
| `apps/emails/management/commands/*` | **0%** | `fetch_inbound` (mock imaplib), `send_deadline_reminders` (окна 24ч/2ч, дедуп напоминаний) |
| `apps/emails/utf8_smtp.py` | **0%** | Smoke-тест кодирования non-ASCII From |
| `apps/requests/tasks.py` | **48%** | Failure-ветки задач (retry, откат статуса в draft/confirmed) через `CELERY_TASK_ALWAYS_EAGER` + mock, выбрасывающий исключение |
| `apps/requests/services/enricher.py` | **13%** | DaData-обогащение с mock HTTP |
| `apps/requests/serializers.py` | **75%** | Ветки create с lat/lon / geocode-fallback / geocode-failure |

Добавленные в этом PR тесты (`tests/test_export.py`, 12 шт.): XLSX-контент и подсветка лучшего КП, формула итога, PDF-заголовок, IDOR 404 на обоих экспортах и `update_item`, shared-secret generic-вебхука, edge-case «нет КП».

## 4. Экспорт

- **XLSX**: реализован. `GET /api/quotes/competitive_sheet_xlsx/?request_id=` → `competitive_sheet_RFQ-{code}.xlsx`. Колонки: поставщик, цена материалов, доставка, сроки поставки, условия оплаты, итог (формула `=C+D`). Лучшее предложение выделено заливкой `#E6F0FA` + ★. Код: `backend/apps/quotes/exporters.py:build_competitive_sheet_xlsx`.
- **PDF**: реализован. `GET /api/quotes/winner_protocol_pdf/?request_id=` → `winner_protocol_RFQ-{code}.pdf`. Протокол выбора победителя: шапка заявки, таблица КП (победная строка подсвечена), решение + основание, строки подписи. Кириллица — bundled DejaVu TTF (`backend/assets/fonts/`), одинаковый рендер в Windows-dev и Linux-prod. Код: `backend/apps/quotes/exporters.py:build_winner_protocol_pdf`.
- Оба эндпоинта делят `get_competitive_rows()` с JSON competitive sheet (числа идентичны) и ту же проверку владения: без `request_id` → 400, чужая/несуществующая заявка → 404.
- Новые зависимости (обоснование): `openpyxl>=3.1` — генерация XLSX (стандарт, pure-python); `reportlab>=4.0` — генерация PDF (pure-python, без системных библиотек).

## 5. PR

- **Ссылка**: https://github.com/karpukhingennadiy-cpu/stroyzakup/pull/1 (`feature/backend-review` → `dev`, репозиторий `stroyzakup` — см. примечание в п.1)
- **Коммиты**:
  1. `fix(security): close IDOR in update_item, add shared-secret auth to generic inbound webhook`
  2. `fix(celery): pass limit to match task, use valid failure statuses, add 'parsed' status`
  3. `feat(quotes): XLSX/PDF export of competitive sheet and winner protocol`

## Definition of Done

- [x] Code review завершён, отчёт сформирован
- [x] Все тесты проходят (96/96 + 1 skip)
- [x] Экспорт XLSX работает для конкурентного листа
- [x] Экспорт PDF работает для протокола
- [x] PR создан в dev, описание заполнено
- [x] Ни один существующий тест не сломан

## Замечания по процессу

- LLM-промпты (`apps/emails/prompts.py`) не изменялись.
- Модель `Request` изменена только в части choices → миграция `0007_alter_request_status` создана.
- Во время работы ветка в рабочей копии была переключена извне на `feature/frontend-ui` (в дереве есть незакоммиченные frontend-изменения — не мои, в PR не включены). Первый коммит перенесён на `feature/backend-review` без потерь.
- `uv sync` без `--extra dev` сносит dev-зависимости (pytest) — для локальной работы использовать `uv sync --extra dev`.

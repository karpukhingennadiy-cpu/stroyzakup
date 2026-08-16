# OPERATIONS — эксплуатация Минитендер.рф

## Ключи и переменные окружения (.env, backend/.env)

| Переменная | Назначение | Без ключа |
|------------|-----------|-----------|
| `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` | DeepSeek: парсинг заявок, MaterialIntel, переписка (llm_writer), inbound-парсинг цен | Парсинг → regex-fallback; письма → статичные шаблоны; inbound-ответы сохраняются, но цены не извлекаются |
| `DADATA_TOKEN` | Верификация/обогащение компаний | Discovery работает без верификации |
| `YANDEX_GEOCODER_KEY` | Адрес → координаты | Геокодинг возвращает 400; заявку можно создать, подбор — без расстояний |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | SMTP-отправка (Beget) | Письма не уходят (в dev — console backend) |
| `INBOUND_IMAP_HOST/PORT/USER/PASSWORD/FOLDER` | IMAP-ящик входящих ответов (B1) | `fetch_inbound` завершается с сообщением «not configured» |
| `INBOUND_EMAIL_DOMAIN` | Домен reply-адресов `rfq-XXX@...` | default `in.xn--d1abbjawic3ap.xn--p1ai` |
| `INBOUND_EMAIL_WEBHOOK_SECRET` | Проверка подписи Mailgun webhook | Подпись не проверяется (небезопасно для prod) |
| `FRONTEND_URL` | Ссылки в письмах (/quote/{token}, конкурентный лист) | default `http://localhost:3000` — в prod обязательно публичный URL |
| `SECRET_KEY` | Django secret (prod обязателен, без default) | prod не стартует |
| `CELERY_BROKER_URL` | Redis для Celery | dev работает синхронно (sync fallback) |
| `DB_*` | PostgreSQL (prod) | dev — SQLite |

## Деградация без внешних сервисов

Система спроектирована на graceful degradation: полный цикл (заявка → парсинг → подбор → RFQ → КП → конкурентный лист) работает локально без единого ключа — парсер и письма переходят на fallback, карты и верификация отключаются точечно.

## Регулярные задачи (cron / Celery beat)

| Задача | Команда | Периодичность |
|--------|---------|---------------|
| Напоминания поставщикам (B10) | `python manage.py send_deadline_reminders` | каждые 15 мин |
| Входящие ответы (B1) | `python manage.py fetch_inbound` | каждые 5 мин |
| Дедупликация поставщиков (C2) | `python scripts/dedupe_suppliers.py --apply` | по мере роста базы |
| Бэкап БД (prod) | `pg_dump` | ежедневно |

## Письма с needs_review

LLM-письма, нарушившие правила безопасности (обещания, скидки, выход за факты заявки), **не отправляются**. Приглашение остаётся в статусе `pending`, в результатах send_rfq — `needs_review` с причиной. Проверка: Django admin → RfqInvitation / EmailMessage, либо логи (`WARNING ... flagged needs_review`).

## Частые проблемы

| Симптом | Причина | Решение |
|---------|---------|---------|
| Парсинг возвращает fallback-позиции с confidence 0.5 | Нет `LLM_API_KEY` или LLM недоступен | Проверить ключ/сеть; лог `LLM_API_KEY not set` |
| Письма не уходят, status `rfq_failed` | SMTP не настроен / неверный пароль | Проверить `EMAIL_*`; результат `error` в send_rfq results |
| Ссылки в письмах ведут на localhost | `FRONTEND_URL` не выставлен | Выставить публичный URL фронта |
| «database is locked» (SQLite) | Параллельные записи в dev | Ожидаемо под нагрузкой; в prod — PostgreSQL |
| Поставщик не попадает в подбор | moderation_status=rejected; нет товара в ассортименте (product-match rule); нет общих категорий | Проверить статус, `product_keywords`, `SupplierCategory` |
| КП не приходят из писем | IMAP не настроен / письмо не на reply-адрес | `docs/INBOUND_SETUP.md`; проверить `To:` = `rfq-XXX@in...` |
| 429 на /quote/ | Throttle 30/мин | Штатно; перебор токенов блокируется |

## Логи

Backend: Django logger, уровень INFO (prod — `config/settings/logging/`). Ключевые события: `Processed reply`, `RFQ send failed`, `flagged needs_review`, `Auto-discovery failed`.

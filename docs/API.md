# API Reference — Минитендер.рф

Базовый URL: `http://localhost:8000/api`. Авторизация: `Authorization: Bearer <access>` (JWT).
Интерактивная документация: `/api/docs/` (Swagger, drf-spectacular).

## Аутентификация

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/auth/register/` | Регистрация `{email, password, first_name?, last_name?}` |
| POST | `/auth/login/` | JWT `{email, password}` → `{access, refresh}` |
| POST | `/auth/token/refresh/` | Обновление access-токена |
| GET/PATCH | `/auth/me/` | Профиль (вкл. `is_staff` для модерации) |
| POST | `/auth/geocode/` | `{address}` → `{latitude, longitude, city, full_address}`; 400 при пустом/ненайденном адресе |

## Заявки `/requests/`

| Метод | Путь | Описание |
|-------|------|----------|
| GET/POST | `/requests/` | Список (только свои) / создание `{raw_text, comment?, delivery_address?, latitude?, longitude?}` |
| GET/PATCH/DELETE | `/requests/{id}/` | Деталь / обновление (адрес) / удаление. Чужая заявка → 404 |
| POST | `/requests/{id}/parse/` | LLM-парсинг raw_text → позиции. Ответ: заявка + `clarifications[]`. Пустой текст → 422 |
| POST | `/requests/{id}/confirm/` | Подтверждение + автоподбор при наличии адреса |
| POST | `/requests/{id}/update_item/` | `{item_id, spec?, quantity?, is_confirmed...}` — правка позиции (в т.ч. ответы на уточняющие вопросы) |
| GET | `/requests/{id}/items/` | Позиции заявки (с `clarification_question`, `confidence`) |
| POST | `/requests/{id}/match_suppliers/` | `{limit?}` (int 1–100) → `{suppliers[], count, discovered, status}`; каждый поставщик содержит `score_breakdown`, `supplier_type`, `moderation_status` |
| POST | `/requests/{id}/send_rfq/` | `{supplier_ids[]}` (обязателен, иначе 400) → `{results[]}` со статусами `sent`/`skipped`/`error`/`needs_review` |

## Поставщики `/suppliers/`

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/suppliers/` | Фильтры: `search`, `city`, `category`, `moderation_status` |
| POST | `/suppliers/` | Ручное добавление (B5): `{name*, email?, phone?, site?, supplier_type?, address?, categories?[id...]}` → source=manual, verified, автообогащение + геокодинг |
| GET | `/suppliers/categories/` | Список категорий для формы |
| GET | `/suppliers/search_radius/?lat=&lon=&radius=` | Поиск в радиусе (км) |
| POST | `/suppliers/{id}/moderate/` | **staff**: `{status: verified\|rejected\|unverified}` (B4) |
| POST | `/suppliers/bulk_verify/` | **staff**: `{ids[], status}` — массовая модерация |

## КП и конкурентный лист `/quotes/`

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/quotes/` | Только КП по своим заявкам (IDOR закрыт); фильтр `?request_id=` |
| POST | `/quotes/` | Ручное внесение КП |
| GET | `/quotes/competitive_sheet/?request_id=` | Сравнение КП + лучший; без id → 400, чужая/несуществующая → 404 |
| GET | `/quotes/competitive_sheet_xlsx/?request_id=` | Экспорт конкурентного листа в XLSX (поставщик, материалы, доставка, сроки, оплата, итог; лучшее КП выделено); 400/404 как у JSON-версии |
| GET | `/quotes/winner_protocol_pdf/?request_id=` | Протокол выбора победителя в PDF (таблица КП, победитель, основание); 400/404 как у JSON-версии |

## Публичное API (без авторизации)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/public/quote/{token}/` | Форма КП для поставщика. Данных заказчика (email/телефона) нет. Throttle 30/мин → 429 |
| POST | `/public/quote/{token}/` | `{items: [{request_item_id, price>0, is_analog?, brand?}], delivery_cost?, delivery_time?, payment_terms?, comment?}`. Цена ≤0/нечисло/пустой список → 400. Повторная отправка обновляет КП |

## Inbound email webhooks

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/emails/webhook/mailgun/` | Mailgun inbound (HMAC-подпись при заданном `INBOUND_EMAIL_WEBHOOK_SECRET`) |
| POST | `/emails/webhook/inbound/` | Generic JSON webhook (при заданном `INBOUND_GENERIC_WEBHOOK_SECRET` требуется заголовок `X-Webhook-Secret`) |

Альтернатива вебхукам: `python manage.py fetch_inbound` (IMAP-polling, см. `docs/INBOUND_SETUP.md`).

## Management-команды

```bash
python manage.py fetch_inbound              # B1: забрать ответы поставщиков из IMAP-ящика
python manage.py send_deadline_reminders    # B10: напоминания за 24ч/2ч (cron каждые 15 мин)
```

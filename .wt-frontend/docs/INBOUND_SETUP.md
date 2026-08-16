# INBOUND_SETUP — приём ответов поставщиков по email (B1)

Цепочка: поставщик отвечает письмом на `rfq-{reply_code}@in.минитендер.рф` → письмо попадает в систему → создаётся/обновляется КП → LLM извлекает цены из текста → заказчик получает уведомление (B7).

## 1. DNS

```
Тип    Имя   Значение                     Приоритет
MX     in    mx1.beget.com (или ваш MX)   10
TXT    in    v=spf1 include:beget.com ~all
```

`in.минитендер.рф` в punycode: `in.xn--d1abbjawic3ap.xn--p1ai` (уже default в `INBOUND_EMAIL_DOMAIN`).

## 2. Вариант A — IMAP-polling (рекомендуется, проще)

1. Завести почтовый ящик на домене (например `in@минитендер.рф`) и настроить **catch-all** или алиасы `rfq-*@in.минитендер.рф` → этот ящик.
2. В `backend/.env`:

```
INBOUND_IMAP_HOST=imap.beget.com
INBOUND_IMAP_PORT=993
INBOUND_IMAP_USER=in@минитендер.рф
INBOUND_IMAP_PASSWORD=...
INBOUND_IMAP_FOLDER=INBOX
```

3. Cron каждые 5 минут:

```
*/5 * * * * cd /path/backend && uv run python manage.py fetch_inbound
```

Команда читает UNSEEN-письма, находит `rfq-XXX@` в To/Cc, вызывает `process_inbound_email_reply` и помечает письмо прочитанным. `--dry-run` — без обработки, `--limit N` — ограничение пачки.

## 3. Вариант B — вебхуки (уже реализованы)

- **Mailgun**: Routes → `match_recipient("rfq-.*@in.минитендер.рф")` → forward на `https://app.минитендер.рф/api/emails/webhook/mailgun/`; задать `INBOUND_EMAIL_WEBHOOK_SECRET` для проверки HMAC-подписи.
- **Generic JSON**: POST на `/api/emails/webhook/inbound/` с `{envelope: {to: [...], from}, subject, text, html}`.

## 4. Что происходит с письмом

1. `parse_reply_address` извлекает `reply_code` из адресата.
2. `process_inbound_email_reply`: EmailMessage (inbound) + Quote (status=received), приглашение → `replied`.
3. `inbound_parser.extract_prices_to_quote`: LLM извлекает цены/условия → QuoteItem. Если письмо — вопрос без цен, llm_writer генерирует ответ-разъяснение (только факты заявки; needs_review → не отправляется).
4. `notify_customer_quote_received` — письмо заказчику со ссылкой на конкурентный лист.

## 5. Проверка end-to-end

1. Отправить RFQ реальному тестовому адресу (send_rfq).
2. Ответить на письмо с текстом: «Цемент М500 — 380 руб/меш, доставка 5000 руб, 3 дня».
3. Прогнать `fetch_inbound` (или дождаться cron).
4. В `/lk/requests/{id}/competitive` — КП с позициями и доставкой.

Fallback при любых сбоях: поставщик заполняет КП по ссылке из письма, либо заказчик вносит КП вручную (POST /quotes/).

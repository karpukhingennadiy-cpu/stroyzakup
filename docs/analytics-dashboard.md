# PostHog Analytics Dashboard

## Обзор

PostHog (self-hosted) развёрнут через `docker-compose.analytics.yml` и интегрирован с backend (Django + Celery) и frontend (Next.js).

## Воронка закупок (Funnel)

Настроена в PostHog UI как 4-шаговая воронка:

| Шаг | Событие | Источник |
|-----|---------|----------|
| 1 | `rfq_created` | Backend (Django signal) |
| 2 | `supplier_matched` | Backend (Django signal) |
| 3 | `quote_received` | Backend (Django signal) |
| 4 | `winner_selected` | Backend (Django signal) |

### Дополнительные frontend-события

| Событие | Триггер |
|---------|---------|
| `$pageview` | Автоматически (PostHog JS) |
| `competitive_sheet_viewed` | Просмотр конкурентного листа |
| `protocol_downloaded` | Скачивание XLSX или PDF |

## Настройка Funnel в PostHog

1. Открыть PostHog UI (`http://localhost:8001` при локальном запуске)
2. Перейти в **Insights → Funnels**
3. Добавить шаги:
   - `rfq_created`
   - `supplier_matched`
   - `quote_received`
   - `winner_selected`
4. Фильтр по времени: 30 дней
5. Сохранить как "Закупочная воронка"

## 152-ФЗ / GDPR Compliance

- **Consent banner**: opt-in по умолчанию, пользователь должен явно согласиться
- **Анонимизация**: `distinct_id` = SHA-256 хеш user_id, без PII
- **Хранение**: self-hosted на собственной инфраструктуре

## Переменные окружения

```env
POSTHOG_API_KEY=<your-project-api-key>
POSTHOG_HOST=http://localhost:8001
NEXT_PUBLIC_POSTHOG_KEY=<your-project-api-key>
NEXT_PUBLIC_POSTHOG_HOST=http://localhost:8001
```

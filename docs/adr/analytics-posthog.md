# ADR-006: Внедрение PostHog (self-hosted) для продуктовой аналитики

**Статус**: Принято (Accepted)  
**Дата**: 2026-08-04  
**Автор**: G6 — Product Analytics Engineer  
**Контекст**: Минитендер.рф v2.1.0, ветка `feature/analytics`  

---

## 1. Резюме (Summary)

Внедряем **PostHog (self-hosted)** как единую систему продуктовой аналитики для отслеживания воронки закупок, поведения пользователей и когортного анализа. Решение обеспечивает полный контроль над данными (152-ФЗ), готовые воронки/когорты из коробки и нативные SDK для Django + Next.js.

---

## 2. Контекст и проблема (Context & Problem)

### Текущее состояние
- **Нет системы аналитики** — события не отслеживаются, воронка не измеряется.
- **Нет event tracking** — неизвестно, как пользователи проходят путь от заявки до протокола.
- Дашборд в Kimi Work существует, но данные приходят из API, не из analytics-хранилища.

### Бизнес-воронка (8 шагов)
1. Пользователь создаёт заявку (RFQ) со списком материалов
2. LLM (DeepSeek) парсит материалы
3. Система ищет поставщиков (Haversine, PostGIS)
4. Отправка RFQ 5 поставщикам (email)
5. Сбор КП (коммерческих предложений)
6. Формирование конкурентного листа
7. Выбор победителя
8. Генерация протокола (PDF/XLSX)

### Цели
- Измерить conversion rate на каждом шаге воронки.
- Понять, где пользователи «отваливаются».
- Провести когортный анализ (регионы, категории материалов, клиенты).
- Построить дашборды: daily / weekly / monthly.
- Соблюсти 152-ФЗ РФ (хранение данных на территории РФ, согласие пользователей).

---

## 3. Рассмотренные альтернативы (Alternatives Considered)

| Инструмент | Плюсы | Минусы | Вердикт |
|------------|-------|--------|---------|
| **PostHog (self-hosted)** | Open-source; SQL-запросы; воронки и когорты из коробки; полный контроль данных; SDK для Django/Next.js; HIPAA-ready | Требует инфраструктуры (Docker); начальная настройка ~1-2 дня | **✅ Принято** |
| **ClickHouse + Grafana** | Максимальная производительность; гибкость SQL; self-hosted | Нет готовых воронок/когорт — нужно писать весь UI; высокая трудоёмкость | ❌ Отклонено — дорого в разработке, нет готовых фич |
| **Yandex.Metrica** | Простая интеграция; привычный для РФ рынка | SaaS (данные на серверах Яндекса); ограниченные SQL-возможности; санкционные риски для B2B | ❌ Отклонено — риски 152-ФЗ и суверенности данных |
| **Mixpanel** | Мощные воронки; хорошая документация | SaaS; дорого; данные за рубежом; риски для РФ | ❌ Отклонено — не соответствует требованию 152-ФЗ |

### Критерии выбора
1. **152-ФЗ / суверенность данных** — данные должны храниться на нашей инфраструктуре.
2. **Готовые воронки и когорты** — не писать свой UI с нуля.
3. **SDK для Django + Next.js** — минимальная трудоёмкость интеграции.
4. **SQL-доступ к сырым данным** — возможность кастомной аналитики.
5. **Self-hosted / on-premise** — контроль над обновлениями и масштабированием.

---

## 4. Решение (Decision)

**Использовать PostHog (self-hosted) через Docker Compose.**

### Архитектура

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Docker Compose Stack                            │
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │   PostHog    │    │   PostHog    │    │   PostHog Workers        │  │
│  │   Web        │    │   Plugin     │    │   (Celery beat)          │  │
│  │   (UI + API) │    │   Server     │    │                          │  │
│  └──────┬───────┘    └──────┬───────┘    └────────────┬─────────────┘  │
│         │                   │                         │                │
│  ┌──────┴───────────────────┴─────────────────────────┴───────────┐   │
│  │                     PostgreSQL (analytics)                     │   │
│  │                    + ClickHouse (events)                       │   │
│  └────────────────────────────────────────────────────────────────┘   │
│         ▲                                                               │
│         │ HTTP / gRPC                                                   │
│  ┌──────┴──────────────────────────────────────────────────────────┐   │
│  │                         Redis (broker)                           │   │
│  │              (уже существует для Celery backend)                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
         ▲
         │
    ┌────┴─────────────────────────────────────────────────────────────┐
    │                         Applications                              │
    │  ┌─────────────┐         ┌─────────────────┐                     │
    │  │  Frontend   │         │     Backend     │                     │
    │  │  Next.js 15 │         │  Django 5.1 +   │                     │
    │  │  posthog-js │◄────────┤  DRF + Celery   │                     │
    │  │  (capture)  │         │  posthog-python │                     │
    │  └─────────────┘         └─────────────────┘                     │
    └──────────────────────────────────────────────────────────────────┘
```

### Инфраструктура (Docker Compose)

PostHog разворачивается как **отдельный сервис** в существующем `docker-compose.yml` (или `docker-compose.analytics.yml` overlay):

- `posthog-web` — UI и API (порт 8000 внутри сети, проксируется через Nginx)
- `posthog-plugin-server` — обработка плагинов и real-time событий
- `posthog-worker` — фоновые задачи (Celery beat)
- `posthog-clickhouse` — хранилище событий (колоночная БД, высокая производительность)
- `posthog-postgres` — отдельный PostgreSQL для PostHog metadata (не путать с основной БД приложения)
- `posthog-redis` — можно использовать **существующий Redis** (уже есть в стеке для Celery)

> **Примечание**: PostHog предоставляет официальный `docker-compose.yml` для self-hosted развёртывания. Будем использовать его как базу, адаптировав под наши сервисы.

---

## 5. Событийная модель (Event Schema)

### 5.1 Frontend-события (posthog-js)

| Событие | Триггер | Свойства |
|---------|---------|----------|
| `$pageview` | Авто (PostHog) | `url`, `referrer`, `utm_source`, `utm_medium` |
| `competitive_sheet_viewed` | Просмотр конкурентного листа | `request_id`, `user_id`, `items_count` |
| `protocol_downloaded` | Скачивание протокола | `request_id`, `format` (pdf / xlsx) |
| `rfq_form_started` | Начало заполнения формы RFQ | `step` (1/2/3) |
| `rfq_form_submitted` | Отправка формы RFQ | `items_count`, `category`, `has_file` |

### 5.2 Backend-события (posthog-python + Celery)

| Событие | Триггер | Свойства | Async |
|---------|---------|----------|-------|
| `rfq_created` | Создание заявки (signal `post_save` на Request) | `user_id`, `items_count`, `category`, `region`, `estimated_budget` | ✅ Celery task |
| `supplier_matched` | Подбор поставщиков | `request_id`, `suppliers_count`, `radius_km`, `category` | ✅ Celery task |
| `quote_received` | Получение КП от поставщика | `request_id`, `supplier_id`, `price`, `delivery_days`, `currency` | ✅ Celery task |
| `winner_selected` | Выбор победителя | `request_id`, `supplier_id`, `total_price`, `savings_vs_max` | ✅ Celery task |
| `rfq_email_sent` | Отправка RFQ поставщику | `request_id`, `supplier_id`, `email`, `channel` (email) | ✅ Celery task |

### 5.3 Воронка (Funnel)

```
Заявка создана (rfq_created)
    ↓ conversion: ?
RFQ отправлен поставщикам (rfq_email_sent)
    ↓ conversion: ?
КП получено ≥1 (quote_received)
    ↓ conversion: ?
Конкурентный лист просмотрен (competitive_sheet_viewed)
    ↓ conversion: ?
Победитель выбран (winner_selected)
    ↓ conversion: ?
Протокол скачан (protocol_downloaded)
```

---

## 6. Интеграция

### 6.1 Frontend (Next.js 15)

**Пакет**: `posthog-js`  
**Инициализация**: в `app/layout.tsx` (или `_app.tsx` для Pages Router) через `PostHogProvider`.

```typescript
// lib/analytics.ts
import posthog from 'posthog-js';

export const initPostHog = () => {
  if (typeof window !== 'undefined') {
    posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
      capture_pageview: true,        // автоматические $pageview
      capture_pageleave: true,       // время на странице
      persistence: 'localStorage',   // cookie-less при необходимости
      loaded: (posthog) => {
        if (process.env.NODE_ENV === 'development') posthog.debug();
      },
    });
  }
};
```

**Отправка кастомных событий**:
```typescript
posthog.capture('protocol_downloaded', {
  request_id: rfqId,
  format: 'pdf',
});
```

### 6.2 Backend (Django 5.1 + DRF)

**Пакет**: `posthog-python`  
**Установка**: `pip install posthog` (добавить в `pyproject.toml`).

**Инициализация** (`backend/config/posthog.py`):
```python
import posthog
from django.conf import settings

posthog.api_key = settings.POSTHOG_API_KEY
posthog.host = settings.POSTHOG_HOST
```

**Async tracking через Celery** (`backend/apps/analytics/tasks.py`):
```python
from celery import shared_task
import posthog

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def track_event(self, event: str, distinct_id: str, properties: dict):
    """Асинхронная отправка события в PostHog.
    
    Не блокирует основной поток запроса.
    При ошибке — retry с экспоненциальным backoff.
    """
    try:
        posthog.capture(
            distinct_id=distinct_id,
            event=event,
            properties=properties,
        )
    except Exception as exc:
        raise self.retry(exc=exc)
```

**Интеграция с Django signals** (`backend/apps/requests/signals.py`):
```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Request
from apps.analytics.tasks import track_event

@receiver(post_save, sender=Request)
def on_request_created(sender, instance, created, **kwargs):
    if created:
        track_event.delay(
            event='rfq_created',
            distinct_id=str(instance.user_id),
            properties={
                'items_count': instance.items.count(),
                'category': instance.category,
                'region': instance.region,
            }
        )
```

> **Важно**: `track_event.delay(...)` возвращает управление мгновенно. Celery worker обрабатывает отправку в фоне. Backend не замедляется.

---

## 7. Требования 152-ФЗ / GDPR

### 7.1 Cookie Consent Banner

- Добавить **баннер согласия** на сбор данных при первом визите.
- PostHog **не инициализируется** до получения согласия (opt-in).
- При отказе — отключить capture, использовать только анонимные `$pageview` (без user_id).

```typescript
// Псевдокод consent-логики
if (userConsent === 'granted') {
  posthog.opt_in_capturing();
} else {
  posthog.opt_out_capturing();
}
```

### 7.2 Анонимизация

- `distinct_id` — хешированный UUID пользователя (не email, не телефон).
- IP-адреса — хранить только первые 3 октета (`192.168.1.xxx`) или полностью обфусцировать.
- Не передавать PII в properties (имена, телефоны, email).

### 7.3 Хранение и удаление данных

- **Хранение**: PostHog self-hosted на серверах проекта (территория РФ при production deploy).
- **Срок хранения**: 24 месяца для событий (настраивается в PostHog TTL).
- **Право на удаление**: реализовать endpoint `/api/analytics/delete-data/` для полного удаления событий по `distinct_id` (по запросу пользователя).

### 7.4 Договор обработки (опционально)

- При наличии юридического лица — оформить договор с ООО «Постхог» (для PostHog Cloud) **не требуется**, т.к. используется self-hosted версия. Данные не покидают инфраструктуру проекта.

---

## 8. План внедрения (Roadmap)

### Этап 1: Инфраструктура (Оценка: 1-2 дня)

| Задача | Описание | DoD |
|--------|----------|-----|
| 1.1 Docker Compose overlay | Добавить `docker-compose.analytics.yml` с сервисами PostHog | `docker compose -f docker-compose.analytics.yml up` запускается без ошибок |
| 1.2 Nginx routing | Настроить reverse proxy для `analytics.minitender.rf` | UI PostHog доступен по домену |
| 1.3 Environment variables | Добавить `POSTHOG_API_KEY`, `POSTHOG_HOST` в `.env` | Переменные прокидываются в backend + frontend |

### Этап 2: Backend SDK + Tracking (Оценка: 2-3 дня)

| Задача | Описание | DoD |
|--------|----------|-----|
| 2.1 Установка SDK | `pip install posthog`, обновить `pyproject.toml` | `posthog` импортируется без ошибок |
| 2.2 Celery tasks | Создать `apps/analytics/tasks.py` с `track_event` | Таска выполняется, событие доходит в PostHog |
| 2.3 Django signals | Подключить signals: `rfq_created`, `supplier_matched`, `quote_received`, `winner_selected` | Все 4 события отправляются async |
| 2.4 Миграции | Создать `apps/analytics` Django-app | App зарегистрирован в `INSTALLED_APPS` |

### Этап 3: Frontend SDK + Tracking (Оценка: 1-2 дня)

| Задача | Описание | DoD |
|--------|----------|-----|
| 3.1 Установка SDK | `npm install posthog-js` | Пакет в `package.json` |
| 3.2 Provider | Добавить `PostHogProvider` в `app/layout.tsx` | `$pageview` автоматически capture |
| 3.3 Custom events | `competitive_sheet_viewed`, `protocol_downloaded`, `rfq_form_*` | События видны в PostHog Live Events |
| 3.4 Consent banner | Компонент `<CookieConsent />` | Баннер отображается, opt-in/opt-out работает |

### Этап 4: Воронки и когорты в PostHog (Оценка: 1-2 дня)

| Задача | Описание | DoD |
|--------|----------|-----|
| 4.1 Funnel dashboard | Создать воронку в PostHog UI | Conversion rate на каждом шаге виден |
| 4.2 Cohort analysis | Когорты: по регионам, категориям, новые/returning | Графики retention построены |
| 4.3 Time-to-quote метрика | SQL-запрос: среднее время от `rfq_created` до `quote_received` | Метрика отображается в dashboard |

### Этап 5: Дашборды + Kimi Work интеграция (Оценка: 2-3 дня)

| Задача | Описание | DoD |
|--------|----------|-----|
| 5.1 Daily dashboard | Активность, новые заявки, КП | Дашборд обновляется ежедневно |
| 5.2 Weekly dashboard | Воронка, conversion rate, top поставщики | Авто-рассылка или widget |
| 5.3 Monthly dashboard | Когорты, ARPU, retention | Авто-рассылка или widget |
| 5.4 Kimi Work Widget | Интеграция с существующим Canvas (опционально) | Widget показывает метрики из PostHog API |

### Этап 6: Автоотчёты (Оценка: 1-2 дня)

| Задача | Описание | DoD |
|--------|----------|-----|
| 6.1 Scheduled reports | Celery beat задача: отправка weekly report на email | Email с PDF-отчётом приходит каждый понедельник |
| 6.2 Kimi Work Automation | Автоматический дашборд через Blueprint Automation | Canvas обновляется по расписанию |

---

## 9. Зависимости и риски

### Зависимости

| Зависимость | Влияние | Митигация |
|-------------|---------|-----------|
| **Production deploy** | Для реальных данных нужен production окружение | Разработка и тестирование на dev/staging; production — после deploy |
| **Redis** | Celery брокер для async tracking | ✅ Уже есть в стеке (Redis 7) |
| **Celery** | Async task processing | ✅ Уже есть в стеке (Celery 5.6.3) |
| **Nginx / домен** | Доступ к PostHog UI | Настроить `analytics.minitender.rf` в DNS |

### Риски

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Перегрузка Redis сообщениями от tracking | Средняя | Среднее | Rate limiting на `track_event`; batch-отправка событий |
| Рост ClickHouse (big data) | Средняя | Высокое | Настроить TTL 24 мес; архивация старых событий |
| Сложность self-hosted PostHog | Средняя | Среднее | Использовать официальный `docker-compose.yml`; документация PostHog |
| Отсутствие cookie consent (юридический риск) | Высокая | Высокое | Этап 3.4 — обязательный; блокирует production release |

---

## 10. Метрики успеха (Success Metrics)

- [ ] Все 7 ключевых событий отслеживаются (4 backend + 3 frontend).
- [ ] Conversion rate воронки измеряется на каждом шаге.
- [ ] Когортный анализ доступен по регионам и категориям.
- [ ] Daily/weekly/monthly дашборды работают без ручного обновления.
- [ ] Cookie consent баннер развёрнут и функционирует.
- [ ] Async tracking не увеличивает p95 latency API > 5%.

---

## 11. Последствия (Consequences)

### Положительные
- Полный контроль над данными (152-ФЗ).
- Готовые воронки, когорты, retention без разработки UI.
- SQL-доступ к сырым данным для кастомной аналитики.
- Единая система для product и marketing аналитики.

### Отрицательные / Накладные расходы
- +1 сервис в Docker Compose (+ ClickHouse, + Postgres для PostHog).
- +~2-4 GB RAM на сервере для стабильной работы PostHog.
- Необходимость мониторинга ClickHouse дискового пространства.
- Cookie consent баннер — дополнительный UI-компонент.

---

## 12. Ссылки (References)

- [PostHog Self-Hosted Docs](https://posthog.com/docs/self-host)
- [PostHog Django Integration](https://posthog.com/docs/libraries/django)
- [PostHog Next.js Integration](https://posthog.com/docs/libraries/next-js)
- [PostHog Funnels](https://posthog.com/docs/product-analytics/funnels)
- [PostHog Cohorts](https://posthog.com/docs/product-analytics/cohorts)
- [152-ФЗ "О персональных данных"](http://www.consultant.ru/document/cons_doc_LAW_61801/)
- PostHog Docker Compose: `https://github.com/PostHog/posthog/blob/master/docker-compose.yml`

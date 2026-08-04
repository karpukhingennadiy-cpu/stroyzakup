# Мониторинг Минитендер (G4)

> Prometheus + Grafana + экспортеры. Контур поднимается локально на этом ПК
> рядом с production-контуром (`docker-compose.prod.yml`).

## Состав контура

| Сервис | Образ | Порт (localhost) | Назначение |
|--------|-------|------------------|------------|
| prometheus | `prom/prometheus:v2.54.1` | 9090 | Сбор и хранение метрик (retention 30d) |
| grafana | `grafana/grafana:11.2.0` | 3001 | Дашборды (прологиниться: admin / `GRAFANA_ADMIN_PASSWORD`) |
| node-exporter | `prom/node-exporter:v1.8.2` | 9100 | CPU / RAM / диск хоста |
| postgres-exporter | `prometheuscommunity/postgres-exporter:v0.15.0` | — | Метрики PostgreSQL |
| nginx-exporter | `nginxinc/nginx-prometheus-exporter:1.4.0` | — | Nginx stub_status → Prometheus |
| celery-exporter | `danihodovic/celery-exporter:0.10.9` | — | Очереди Celery (broker Redis) |

Метрики backend собираются с endpoint `/metrics` (django-prometheus, порт 8000, внутри сети).

## Запуск

```bash
# 1. Production-контур (создаёт сеть minitender-net)
docker compose -f docker-compose.prod.yml up -d --build

# 2. Контур мониторинга
docker compose -f docker-compose.monitoring.yml up -d

# 3. Проверка
curl http://localhost:9090/-/ready     # Prometheus ready
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[].health'  # все "up"
start http://localhost:3001            # Grafana (admin / GRAFANA_ADMIN_PASSWORD)
```

Остановка: `docker compose -f docker-compose.monitoring.yml down` (данные сохраняются в томах `prometheus_data`, `grafana_data`).

## Переменные окружения (.env.production)

| Переменная | Назначение |
|-----------|------------|
| `GRAFANA_ADMIN_USER` | Логин админа Grafana (по умолчанию `admin`) |
| `GRAFANA_ADMIN_PASSWORD` | Пароль админа Grafana (**обязательна**, без неё Grafana не стартует) |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | Используются postgres-exporter для подключения к БД |
| `POSTHOG_HOST` / `POSTHOG_PERSONAL_API_KEY` | Только для дашборда воронки (data source PostHog) |

## Дашборды (папка «Минитендер» в Grafana)

Дашборды провижинируются автоматически из `deploy/monitoring/dashboards/`.

| Дашборд | Содержание |
|---------|-----------|
| **Обзор (health, rate, 5xx)** | Статус backend/nginx/PostgreSQL (up), rate запросов по view, доля и поток ошибок 5xx, latency p95 |
| **Инфраструктура** | CPU и RAM хоста, свободное место на диске, подключения и транзакции PostgreSQL, соединения и RPS nginx |
| **Очереди Celery** | Статус celery-exporter, длина очередей, задачи по статусам (tasks/s) |
| **Воронка (PostHog)** | Объёмы событий `rfq_created → supplier_matched → quote_received → winner_selected` за 30 дней |

### Дашборд воронки — важно

Дашборд «Воронка (PostHog)» требует Grafana-плагин **PostHog data source**
(`grafana-posthog-datasource`). До установки плагина его панели показывают
ошибку datasource — это ожидаемо. Установка:

```bash
# Вариант 1: через админку Grafana → Administration → Plugins → "PostHog"
# Вариант 2: переменная окружения для сервиса grafana
GF_INSTALL_PLUGINS=grafana-posthog-datasource
```

Каноническая воронка с конверсиями между шагами настраивается в PostHog UI
(Insights → Funnels) — см. `docs/analytics-dashboard.md`.

## Как читать дашборды

- **Backend health (up)** — 1/UP зелёный: `/metrics` отвечает. Если 0/DOWN —
  проверить `docker compose -f docker-compose.prod.yml ps` и логи backend.
- **Доля 5xx** — зелёный < 1 %, оранжевый 1–5 %, красный > 5 %. При росте
  смотреть панель «Ошибки 5xx» (какие статусы) и логи backend.
- **Latency p95** — норма до ~0.5 с для API-эндпоинтов; рост без роста
  трафика = проблема в БД или внешних API (DeepSeek/DaData).
- **Свободное место на диске** — красный порог < 10 ГБ. PostHog и Prometheus
  активно пишут на диск; следить еженедельно.
- **Задач в очереди** — устойчивый рост = celery-worker не справляется или
  упал; проверить `docker compose -f docker-compose.prod.yml logs celery-worker`.

## Структура файлов

```
docker-compose.monitoring.yml          # контур мониторинга
deploy/monitoring/
  prometheus.yml                       # scrape-цели
  grafana/provisioning/
    datasources/datasources.yml        # Prometheus + PostHog
    dashboards/dashboards.yml          # провайдер дашбордов
  dashboards/
    minitender-overview.json           # health / rate / 5xx / latency
    minitender-infra.json              # CPU / RAM / диск / БД / nginx
    minitender-celery.json             # очереди Celery
    minitender-funnel.json             # воронка PostHog
```

## Сети

Prod-контур и контур мониторинга связаны именованной сетью `minitender-net`
(объявлена в `docker-compose.prod.yml`, подключена как `external` в
`docker-compose.monitoring.yml`). Порты 9090/3001/9100 проброшены на
localhost только для доступа администратора с этого ПК; наружу (роутер)
пробрасывать их **не нужно** — внешний доступ только к 80/443 (см.
`orchestrator/docs/EXTERNAL_ACCESS.md`).

## Следующие шаги (за рамками G4 MVP)

- Алертинг: Alertmanager + правила (5xx > 5 %, диск < 10 ГБ, backend down > 2 мин) → email/Telegram.
- Логи: Loki + promtail в той же Grafana.
- Uptime-чек `/api/health/` извне (через blackbox-exporter или внешний сервис).

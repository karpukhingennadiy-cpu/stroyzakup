# Релизный анализ — Минитендер.рф (StroyZakup)

**Дата:** 2026-08-16 | **Ветка:** dev | **Теги:** v0.2.0 … v2.3.0 (9 релизов на GitHub)
**Цель:** подвести проект к продакшен-релизу (v2.4.0)

---

## 1. Сводка состояния

| Слой | Состояние | Проверка |
|---|---|---|
| Backend Django 5 + DRF + Celery | OK Работает | 182 passed, 1 skipped (pytest, 142с) |
| Frontend Next.js 16 + Tailwind 4 | OK Работает | next build — успех (11 маршрутов), tsc чистый |
| Редизайн (REDESIGN_TASK) | OK Применён | v2.3.0: токены, лендинг, ЛК, мастер, поставщики, auth |
| CI/CD | ВНИМАНИЕ Файлы есть, запуск не подтверждён | 4 workflow (backend+PostGIS, frontend, docker, deploy-staging) |
| Деплой-контур | OK Проверен локально | docker-compose.prod.yml: 6 сервисов, smoke 200 |
| Мониторинг | ВНИМАНИЕ Частично | Prometheus/Grafana (monitoring.yml), PostHog — ключ не задан |
| Документация | ВНИМАНИЕ Частично | README/API/QA ок; CHANGELOG устарел |
| Релизы GitHub | OK 9 шт | v0.2.0 → v2.3.0 |

## 2. Пробелы до релиза (по приоритетам)

### P0 — блокеры релиза
| # | Что | Где | Статус |
|---|---|---|---|
| 1 | Версии не синхронизированы: package.json/pyproject = 0.1.0, теги = v2.3.0 | frontend/package.json, backend/pyproject.toml | Нужно → 2.4.0 |
| 2 | main отстаёт от dev на 17 коммитов (редизайн, B9, security, тесты) | git | merge dev → main |
| 3 | CHANGELOG.md не обновлён после v2.0.0 (нет 2.1/2.2/2.3) | CHANGELOG.md | Дописать |
| 4 | Бэкапы БД отсутствуют — нет скрипта pg_dump + cron | scripts/ | Создать + cron |
| 5 | CI не подтверждён — RELEASE_CHECKLIST «GitHub Actions CI» не отмечен | .github/workflows/ | Прогнать/починить |
| 6 | PostHog ключ не задан (NEXT_PUBLIC_POSTHOG_KEY «not set» в логах) | .env.production | Добавить |

### P1 — важно для качества
| # | Что | Детали |
|---|---|---|
| 7 | Пагинация поставщиков | Таблица поставщиков без пагинации (в отличие от заявок) |
| 8 | Lighthouse-аудит | Цель: 90+ Perf, 100 A11y (неделя 3 REDESIGN_TASK) |
| 9 | Проверка адаптива 375px после редизайна | Мастер: sticky bottom; таблицы: горизонтальный скролл |
| 10 | README: скриншоты «до/после» редизайна | kimi-redesign/screens/after/ |
| 11 | Google OAuth — заглушка без бэкенда | P3 по ТЗ, пометить «планируется» |

### P2 — серверное (вне кода, по GO_LIVE_CHECKLIST)
| # | Что | Где |
|---|---|---|
| 12 | TLS Let's Encrypt (минитендер.рф + app.минитендер.рф) | certbot + nginx 443 |
| 13 | MX in.минитендер.рф + catch-all (inbound КП) | Beget, docs/INBOUND_SETUP.md |
| 14 | DKIM (старый ключ скомпрометирован) | почтовый провайдер |
| 15 | USE_CELERY=true, ALLOWED_HOSTS, FRONTEND_URL, ротация SECRET_KEY | server .env |
| 16 | Cron: reminders (*/15м), fetch_inbound (*/5м), pg_dump (день, 14 дней) | сервер |
| 17 | Smoke прод: health, логин, заявка, RFQ на тестовый ящик | сервер |
| 18 | Sentry/логирование ошибок | опционально (Prometheus есть) |

## 3. План к релизу v2.4.0

### Шаг 1 — Код (P0, ~1 сессия)
1. Поднять версии: frontend 0.1.0 → 2.4.0, backend 0.1.0 → 2.4.0
2. Дописать CHANGELOG.md (v2.1.0, v2.2.0, v2.3.0, 2.4.0-unreleased)
3. Скрипт бэкапа scripts/backup_db.sh (pg_dump + retention 14 дней)
4. PostHog: NEXT_PUBLIC_POSTHOG_KEY в .env.production (ключ у пользователя)
5. Пагинация поставщиков (10/стр, по образцу заявок)
6. Прогнать CI: gh run list, починить workflow при падении

### Шаг 2 — Ветки и релиз
1. git checkout main && git merge dev (17 коммитов)
2. Тег v2.4.0 + gh release create v2.4.0 с нотами
3. Обновить RELEASE_CHECKLIST на GitHub (отметить выполненное)

### Шаг 3 — Сервер (нужен доступ/пользователь)
1. TLS, MX, DKIM, env, cron — по GO_LIVE_CHECKLIST (п.12-18)
2. Smoke-тест прод-URL

## 4. Риски
- PostHog-ключ: без него аналитика (KC-03) не работает — метрики конверсии не увидим
- Inbound-почта: без MX/catch-all поставщики не смогут отвечать письмом (ключевая фича)
- Бэкапы: без pg_dump потеря данных при инциденте
- CI: если workflow не проходили — возможны сюрпризы при merge

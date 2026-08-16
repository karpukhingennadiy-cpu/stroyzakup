# GO_LIVE_CHECKLIST — выход в продакшен (B8)

Дата обновления: 2026-07-31.

## Контур (проверено локально в Docker, 2026-07-31)

- [x] `docker-compose.prod.yml` поднимает 6 сервисов: db (PostGIS), redis, backend (gunicorn), celery-worker, frontend, nginx
- [x] Миграции на PostgreSQL в контейнере — все применены
- [x] Демо-данные перенесены (933 объекта: 192 поставщика, 92 заявки, 9 пользователей)
- [x] Smoke: `GET /api/health/` → 200 через nginx; `POST /api/auth/login/` → 200, JWT выдан; фронт отдаётся на :80
- [x] Найденные при сборке дефекты исправлены: `ENV` до `FROM` в backend/Dockerfile, `.dockerignore` (venv попадал в контекст), GDAL/PostGIS убраны из prod (координаты — FloatField), DB-креды и API-ключи проброшены через env, `CMD` в frontend/Dockerfile — валидный JSON, `node_modules` в runner
- [x] Тесты на PostgreSQL: 84/84 (`config.settings.pgtest`)
- [x] `/api/health/` endpoint для healthcheck'ов

## Перед выкаткой на сервер (выполняется на сервере)

- [ ] `ALLOWED_HOSTS` — только реальные домены (убрать localhost из env сервера)
- [ ] `FRONTEND_URL=https://app.минитендер.рф` — ссылки в письмах
- [ ] `SECURE_SSL_REDIRECT=true` в server .env (локально false для smoke)
- [ ] TLS: Let's Encrypt (certbot) для минитендер.рф и app.минитендер.рф; `nginx.conf` — server 443 + редирект 80→443
- [ ] MX `in.минитендер.рф` + catch-all ящик (см. `docs/INBOUND_SETUP.md`) — inbound-ответы поставщиков
- [ ] `USE_CELERY=true` — асинхронный parse/match/send_rfq через Redis (B2)
- [ ] Cron: `send_deadline_reminders` (*/15 мин), `fetch_inbound` (*/5 мин), `pg_dump` бэкап (ежедневно, хранение 14 дней)
- [ ] `CSRF_TRUSTED_ORIGINS` / `CORS_ALLOWED_ORIGINS` — прод-домены
- [ ] Ротация SECRET_KEY и паролей БД; `.env` только на сервере (не в git)
- [ ] Smoke prod-URL: health, логин, создание заявки, RFQ на тестовый ящик

## После выкатки

- [ ] Мониторинг логов: `needs_review` письма, ошибки SMTP, ошибки LLM
- [ ] Дедупликация поставщиков после первых discovery (`scripts/dedupe_suppliers.py --apply`)

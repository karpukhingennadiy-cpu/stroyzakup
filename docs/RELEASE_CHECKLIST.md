# Release Checklist - Minitender

- [x] Migrations after model fixes
- [x] Secrets in .env (python-decouple)
- [x] CORS_ALLOWED_ORIGINS configured
- [x] DEFAULT_FROM_EMAIL and EMAIL_BACKEND
- [x] CELERY_BROKER_URL + result_backend
- [x] pytest (31 tests)
- [x] npm run build (11 pages)
- [ ] GitHub Actions CI
- [x] /api/health/ endpoint
- [x] SECURE_SSL_REDIRECT + HSTS in prod
- [ ] HTTPS via certbot
- [ ] New DKIM key (old compromised)
- [ ] Monitoring (Sentry)
- [ ] DB backups (pg_dump cron)
- [ ] Logging (ELK / journald)

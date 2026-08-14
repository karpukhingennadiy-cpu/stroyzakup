# Аудит проекта — Минитендер.рф (Stroyzakup)

> Дата аудита: 14.08.2026
> Область: backend (Django 5.1 + DRF + Celery), frontend (Next.js 16 + React 19 + Tailwind 4), инфраструктура (Docker Compose, Nginx, systemd), тесты.
> Метод: чтение исходного кода, проверка конфигурации/деплоя, сопоставление с ранее известными проблемами (matcher/email, websearch, geocoder, публичное КП, assistant, Celery).
> Файлы не изменялись.

Статус-флоу заявки (эталон из моделей и миграций):
`draft → parsing → parsed → confirmed → matching → matched → rfq_sent → collecting_quotes → ready → completed` (+ `rfq_failed`, `cancelled`).

---

## Критические (P0)

1. **[frontend/app/lk/requests/new/page.tsx:256-259 + backend/apps/requests/serializers.py:24-36]** — Точка доставки из шага 2 мастера **не сохраняется**. Мастер шлёт `PATCH /requests/{id}/` с `delivery_address/latitude/longitude`, но `RequestSerializer` (используется для update) объявляет только `delivery_address` (write_only) и не имеет `update()`-оверрайда, а `latitude/longitude` вообще не являются полями сериализатора → DRF молча их игнорирует (`setattr` на несуществующий атрибут модели). Последствия: `req.address` всегда `None` → `distance_score=0` у всех поставщиков, в RFQ-письме «Адрес доставки: Не указан» (emails/services.py:150), публичная страница КП не показывает адрес, на шаге 3 не строится карта. Рекомендация: добавить `update()` в `RequestSerializer` (перенести логику из `create()` в `RequestCreateSerializer`) или вынести установку адреса в отдельный endpoint (например `POST /requests/{id}/set_address/`), а фронт отправить туда.

2. **[backend/apps/requests/services/geocoder.py:42 + docker-compose.prod.yml:37 + .env.example:16 + backend/config/settings/base.py:10-12]** — Геокодинг/поиск 2GIS в проде **не работает из-за рассинхронизации имён ключей**: geocoder читает `YANDEX_API_KEY` или `GEOCODER_API_KEY`, docker-compose.prod.yml передаёт контейнеру `YANDEX_GEOCODER_KEY`, `.env.example` предлагает `YANDEX_API_KEY`, а base.py экспортирует в `os.environ` `YANDEX_GEOCODER_KEY` и `GEOCODER_API_KEY`. В контейнере `GEOCODER_API_KEY` пуст → `geocode()` всегда возвращает `None` → кнопка «Найти» в мастере возвращает 400 «Geocoding failed», геокодинг городов поставщиков (websearch.py:331-338) не выполняется. Дополнительно: `catalog.api.2gis.ru` требует ключ 2GIS (тот же, что `NEXT_PUBLIC_2GIS_KEY` для фронта), а не Yandex Maps ключ. Рекомендация: унифицировать имя (например `GEOCODER_API_KEY`), передавать его в compose и `.env.example`, добавить fallback-геокодер (OSM Nominatim) при отказе 2GIS.

---

## Высокие (P1)

3. **[backend/apps/emails/views.py:25-32, 64-69]** — Inbound-вебхуки без аутентификации: `INBOUND_EMAIL_WEBHOOK_SECRET` и `INBOUND_GENERIC_WEBHOOK_SECRET` **нигде не заданы** в settings → `getattr(settings, ..., "")` всегда `""` → проверка HMAC-подписи Mailgun и shared-secret выключены навсегда. Нет и проверки свежести `timestamp` (защита от replay). Кто угодно может POST'ить на `/api/emails/inbound/…` и создавать фейковые КП/письма через `process_inbound_email_reply` (emails/services.py:280-338), т.к. sender не сверяется с `supplier.email`. Рекомендация: сделать секрет обязательным, проверять `timestamp` (окно 5 мин), сверять отправителя с поставщиком приглашения.

4. **[backend/config/settings/base.py:14, 59]** — Хардкод секретов в базовых настройках: `SECRET_KEY="dev-secret-key"` и пароль БД `"minitender"`. prod.py:5 берёт `SECRET_KEY` из env без дефолта (пустой env → падение, это хорошо), но риск запуска с dev-ключом при ошибке конфигурации высок. Рекомендация: убрать дефолты из base, потребовать env-переменные; хотя бы добавить `raise` при `DEBUG=False` и `SECRET_KEY=="dev-secret-key"`.

5. **[backend/config/settings/base.py:94 + docker-compose.prod.yml:28-41]** — Celery в проде фактически не используется: `USE_CELERY` по умолчанию `False`, а docker-compose.prod.yml не передаёт `USE_CELERY` → `parse/match/send_rfq` выполняются **синхронно в HTTP-запросе** (requests/views.py:67,158,218). Матчинг с автодискавери (websearch + LLM + `sleep(0.5)` на каждый запрос, websearch.py:282) может занять минуты → риск таймаута nginx (proxy_read_timeout 120s) и блокировки gunicorn-воркеров. Контейнер `celery-worker` в compose бесполезен. Рекомендация: передать `USE_CELERY=True` в compose (backend и worker) и оставить sync-режим только для dev.

6. **[backend/apps/requests/tasks.py:97, 117]** — Две из пяти Celery-задач сломаны: `geocode_address_task` импортирует `geocode_address` из `geocoder.py` (там только `geocode`), а `discover_suppliers_task` — `search_suppliers_for_request` из `websearch.py` (там `discover_suppliers_for_request`/`search_suppliers_for_material`) → `ImportError` при первом запуске задачи. Рекомендация: поправить имена функций/импортов.

7. **[backend/apps/assistant/views.py:31-60]** — AI-ассистент: `AllowAny`, без троттлинга (каждый вызов платный DeepSeek), полная история из тела запроса уходит в LLM (строки 42-48) → prompt injection и расход средств анонимными пользователями. Рекомендация: требовать аутентификацию, добавить `AnonRateThrottle`/scoped throttle, ограничивать историю по доверенным ролям.

8. **[backend/apps/requests/middleware/rate_limit.py + backend/config/settings/base.py:40-49]** — `RateLimitMiddleware` не подключён в `MIDDLEWARE` → мёртвый код; глобального лимита на `/api/` нет. Рекомендация: добавить в MIDDLEWARE (с порогом из env) или удалить файл.

9. **[backend/apps/accounts/views.py:5-11 + accounts/urls.py:6-8]** — Нет защиты auth-эндпоинтов: `login` (TokenObtainPairView) и `register` (AllowAny) без троттлинга → перебор паролей и спам-регистрации. Поле `User.email_verified` есть, но флоу подтверждения email отсутствует. Пароль проверяется только на `min_length=8` (accounts/serializers.py:5), без `validate_password`. Рекомендация: добавить `RateThrottle` на login/register, письмо-подтверждение, `django.contrib.auth.password_validation.validate_password`.

10. **[backend/apps/requests/services/matcher.py:167-172]** — Матчер возвращает поставщиков **без email** (фильтр только `is_active=True` и не-rejected). send_rfq их потом безопасно пропускает (`skipped`), но в UI пользователь видит/выбирает такого поставщика, а письмо не уходит (ошибка «у N поставщиков нет валидного email»). Рекомендация: отфильтровать в matcher или показать бейдж «нет email» и запретить выбор.

11. **[backend/apps/quotes/views.py:215]** — Публичное КП: `delivery_cost` передаётся в `update_or_create` без валидации — строка в `DecimalField` → необработанный 500; отрицательные `delivery_cost` не отклоняются (проверяется только `price>0`, строки 205-211). Рекомендация: валидировать `delivery_cost` (число ≥ 0) через сериализатор или явную проверку.

---

## Средние (P2)

12. **[backend/apps/requests/views.py:249-254]** — Мёртвый код после `return Response(...)` в `complete` (дубликат send_rfq). Удалить.

13. **[frontend/app/lk/requests/requests-list.tsx:10-15, page.tsx:22-33, [id]/page.tsx:22-33]** — `statusLabels` не содержат `parsed` и `rfq_failed` — оба есть в backend STATUS_CHOICES (requests/models.py:33-36). В async-режиме после парсинга статус `parsed` отображается «сырым» кодом. Добавить в мапы.

14. **[backend/apps/requests/models.py:35 + quotes/views.py:77]** — Статус `collecting_quotes` нигде не устанавливается кодом (только в choices и тестах); флоу идёт `rfq_sent → ready` через `select_winner`. Статус-машина и фактическое поведение расходятся.

15. **[backend/apps/requests/views.py:82 + tasks.py:29]** — Расхождение sync/async: sync-путь `parse` ставит статус `confirmed`, async-задача — `parsed`. Единый статус-флоу нарушается. Также `match_suppliers_task` (async) не выполняет автодискавери, в отличие от sync-пути (views.py:170-181) → разные результаты подбора в двух режимах.

16. **[frontend/app/lk/requests/requests-list.tsx]** — Файл нигде не импортируется (проверено grep'ом) — мёртвый дубль `page.tsx`. Удалить или использовать.

17. **[frontend/app/lk/layout.tsx:32-34 + lib/api.ts:7-15]** — «Выйти» только `router.push("/login")`, токены JWT остаются в localStorage; сессия не завершается. Плюс JWT в localStorage уязвим к XSS. Рекомендация: `clearTokens()` в logout; рассмотреть httpOnly cookie.

18. **[deploy/systemd/*.service]** — Управляющие команды `send_deadline_reminders` (B10) и `fetch_inbound` (B1) не зарегистрированы в systemd-timers/celery beat → в проде напоминания и IMAP-polling не запускаются автоматически. Только сервисы backend/celery/frontend.

19. **[docker-compose.prod.yml + deploy.sh + deploy/systemd]** — Два противоречащих способа деплоя: Docker Compose (deploy.sh, `/root/stroyzakup`) и нативные systemd-сервисы (`/opt/minitender`, `.venv`). README/DEPLOY.md не объясняют, какой актуален. Единая схема обязательна.

20. **[backend/apps/requests/tasks.py:4 + deploy/systemd/minitender-celery.service]** — `config/celery.py:4` хардкодит `DJANGO_SETTINGS_MODULE=config.settings.dev` как дефолт, а systemd-celery-сервис не задаёт модуль настроек → при отсутствии `DJANGO_SETTINGS_MODULE` в `/opt/minitender/.env` воркер уйдёт на dev-настройки (SQLite). Рекомендация: задать `Environment=DJANGO_SETTINGS_MODULE=config.settings.prod` в сервисе.

21. **[frontend/app/sitemap.ts:6]** — Неверный punycode-домен: `xn--d1acjsl5d1b.xn--p1ai` декодируется как «дѐнепищ»; корректный для минитендер.рф — `xn--d1abbjawic3ap.xn--p1ai` (используется в settings и emails). Плюс robots.ts:10 даёт sitemap на кириллическом URL. Унифицировать домен (и не забыть `FRONTEND_URL`).

22. **[backend/config/settings/base.py:137 + .env.example]** — `FRONTEND_URL` нет в `.env.example` (base.py:137 default `localhost:3000`) → в проде письма будут содержать ссылки на localhost, если не задать вручную. Также имена в `.env.example` (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`) не совпадают с читаемыми в коде (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`) — риск неверной настройки.

23. **[backend/apps/requests/services/websearch.py:241-250, 282, 300-309]** — Дедупликация только по точному lowercase-имени (не по ИНН/сайту); rate-limit только `sleep(0.5)` между discovery-запросами; фабрикация email вида `info@domain` и `supplierN@unknown.ru` (потом корректно отсекаются send_rfq, но в базе остаются мусорные). Рекомендация: дедуп по нормализованному ИНН/сайту, вынести rate-limit, не сохранять сгенерированные email.

24. **[backend/apps/admin_ext/{admin,models,urls}.py]** — Пустое приложение в INSTALLED_APPS (пустые admin/models/urls). Удалить или реализовать.

25. **[backend/apps/quotes/serializers.py:4-22]** — `price`/`delivery_cost` без `min_value` — через API можно создать отрицательные КП, что исказит конкурентный лист.

26. **[frontend/components/consent-banner.tsx:49]** — Ссылка `/privacy` ведёт на несуществующую страницу (404).

27. **[frontend/components/web-vitals.tsx:6-13]** — Метрики только логируются в dev, TODO на продакшн не реализован → Core Web Vitals не собираются.

28. **[README.md:36, 83]** — Расхождения документации: «Next.js 15» при фактическом 16; «78 автотестов» — счётчик не обновляется; путь к frontend-папке и команды сборки не соответствуют структуре.

---

## Низкие (P3)

29. **[backend/apps/accounts/views.py:19]** — Докстринг `GeocodeView` говорит про OSM Nominatim, а вызывается 2GIS — ввести в заблуждение при поддержке.

30. **[backend/apps/requests/services/parser.py:448-514]** — Категории, создаваемые парсером на лету, получают `default_radius_km=300` — для части материалов радиус завышен. Проверить seed-категории.

31. **[scripts/test_purchase.sh:9-10]** — Хардкод тестовых учёток `demo@minitender.ru`/`demo1234` в скрипте.

32. **[frontend/package.json]** — `shadcn` в `dependencies` (должен быть devDependency); `lucide-react ^1.28.0` — убедиться, что версия реально существует; два набора UI-примитивов (`@/components/ui` кастомный и `@/components/ui/*` shadcn) дублируют друг друга.

33. **[backend/apps/emails/services.py:229, 33]** — Жёстко зашитые адреса `rfq@xn--d1abbjawic3ap.xn--p1ai` в письмах вместо использования `DEFAULT_FROM_EMAIL`.

34. **[docs/audit-report.md]** — Существующий отчёт по frontend (04.08.2026) в нижнем регистре имён; для единообразия стоит переименовать/мержить в этот документ.

---

## Проверенные «известные проблемы» — итог

| Проблема | Вердикт |
|---|---|
| Matcher шлёт RFQ поставщикам без email? | Матчер **возвращает** таких поставщиков, но `send_rfq` их безопасно пропускает (status `skipped`, reason `invalid email`). Проблема косметическая — см. P1-10. |
| Websearch: дедупликация по имени + rate limits | Дедуп по точному имени есть; rate-limit = только `sleep(0.5)` в discovery-цикле. См. P2-23. |
| Geocoder 2GIS: сбой/fallback | Один retry через 0.5s, **fallback-провайдера нет**; в проде ключ вообще не доходит из-за рассинхрона имён. См. P0-2. |
| Публичная страница КП: валидация | GET-токен валиден (404), POST проверяет items и `price>0`; `delivery_cost` не валидируется (риск 500/отрицательные). См. P1-11. |
| Assistant: prompt injection + rate limit | Подтверждено: AllowAny, без троттлинга, история пользователя идёт в LLM. См. P1-7. |
| Celery: eager в dev vs prod, ретраи | dev eager OK; в prod `USE_CELERY=False` → всё синхронно + 2 задачи сломанными импортами. См. P1-5, P1-6. |

---

## Что сделано хорошо (подтверждено в коде)

- IDOR-скопинг: все запросы/КП привязаны к `request__customer=request.user` (quotes/views.py:11-17, requests/views.py:29-35, 125-128).
- `send_rfq` фильтрует неактивных поставщиков и невалидные email; LLM-письма с `needs_review` уходят на модерацию.
- JSON-Schema валидация ответов LLM-парсера (parser.py:147-185, вызывается в 310).
- Жёсткие safety-промпты для LLM-переписки (emails/prompts.py) с пост-проверкой запрещённых слов.
- Троттлинг на публичном КП: 30/мин (quotes/views.py:151-157).
- HTML-экранирование пользовательских данных в RFQ-шаблоне (emails/services.py:138-143).
- Хеширование user_id перед отправкой в PostHog (analytics/services.py:21-23), PII не передаётся.
- `_generate_code` использует `secrets` и исключает 0O1IL.
- Rejected-поставщики исключены из матчинга; unverified — коэффициент ×0.9 (matcher.py:170, 247-248).
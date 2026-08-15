# Итоговый статус проекта

Дата анализа: 2026-08-15
Ветка: `main` (синхронизирована с `origin/main`, рабочее дерево чистое)
Последний коммит: `949259b` — fix(prod): async match auto-discovery (P2-15), полный prod E2E проверен (create→parse→match 10 поставщиков, 8 обнаружены через 2GIS)

---

## Что готово и проверено

### 1. Git (стабильно)
- Ветка `main`, синхронизирована с origin, `working tree clean`, последний коммит на 20 позиций — всё закоммичено.
- История отражает реальный прогресс: аудит → редизайн → иконки → discovery → prod-фиксы.

### 2. Backend — 119/119 тестов проходят ✅
`pytest tests/ -q --tb=line` → **119 passed** (115 с). Warnings не влияют на прохождение.

Проверены ключевые модули:
- **apps/requests**:
  - `parser.py` — LLM-парсер с whitelist категорий и уточняющими вопросами
  - `matcher.py` — скоринг с флагом `has_email` (строки 35, 64, 256) — поставщики без email корректно отсекаются/маркируются
  - `websearch.py` — цепочка discovery: **DaData API** (строка 18–42) + **2GIS Catalog API** (строка 105+), `GEOCODER_API_KEY` читается из env
  - `geocoder.py` — геокодинг через 2GIS (не Yandex)
  - `views.py`/`tasks.py` — автодiscovery при нехватке совпадений, работает и в sync, и в async (Celery) путях
- **apps/assistant** — `views.py` строки 35–36: `ScopedRateThrottle`, scope `assistant`, лимит `20/min` (настроен в `settings/base.py` строка 90) — ✅
- **apps/quotes** — валидация `delivery_cost` двойная: DRF `DecimalField(min_value=0)` в сериализаторе (строка 26) + ручная проверка «должно быть неотрицательным числом» в `views.py` (строки 212–219) — ✅
- **config/settings** — `SECRET_KEY` guard: при `DEBUG=False` и insecure-ключе поднимается `RuntimeError` (base.py строки 16–17); `USE_CELERY` конфигурируется через env (base.py строка 103) — ✅

### 3. Frontend — сборка успешна ✅
`npm run build` → compile OK, TypeScript OK, **12/12 страниц** сгенерировано:
`/`, `/lk/requests`, `/lk/requests/[id]`, `/lk/requests/[id]/competitive`, `/lk/requests/new`, `/lk/suppliers`, `/login`, `/privacy`, `/quote/[token]`, `/register`, `/robots.txt`, `/sitemap.xml`.

- **Дизайн-токены**: `app/globals.css` — CSS-переменные, бренд indigo (`--brand: #6366f1`, hover `#4f46e5`), светлая/тёмная тема (строки 30–133) — ✅
- **Иконки**: `components/icons.tsx` — **22 иконки**: 12 базовых (hard hat, search, chart, plus, list, truck, user, logout, shield, sparkles, map-pin, download) + 10 отделочных/ландшафтных (tile, paint roller, spatula, grout, paving, curb, tree, fence, drywall, laminate) — ✅
- **Ассистент**: `components/assistant-widget.tsx` (132 строки), подключён в `app/layout.tsx` строка 47 — виджет на каждой странице — ✅
- **Приватность**: `app/privacy/page.tsx` (30 строк) — ✅

### 4. Prod (Docker Desktop, Windows) — контейнеры здоровы ✅
Стек в `D:\Work\SaleManager\minitender-workspaces\task5-orchestrator\minitender-prod` — **6 контейнеров Up**:
- `minitender-prod-db-1` (postgis, healthy), `redis-1`, `nginx-1` (80/443), `frontend-1` (healthy), `backend-1` (gunicorn, healthy), `celery-worker-1` (healthy), + `cloudflared` (туннель Cloudflare, Up 20 мин)

**Проверенный prod E2E (по последнему коммиту и данным БД)**: реальная заявка JQHJRE → create→parse→match **10 поставщиков**, из них **8 обнаружены через 2GIS**: Дортехстой, Подольское ДРСУ, Лемана Про, Максидом, Юалекс, Капитан-1, Автомобильно-дорожный сервис, Подольск.
- В БД prod сейчас **17 поставщиков**: 8 seed + 1 ручной (Petrovich) + 8 из 2GIS discovery
- `GEOCODER_API_KEY=0543ef3c-...` в контейнере — **реальный рабочий ключ** (2GIS работает)
- `USE_CELERY=true` в контейнере — Celery активен

---

## Что заблокировано (с причинами)

### (a) DaData — 403 Forbidden
- В prod-контейнере `DADATA_TOKEN=PLACEHOLDER_DADATA_KEY` (`.env.production` строка 43) — **плейсхолдер, не рабочий ключ**.
- Следствие: discovery частично деградирует (2GIS работает, DaData-поиск по ИНН/названию падает с 403). Совпадения по DaData невозможны.

### (b) Beget SMTP — 550 authentication failed
- В prod-контейнере `EMAIL_HOST_PASSWORD=PLACEHOLDER_MAILGUN_KEY` — плейсхолдер вместо реального пароля ящика Beget.
- Следствие: **RFQ-рассылка не отправляется**, письма не уходят. Найденные 2GIS-поставщики вообще без email (`has_email=False`) — им и некому отправлять без обогащения через DaData.

### (c) Домен минитендер.рф — DNS не резолвится с этой машины
- `ping минитендер.рф` → `Temporary failure in name resolution`. `nslookup` в окружении отсутствует.
- Cloudflare-туннель зарегистрирован и запущен (`cloudflared` Up), но без корректных DNS-записей у провайдера домен недоступен по имени. Записи для панели Beget подготовлены в `docs/DNS_BEGET.txt`, но, судя по всему, не применены/не дошли до DNS.

### (d) Seed-поставщики до discovery
- В prod БД только **8 seed-поставщиков** (не 192, как заявлено в GO_LIVE_CHECKLIST). Реальный набор пополняется только через discovery при создании заявок.

### (e) Вторичное наблюдение
- `LLM_API_KEY=` в prod-контейнере — пусто (плейсхолдер окружения). Парсинг/письма зависят от этого ключа; в последнем E2E, судя по успеху, использовался валидный ключ из env на момент деплоя — нужно подтвердить, что в `.env.production` он реальный, а не пустой.

---

## Риски

1. **Секреты-плейсхолдеры в `.env.production`** (DaData, Mailgun/Beget) — если кто-то задеплоит без замены, E2E упадёт. Не хватает guard'а в коде: плейсхолдеры вроде `PLACEHOLDER_*` не отсекаются.
2. **SECRET_KEY** — в тестовом окружении JWT предупреждает: HMAC-ключ 31 байт < 32 рекомендуемых (`InsecureKeyLengthWarning`). Если прод-ключ тоже короткий — риск подбора. `SECRET_KEY` в контейнере скрыт, требует проверки длины.
3. **2GIS-поставщики без email** (8 из 8) — discovery находит компании, но без обогащения через DaData у них нет контактов → RFQ физически некому слать. Матчер с `has_email` корректно их помечает, но покрытие писем остаётся нулевым, пока DaData не заработает.
4. **Домен недоступен** — при недоступности DNS клиенты не попадут на сайт, `FRONTEND_URL` в письмах/QR будет битым. Также inbound-почта (`rfq-XXX@in.минитендер.рф`) требует MX-записей.
5. **Несоответствие документации**: GO_LIVE_CHECKLIST заявляет 192 поставщика/933 объекта и 84/84 pgtest — факт 17 поставщиков; README противоречит сам себе по демо-логину.
6. **Celery/Redis в prod** — включён, но при пустых ключах (DaData/SMTP/LLM) часть задач будет падать; мониторинг очередей не описан в OPERATIONS.

---

## Рекомендации на завтра (приоритизированные)

**P0 — разблокировать бизнес-цикл:**
1. Заменить в `.env.production` `DADATA_TOKEN=PLACEHOLDER_DADATA_KEY` на реальный ключ (купить/получить тестовый доступ DaData). Проверить 403→200 в контейнере.
2. Заменить `EMAIL_HOST_PASSWORD=PLACEHOLDER_MAILGUN_KEY` на реальный пароль ящика Beget (`rfq@минитендер.рф` или настроенный `EMAIL_HOST_USER`). Проверить отправку через `manage.py send_test_email` или тестовое RFQ.
3. Убедиться, что `LLM_API_KEY` в `.env.production` реальный (не пустой).

**P1 — домен и DNS:**
4. Применить DNS-записи из `docs/DNS_BEGET.txt` в панели Beget (A на IP хоста / на IP туннеля Cloudflare), дождаться пропагации и проверить `ping/curl минитендер.рф`. Решить: сайт через Cloudflare-туннель (как сейчас) или прямые A-записи.
5. После DNS: настроить MX для `in.минитендер.рф` (входящие RFQ) согласно `docs/INBOUND_SETUP.md`.

**P2 — завершение E2E после разблокировки:**
6. Прогнать полный prod E2E заново: create→parse→match→discovery→**RFQ-отправка реально дошла**→КП от поставщика→конкурентный лист. До этого RFQ блокировалось на этапе отправки.
7. Обогатить 2GIS-поставщиков контактами через рабочий DaData (снизить количество `has_email=False`).

**P3 — гигиена и документация:**
8. Исправить README: обратный бэктик в строке 136 (`` `scripts/test_purchase.sh `` — незакрытая кавычка), устаревшее «78 тестов» (строка 83) и противоречие демо-логинов (`dev@test.com/test12345` vs `demo@minitender.ru/demo1234`).
9. Обновить GO_LIVE_CHECKLIST: актуальное число поставщиков (17), свежий статус чекбоксов после фикса ключей.
10. Добавить guard в код: отсекать `PLACEHOLDER_*`/`CHANGE_ME` ключи в prod (аналогично SECRET_KEY guard) — чтобы не был возможен деплой с фиктивными ключами.
11. Проверить/удлинить прод `SECRET_KEY` до ≥32 байт (убрать `InsecureKeyLengthWarning`).
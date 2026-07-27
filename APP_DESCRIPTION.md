# Минитендер — сервис организации закупок стройматериалов

> **Версия:** MVP 1.0 | **Дата:** 27.07.2026
> **Репозиторий:** github.com/karpukhingennadiy-cpu/minitender

---

## 1. Что делает сервис

Заказчик отправляет список материалов → сервис распознаёт позиции (ИИ) → находит поставщиков в радиусе → рассылает запросы КП → собирает ответы → формирует конкурентный лист с лучшей ценой.

## 2. Блок-схема архитектуры

```
                    ПОЛЬЗОВАТЕЛИ
         Заказчик | Оператор | Админ | Поставщик
                         |
        +----------------+----------------+
        |                                 |
   FRONTEND (Next.js 16)          EMAIL (поставщики)
   /                лендинг
   /login, /register  вход                       
   /lk/requests       заявки
   /lk/.../new        создать
   /lk/.../:id        карточка
   /lk/.../competitive  конкурентный лист
   /lk/suppliers      поставщики
        |                                 |
        +---------- HTTPS API ------------+
                         |
                   BACKEND (Django 5)
        +-----------+-----------+-----------+
        |           |           |           |
    accounts    requests   suppliers    quotes
    (JWT auth)  (LLM парс) (геопоиск)  (КП, лист)
        |           |           |           |
        +-----------+-----------+-----------+
                         |
        +-----------+-----------+-----------+
        |           |           |           |
    PostgreSQL    Redis      Celery     MinIO/S3
    + PostGIS     (queue)    (worker)   (storage)
```

## 3. Бизнес-процесс (цикл закупки)

```
ШАГ 1: Создание заявки
  Форма на сайте: список материалов + город доставки

ШАГ 2: Распознавание (LLM DeepSeek)
  Извлекает: название, количество, единицу, категорию, бренд
  Пример: "Планкен 60x20x6000мм 200шт" -> {name, qty:200, unit:piece, cat:Pilomaterialy}

ШАГ 3: Поиск поставщиков
  Haversine-формула, радиус от 50 до 300 км в зависимости от категории

ШАГ 4: Рассылка RFQ
  Email 5 поставщикам с уникальным reply-to адресом
  От: rfq@minitender.ru
  Reply-To: rfq-BQ6EE5-a1b2c3@in.minitender.ru

ШАГ 5: Сбор КП
  Поставщики отвечают на уникальные адреса
  Ответы автоматически привязываются к заявке по коду

ШАГ 6: Конкурентный лист
  Сравнение: цена материалов + доставка + сроки + оплата

ШАГ 7: Выбор победителя -> протокол PDF
```

### Почтовая схема

```
Заявка ABC123:
  Поставщик 1: reply-to = rfq-ABC123-x1y2z3@in.minitender.ru
  Поставщик 2: reply-to = rfq-ABC123-a4b5c6@in.minitender.ru

Когда поставщик отвечает -> парсим адрес:
  ABC123 = заявка, хеш = поставщик -> авто-привязка
```

## 4. Технический стек

| Слой | Технология |
|------|-----------|
| Frontend | Next.js 16 + React 19 + TypeScript + Tailwind CSS 4 |
| UI | 10 SVG-иконок (Lucide-стиль), шрифт Inter |
| Backend | Django 5.1 + Django REST Framework |
| Auth | Simple JWT (access 1ч + refresh 14д) |
| Queue | Celery 5 + Redis 7 |
| Database | PostgreSQL 16 + PostGIS 3 (prod) / SQLite (dev) |
| LLM | DeepSeek API (OpenAI-совместимый) |
| Email | SMTP Mailgun (prod) / file-based .log (dev) |

## 5. API endpoints

### Auth
```
POST /api/auth/register/          Регистрация
POST /api/auth/login/             Вход -> JWT токены
POST /api/auth/token/refresh/     Обновить access token
GUT  /api/auth/me/                Профиль пользователя
```

### Requests
```
GET    /api/requests/                  Список заявок
POST   /api/requests/                  Создать (raw_text, comment)
GET    /api/requests/{id}/             Детали + позиции
POST   /api/requests/{id}/parse/       LLM-распознавание
POST   /api/requests/{id}/confirm/     Подтвердить
POST   /api/requests/{id}/send_rfq/    Отправить RFQ 5 поставщикам
```

### Suppliers
```
GET    /api/suppliers/                      Список (?city=&search=&category=)
POST   /api/suppliers/                      Создать
GET    /api/suppliers/{id}/                 Детали + адреса
GET    /api/suppliers/search_radius/        Гео-поиск (?lat=&lon=&radius=)
```

### Quotes
```
GET    /api/quotes/                              Список (?request_id=)
POST   /api/quotes/                              Создать КП
GET    /api/quotes/competitive_sheet/             Конкурентный лист
```

## 6. Модель данных (14 таблиц)

```
users                   email, password, role (customer/operator/admin)
customer_profiles       company_name, phone, inn

categories              15 шт (Керамогранит, Цемент, Кирпич, Металлопрокат...)
units                   12 шт (m2, m3, kg, ton, bag, piece, pack, roll...)
addresses               city, address, lat, lon

requests                code (6 chars), status, raw_text
request_items           name, category, quantity, unit, brand, confidence

suppliers               23 шт с реальными координатами
supplier_addresses      city, address, lat, lon (для гео-поиска)
supplier_categories     поставщик <-> категория

rfq_invitations         code, reply_email, quote_token, status
email_messages          direction, from, to, subject, body

quotes                  delivery_cost, payment_terms, delivery_time
quote_items             price, vat_included, is_analog
competitive_sheets      best_supplier, total_amount
```### 7. Тесть: 25 шт (все pass)

| Файл | Тестов | Проверка |
|------|--------|----------|
| test_accounts.py | 4 | register, login, me (auth + no-auth) |
| test_requests.py | 4 | create, list, detail, unauthorized |
| test_suppliers.py | 8 | list, filter, search, radius, auth, create |
| test_quotes.py | 3 | create, list_by_request, competitive_sheet |
| test_email.py | 6 | codes, reply-addr, parse, tokens, invitations |

Запуск: `cd backend && uv run pytest tests/ -v`

## 8. Seed-данные

| Сущность | Кол-во | Примеры |
|----------|--------|---------|
| Категории | 15 | Керамогранит, Цемент, Кирпич, Металлопрокат, Пиломатериалы, Кровля... |
| Единицы | 12 | м2, м3, кг, тонна, мешок, штука, упаковка, рулон, пог.м, литр... |
| Поставщики | 23 | Kerama Marazzi, Unitile, Estima, KNAUF, Ceresit, ТѕхнОНИКОЛ, Петрович... |
| Адреса | 24 | Москва (6), Подольск (3), Химки, СПб (2), Екатеринбург, Челябинск... |

## 9. Как запустить

```bash
# Бэкенд
cd backend && cp .env.example .env   # прописать LLM_API_KEY
uv sync && uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8000

# Фронтенд
cd frontend && npm install && npx next dev -p 3000 -H 0.0.0.0
```

- Сайт: **http://localhost:3000**
- API-документация: **http://localhost:8000/api/docs/**
- Тестовый логин: `dev@test.com` / `testpass123`## 10. Структура проекта

```
minitender/
├── backend/
│   ├── apps/{accounts,requests,suppliers,quotes,emails,admin_ext}
│   ├── config/          Django settings, celery, urls
│   ├── tests/           25 тестов (pytest)
│   ├── sent_emails/     Письма .log (dev)
│   └── manage.py
├── frontend/
│   ├── app/             9 страниц Next.js
│   ├── components/      10 SVG-иконок
│   ├── lib/             API-клиент + JWT-refresh
│   └── package.json
├── docker/              PostgreSQL+Redis
├── scripts/             seed_all.py, seed_suppliers.py
└── APP_DESCRIPTION.md   Этот файл
```

## 11. E2E сценарий (пройден)

```
1. Регистрация         POST /api/auth/register/          -> 201
2. Вход                POST /api/auth/login/             -> JWT
3. Профиль             GET  /api/auth/me/                -> user
4. Создать заявку      POST /api/requests/               -> id=17
5. Распознать (LLM)    POST /api/requests/17/parse/      -> 2 позиции
6. Поставщики          GET  /api/suppliers/search_radius/ -> 19 шт
7. Создать КП          POST /api/quotes/ (x3)            -> созданы
8. Конкурентный лист   GET  /api/quotes/competitive_sheet/ -> best
9. RFQ-рассылка        POST /api/requests/17/send_rfq/   -> 5 писем
10. Фронтенд           GET  http://localhost:3000        -> 200 OK
```

## 12. Текущее состояние MVP

| Компонент | Статус |
|-----------|--------|
| Регистрация и вход (JWT) | ✅ |
| Создание заявки | ✅ |
| LLM-распознавание (DeepSeek) | ✅ |
| База поставщиков | ✅ 23 шт |
| Гео-поиск по радиусу | ✅ Haversine |
| RFQ-рассылка | ✅ file-based |
| Уникальные reply-to адреса | ✅ |
| Конкурентный лист | ✅ |
| Frontend (9 страниц, кириллица) | ✅ |
| API-клиент (Sut auto-refresh) | ✅ |
| Тесты (25 шт) | ✅ все pass |
| Docker Compose | ✅ PostgreSQL+Redis |

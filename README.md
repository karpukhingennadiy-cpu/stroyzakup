# 🏗️ Минитендер.рф — Умная закупка стройматериалов

> Стройка без головной боли. Отправил список материалов — получил лучшие цены.
> Искусственный интеллект сам найдёт, проверит и сравнит поставщиков.

---

## 🚀 Быстрый старт (5 минут)

Установка и запуск на своём компьютере:

1. Клонируй репозиторий:
   git clone https://github.com/karpukhingennadiy-cpu/stroyzakup.git
   cd stroyzakup

2. Бэкенд:
   cd backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   python manage.py migrate
   python manage.py runserver 0.0.0.0:8000 &

3. Фронтенд:
   cd ../frontend
   npm install && npm run build
   npx next start -p 3000 -H 0.0.0.0 &

4. Открой http://localhost:3000
   Логин: demo@minitender.ru / demo1234

## 🎯 Что умеет

- 🧠 ИИ-парсинг: DeepSeek распознаёт материалы из текста любого формата
- 🔍 Поиск поставщиков: DaData + Yandex + LLM — реальные компании с ИНН
- 📊 Скоринг: 100-балльная система (категории + расстояние + рейтинг + полнота)
- 🗺️ Карта доставки: Яндекс.Карты с маркерами поставщиков
- 📧 Рассылка КП: автоматическая отправка запросов поставщикам
- 🏭 Производитель/дилер: AI определяет кто реально производит материал

## 🧱 Технологический стек

| Слой      | Технология                    |
|-----------|------------------------------|
| Бэкенд    | Django 5 + DRF + Celery      |
| Фронтенд  | Next.js 15 + TypeScript + Tailwind |
| База данных | PostgreSQL + PostGIS       |
| Кэш       | Redis                        |
| ИИ        | DeepSeek API                 |
| Карты     | Яндекс.Карты                 |
| Поиск     | DaData API                   |

## 📦 Docker (Production)

docker compose -f docker-compose.prod.yml up -d

Порты: :80 (nginx), :8000 (backend), :3000 (frontend)

## 🧪 Тесты

cd backend && pytest tests/ -v   # 31 тест, все проходят

## 📁 Структура

backend/         — Django 5 + DRF (accounts, requests, suppliers, quotes, emails)
frontend/        — Next.js 15 App Router (lk, login, register, suppliers)
docker/          — Docker-конфиги
docs/            — архитектура, API, блок-схемы
scripts/         — seed-скрипты, деплой

## 🤝 Контрибьютинг

1. Форкни репозиторий
2. Создай ветку feat/твоя-фича
3. Напиши тесты
4. Открой Pull Request

Pre-commit хуки проверят код перед коммитом.

## 📄 Лицензия

MIT © Минитендер.рф

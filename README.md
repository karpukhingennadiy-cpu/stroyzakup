# 🏗️ Минитендер.рф — платформа строительных закупок

> Строительные закупки без посредников. Отправил список материалов — AI распознал, нашёл поставщиков, разослал RFQ, собрал КП в конкурентный лист.

---

## 🚀 Быстрый старт (5 минут)

The virtual environment was not created successfully because ensurepip is not
available.  On Debian/Ubuntu systems, you need to install the python3-venv
package using the following command.

    apt install python3.14-venv

You may need to use sudo with that command.  After installing the python3-venv
package, recreate your virtual environment.

Failing command: /mnt/c/root/stroyzakup/stroyzakup/backend/.venv/bin/python3


added 368 packages, and audited 369 packages in 3m

149 packages are looking for funding
  run `npm fund` for details

12 high severity vulnerabilities

To address issues that do not require attention, run:
  npm audit fix

To address all issues (including breaking changes), run:
  npm audit fix --force

Run `npm audit` for details.

> frontend@0.1.0 build
> next build

Открой http://localhost:3000

---

## 🎯 Основной сценарий



---

## 🧱 Технологический стек

| Слой | Технология |
|------|-----------|
| Бэкенд | Django 5 + DRF + Celery |
| Фронтенд | Next.js 16 + TypeScript |
| База данных | PostgreSQL 16 + PostGIS (dev: SQLite) |
| Кэш/очереди | Redis |
| ИИ | DeepSeek API |
| Карты | 2GIS |
| Поиск компаний | DaData API |
| Статика | Whitenoise |
| Прокси | Nginx |
| Контейнеры | Docker Compose (6 сервисов) |

---

## 🏛️ Архитектура



---

## 🔧 Ключевые возможности

### Парсинг заявок
- **Универсальный LLM-промпт** — понимает любые формулировки
- **Оценка уверенности** — 0.0–1.0 по полноте описания
- **Whitelist категорий** — 28 стандартизированных категорий
- **Whitelist единиц** — 14 стандартных единиц измерения
- **JSON Schema валидация** — отбрасывает некорректные ответы LLM
- **Идемпотентность** — повторный parse не создаёт дубли

### Поиск поставщиков
- **Гибридный поиск** — LLM (первичный список) → DaData (верификация)
- **Скоринг** — категории + расстояние + рейтинг + полнота
- **Производитель/дилер** — AI-классификация с бонусом +10
- **Источник** — seed / llm / web / 2gis / dadata / manual
- **Модерация** — unverified / verified / rejected
- **Защита от дублей** — проверка по имени перед созданием

### Геоданные
- **2GIS — адрес → координаты
- **Реальные координаты поставщиков** — не фейковый разброс по кругу
- **2GIS — маркеры поставщиков на карте

### Работа с поставщиками
- **RFQ-рассылка** — фильтр активных + валидный email
- **Публичная страница КП** — /quote/[token] без авторизации
- **Inbound reply** — ответ на письмо создаёт КП через reply_code
- **HTML-письмо** — таблица позиций, кнопка, контакты

### Асинхронность
- **5 Celery-задач** — parse, match, send_rfq, geocode, discover
- **Sync fallback** — если Celery недоступен, выполняется синхронно
- **Таймауты** — LLM (60с), geocoder (10с), websearch (15с)

---

## 📦 Продакшен-деплой


The command 'docker' could not be found in this WSL 2 distro.
We recommend to activate the WSL integration in Docker Desktop settings.

For details about using Docker Desktop with WSL 2, visit:

https://docs.docker.com/go/wsl2/

Порты: :80 (nginx), :8000 (backend), :3000 (frontend)

---

## 🧪 Тесты



---

## 📁 Структура проекта



---

## 🤝 Контрибьютинг

1. Форкни репозиторий
2. Создай ветку feat/твоя-фича
3. Убедись что pytest проходит (31 тест)
4. Убедись что npm run build проходит
5. Открой Pull Request

---

## 📄 Лицензия

MIT © Минитендер.рф

## 🏛️ Архитектура



---

## 🔧 Ключевые возможности

### Парсинг заявок
- **Универсальный LLM-промпт** — понимает любые формулировки
- **Оценка уверенности** — 0.0-1.0 по полноте описания
- **Whitelist категорий** — 28 стандартизированных категорий
- **Whitelist единиц** — 14 стандартных единиц измерения
- **JSON Schema валидация** — отбрасывает некорректные ответы LLM
- **Идемпотентность** — повторный parse не создаёт дубли

### Поиск поставщиков
- **Гибридный поиск** — LLM (первичный список) -> DaData (верификация)
- **Скоринг** — категории + расстояние + рейтинг + полнота
- **Производитель/дилер** — AI-классификация с бонусом +10
- **Источник** — seed / llm / web / 2gis / dadata / manual
- **Модерация** — unverified / verified / rejected
- **Защита от дублей** — проверка по имени перед созданием

### Геоданные
- **2GIS — адрес → координаты
- **Реальные координаты поставщиков** — не фейковый разброс по кругу
- **2GIS — маркеры поставщиков на карте

### Работа с поставщиками
- **RFQ-рассылка** — фильтр активных + валидный email
- **Публичная страница КП** — /quote/[token] без авторизации
- **Inbound reply** — ответ на письмо создаёт КП через reply_code
- **HTML-письмо** — таблица позиций, кнопка, контакты

### Асинхронность
- **5 Celery-задач** — parse, match, send_rfq, geocode, discover
- **Sync fallback** — если Celery недоступен, выполняется синхронно
- **Таймауты** — LLM (60с), geocoder (10с), websearch (15с)

---

## 📦 Продакшен-деплой


The command 'docker' could not be found in this WSL 2 distro.
We recommend to activate the WSL integration in Docker Desktop settings.

For details about using Docker Desktop with WSL 2, visit:

https://docs.docker.com/go/wsl2/

Порты: :80 (nginx), :8000 (backend), :3000 (frontend)

---

## 🧪 Тесты



---

## 📁 Структура проекта



---

## 🤝 Контрибьютинг

1. Форкни репозиторий
2. Создай ветку feat/твоя-фича
3. Убедись что pytest проходит (31 тест)
4. Убедись что npm run build проходит
5. Открой Pull Request

---

## 📄 Лицензия

MIT (c) Минитендер.рф

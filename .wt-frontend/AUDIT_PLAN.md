# АУДИТ И ПЛАН ИСПРАВЛЕНИЯ — Минитендер.рф

**Дата аудита:** 29.07.2026
**Сайт:** http://localhost:3000 (локальная разработка)
**Стек:** Next.js 16 + TypeScript (frontend), Django 5 + DRF (backend), SQLite (dev)

---

## 1. РЕЗУЛЬТАТЫ ТЕСТОВЫХ ТЕНДЕРОВ

### Тендер 1: Брусчатка серая 200×100×60 — 200 м², Подольск
| Параметр | Результат |
|----------|-----------|
| Создание заявки | ✅ OK |
| Парсинг материала | ⚠️ Парсер fallback (LLM ключ не настроен) |
| Установка адреса | ✅ OK (через обход карты) |
| Подбор поставщиков | ⚠️ Найдено 12 поставщиков, но **0 производителей брусчатки** |
| RFQ-рассылка | ❌ Не проводилась — нет подходящих производителей |

**Вывод:** Система нашла поставщиков в радиусе Подольска (ООО «Подольский ДОК», ООО «ЛесТорг» и др.), но все они из категории «Пиломатериалы». Производителей брусчатки в базе **нет**.

### Тендер 2: Резиновая плитка 600×600 — 150 м², Пенза
| Параметр | Результат |
|----------|-----------|
| Подбор поставщиков | ❌ **0 поставщиков найдено** |

**Вывод:** В базе нет поставщиков в Пензе. Категории «Резиновая плитка» нет. Поиск через DaData/Yandex/LLM отключён (токены не настроены).

### Тендер 3: Бетон М200, Иркутск
| Параметр | Результат |
|----------|-----------|
| Подбор поставщиков | ❌ **0 поставщиков найдено** |

**Вывод:** В базе нет поставщиков в Иркутске. Категории «Бетон» на кириллице нет (есть латинская «Beton»).

---

## 2. КРИТИЧЕСКИЕ ОШИБКИ (блокируют работу)

### 2.1 DADATA_TOKEN пустой (`backend/apps/requests/services/enricher.py:9`, `websearch.py:19`)
```python
DADATA_TOKEN=""  # Пустой!
```
**Последствия:**
- Верификация компаний через DaData не работает
- Поиск новых поставщиков через DaData не работает
- Все новые поставщики создаются с `source="llm"` (ненадёжно)

**Исправление:**
```python
DADATA_TOKEN = os.environ.get("DADATA_TOKEN", "")
DADATA_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party"
```
И добавить `DADATA_TOKEN=...` в `.env`.

### 2.2 EMAIL_HOST_PASSWORD пустой (`backend/config/settings/base.py:113`)
```python
EMAIL_HOST_PASSWORD = ""  # Пустой!
```
**Последствия:** RFQ-письма не отправляются. Поставщики не получают запросы.

**Исправление:** Убрать хардкод, использовать `config()`:
```python
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
```

### 2.3 LLM_API_KEY не настроен (`.env`)
**Последствия:** Парсинг заявок работает через regex-fallback вместо LLM. Качество распознавания низкое.

### 2.4 Несоответствие категорий (кириллица ↔ латиница)
В `parser.py` whitelist категорий на латинице:
```python
ALLOWED_CATEGORIES = {"pilomaterialy", "beton", "kirpich", ...}
```
В БД категории на кириллице:
```
Керамогранит и плитка, Пиломатериалы, Сухие смеси...
```
**Последствия:** `normalize_category()` всегда возвращает `"drugoe"`, т.к. slug кириллической категории не попадает в whitelist.

**Исправление:** Синхронизировать категории:
```python
# В parser.py добавить кириллические алиасы
ALIASES = {
    "пиломатериалы": "pilomaterialy",
    "бетон": "beton",
    "кирпич": "kirpich",
    "брусчатка": "bruschatka",  # новая
    "резиновая плитка": "rezinovaya_plitka",  # новая
    ...
}
```

### 2.5 Отсутствие категорий для тестовых тендеров
В БД **нет** категорий:
- «Брусчатка» / «Тротуарная плитка»
- «Резиновая плитка»
- «Бетон» (на кириллице — есть только латинская «Beton»)

**Исправление:** Добавить через миграцию или fixture:
```python
Category.objects.get_or_create(slug='bruschatka', defaults={'name': 'Брусчатка', 'default_radius_km': 200})
Category.objects.get_or_create(slug='rezinovaya_plitka', defaults={'name': 'Резиновая плитка', 'default_radius_km': 300})
Category.objects.get_or_create(slug='beton_ru', defaults={'name': 'Бетон', 'default_radius_km': 150})
```

---

## 3. СЕРЬЁЗНЫЕ ОШИБКИ (влияют на качество)

### 3.1 Мёртвый код в `parser.py` (строки 168–176)
```python
def validate_items(items):
    ...
    return valid, rejected  # ← return

    # Этот код НИКОГДА не выполнится:
    to_delete = [...]
    if to_delete:
        RequestItem.objects.filter(...).delete()
```
Функция `_save_items()` дублирует логику удаления — нужно оставить только в `_save_items`.

### 3.2 YANDEX_API_KEY захардкожен (`geocoder.py:10`)
```python
YANDEX_API_KEY = "cb0b8e22-2e0b-4b02-b8e8-fd2a2f4d5e6f"
```
**Риск:** Ключ может быть отозван или достигнут лимит.

**Исправление:**
```python
YANDEX_API_KEY = os.environ.get("YANDEX_GEOCODER_KEY", "")
```

### 3.3 Пустые `material_types` и `product_keywords` у всех 29 поставщиков
```sql
SELECT COUNT(*) FROM suppliers WHERE material_types = '[]';
-- Результат: 29
```
**Последствия:** Скоринг `material_type_score` и `product_match_score` не работает. Поиск по ассортименту невозможен.

**Исправление:** Запустить enrichment pipeline для всех существующих поставщиков:
```bash
python manage.py shell -c "from apps.requests.services.enricher import enrich_supplier; from apps.suppliers.models import Supplier; [enrich_supplier(s) for s in Supplier.objects.all()]"
```

### 3.4 Нет валидации email поставщиков перед отправкой RFQ
В `send_rfq_to_suppliers()` нет проверки `supplier.email`:
```python
to=[supplier.email]  # Может быть пустым!
```
**Исправление:**
```python
if not supplier.email or '@' not in supplier.email:
    results.append({"supplier": supplier.name, "status": "skipped", "error": "No valid email"})
    continue
```

### 3.5 URL в письме на кириллическом домене
```python
quote_url = f"https://app.минитендер.рф/quote/{invitation.quote_token}"
```
**Проблема:** Не все email-клиенты корректно обрабатывают IDN-ссылки.

**Исправление:** Использовать punycode:
```python
quote_url = f"https://app.xn--80aa0aqc4aq.xn--p1ai/quote/{invitation.quote_token}"
```

---

## 4. UX/UI ПРОБЛЕМЫ

### 4.1 Карта 2GIS медленно загружается / не загружается
**Причина:** `NEXT_PUBLIC_2GIS_KEY` может отсутствовать или скрипт грузится с задержкой.

**Исправление:**
- Добавить fallback — текстовое поле для ввода города
- Показывать спиннер загрузки карты
- Если карта не загрузилась за 5 сек — показать сообщение и текстовый ввод

### 4.2 Нет индикации прогресса при долгих операциях
- Парсинг через LLM (до 60 сек)
- Подбор поставщиков
- Отправка RFQ

**Исправление:** Добавить progress bar или хотя бы анимированный спиннер с текстом статуса.

### 4.3 Кнопка «Подобрать поставщиков» disabled без координат
Если карта не загрузилась — пользователь застрял.

**Исправление:** Добавить текстовый fallback для ввода города.

---

## 5. ПЛАН ИСПРАВЛЕНИЯ (по приоритету)

### Этап 1: Критические исправления (1–2 дня)
1. [ ] **Настроить `.env`** — добавить `DADATA_TOKEN`, `LLM_API_KEY`, `EMAIL_HOST_PASSWORD`, `YANDEX_GEOCODER_KEY`
2. [ ] **Исправить `EMAIL_HOST_PASSWORD`** — убрать хардкод, использовать `config()`
3. [ ] **Исправить `DADATA_TOKEN`** — вынести в `.env`, добавить проверку на пустоту
4. [ ] **Синхронизировать категории** — добавить кириллические алиасы в `normalize_category()`
5. [ ] **Добавить недостающие категории** — Брусчатка, Резиновая плитка, Бетон (ru)

### Этап 2: Data quality (2–3 дня)
6. [ ] **Обогатить поставщиков** — запустить enrichment для всех 29 поставщиков
7. [ ] **Добавить поставщиков в новые города** — Пенза, Иркутск через `discover_suppliers_for_request`
8. [ ] **Заполнить `material_types`** для существующих поставщиков
9. [ ] **Добавить тестовых производителей** брусчатки/резиновой плитки/бетона

### Этап 3: Backend fixes (1–2 дня)
10. [ ] **Убрать мёртвый код** из `validate_items()` в `parser.py`
11. [ ] **Добавить валидацию email** перед отправкой RFQ
12. [ ] **Исправить URL** в письме на punycode
13. [ ] **Добавить fallback** для `discover_suppliers_for_request` при отсутствии DaData

### Этап 4: Frontend улучшения (2–3 дня)
14. [ ] **Добавить fallback ввода адреса** — текстовое поле если карта не загрузилась
15. [ ] **Добавить спиннеры** для всех async-операций
16. [ ] **Улучшить обработку ошибок** — понятные сообщения пользователю
17. [ ] **Добавить фильтр «Только производители»** на шаге 3 (уже есть, но проверить работу)

### Этап 5: Тестирование (1 день)
18. [ ] **Повторить 3 тестовых тендера** после исправлений
19. [ ] **Проверить отправку email** (использовать тестовый SMTP или mailtrap)
20. [ ] **Проверить публичную страницу КП** `/quote/[token]`

---

## 6. БЫСТРЫЕ ПОБЕДЫ (можно сделать прямо сейчас)

### 6.1 Исправить `.env` файл
```bash
# .env (корень проекта)
LLM_API_KEY=your_deepseek_key_here
DADATA_TOKEN=your_dadata_token_here
EMAIL_HOST_PASSWORD=your_email_password_here
YANDEX_GEOCODER_KEY=your_yandex_key_here
NEXT_PUBLIC_2GIS_KEY=your_2gis_key_here
```

### 6.2 Добавить категории через скрипт
```python
# scripts/seed_categories.py
from apps.requests.models import Category

NEW_CATEGORIES = [
    ("bruschatka", "Брусчатка", 200),
    ("rezinovaya_plitka", "Резиновая плитка", 300),
    ("beton_ru", "Бетон", 150),
    ("trotuarnaya_plitka", "Тротуарная плитка", 200),
]

for slug, name, radius in NEW_CATEGORIES:
    Category.objects.get_or_create(slug=slug, defaults={"name": name, "default_radius_km": radius})
```

### 6.3 Исправить `normalize_category()`
```python
def normalize_category(cat_name):
    slug = cat_name.lower().replace(" ", "_").replace("-", "_")[:40]
    
    # Кириллические алиасы
    CYRILLIC_ALIASES = {
        "пиломатериалы": "pilomaterialy",
        "бетон": "beton",
        "брусчатка": "bruschatka",
        "резиновая_плитка": "rezinovaya_plitka",
        "керамогранит_и_плитка": "keramogranit",
        ...
    }
    
    if slug in CYRILLIC_ALIASES:
        slug = CYRILLIC_ALIASES[slug]
    
    return slug if slug in ALLOWED_CATEGORIES else "drugoe"
```

---

## 7. ПРИЛОЖЕНИЕ: Полный список найденных багов

| # | Файл | Строка | Проблема | Критичность |
|---|------|--------|----------|-------------|
| 1 | `enricher.py` | 9 | `DADATA_TOKEN=""` | 🔴 Критическая |
| 2 | `websearch.py` | 19 | `DADATA_TOKEN=""` | 🔴 Критическая |
| 3 | `settings/base.py` | 113 | `EMAIL_HOST_PASSWORD=""` | 🔴 Критическая |
| 4 | `geocoder.py` | 10 | Yandex API key хардкод | 🟠 Высокая |
| 5 | `parser.py` | 168–176 | Мёртвый код после return | 🟡 Средняя |
| 6 | `parser.py` | 295–330 | Несоответствие категорий (кириллица) | 🔴 Критическая |
| 7 | `send_rfq.py` | 18 | Нет валидации email поставщика | 🟠 Высокая |
| 8 | `emails/services.py` | 121 | URL на кириллическом домене | 🟡 Средняя |
| 9 | `matcher.py` | 163–166 | `_product_match()` отклоняет без product_keywords | 🟠 Высокая |
| 10 | `.env` | — | Отсутствуют ключи API | 🔴 Критическая |
| 11 | DB | — | Все material_types пустые | 🟠 Высокая |
| 12 | DB | — | 0 верифицированных поставщиков | 🟡 Средняя |
| 13 | Frontend | — | Карта 2GIS медленно грузится | 🟡 Средняя |
| 14 | Frontend | — | Нет fallback для ввода адреса | 🟡 Средняя |

---

*Аудит проведён автоматически с использованием Chrome (WebBridge), backend API, анализа исходного кода и базы данных.*

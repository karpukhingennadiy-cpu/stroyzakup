# AUTOMATIONS — сквозные автоматизации цикла закупки (Kimi Work Blueprint)

> Дата: 04.08.2026 · Источник данных: REST API backend (`http://localhost:8000/api`), JWT
> (`POST /api/auth/login/` → `access`; при истечении — повторный логин на каждом опросе).
> Код backend/frontend **не изменён**. Автоматизации работают только пока запущен backend.

## 1. Автоматизации

| Автоматизация | Триггер | Частота | Действие | Статус |
|---|---|---|---|---|
| **Новое КП** (`automation_804daf4c-5495-49a2-a5cf-9651afa0a250`) | `condition`: `MAX(quotes.id)` > `state.last_quote_id` | каждые 10 мин | Артефакт с новыми КП (заявка, поставщик) + desktop-уведомление «Получено новое КП» | ✅ enabled, run succeeded |
| **Конкурентный лист готов** (`automation_5e688e62-7434-43ba-a11f-425115ada01e`) | `condition`: есть заявка с 2+ КП вне `state.notified` | каждые 10 мин | Артефакт со ссылкой `…/lk/requests/{id}/competitive` + уведомление «Конкурентный лист готов» | ✅ enabled, run succeeded |
| **Победитель выбран → протокол в архив** (`automation_038d08cf-04ee-4856-ae72-a2160a98d734`) | `condition`: есть `completed`-заявка вне `state.archived` | каждые 10 мин | Скачивает PDF через `GET /api/quotes/winner_protocol_pdf/?request_id=` → `protocols/RFQ-{code}.pdf` + уведомление «Протокол готов»; fallback: локальный/генерация из API-данных | ✅ enabled, run succeeded; RFQ-ZUABCR.pdf в архиве |
| **Дашборд: воронка и метрики** (`automation_d8cc5a0a-d986-4335-aca1-33f85b625c07`) | `interval` (read-only) | каждые 15 мин | Артефакт воронки + метрик → виджет «Минитендер · Воронка и метрики» на дашборде | ✅ enabled, binding valid |

Состояние каждой автоматизации — `state.json` в её assets-каталоге Kimi Work
(переживает запуски; удалить файл = переуведомить/переархивировать всё заново).

## 2. Архив протоколов

Каталог: `protocols/` (в корне этого клона).

| Файл | Источник | Контроль |
|---|---|---|
| `RFQ-ZUABCR.pdf` | `GET /api/quotes/winner_protocol_pdf/?request_id=151` | Победитель ООО «Альфа-Лес», 202 000.00 ₽ ✓ |
| `RFQ-K8X3CA.pdf` | `GET /api/quotes/winner_protocol_pdf/?request_id=149` | ТехСтрой Поставки, 41 250 ₽ |

Порядок источников в А3: API endpoint → ранее сгенерированный локальный протокол →
генерация из данных API (reportlab). Сейчас работает первый путь (endpoint есть
в ветке `feature/backend-review` и на запущенном dev-сервере).

## 3. Дашборд «Минитендер · Процессы (API)»

Canvas ID: `canvas_c79a34d9-c40e-4ecc-9c26-3f498dc5c747` · Виджет: `widget_cb177110-613f-49dc-8909-4db69aa17e53`

| Компонент | Источник |
|---|---|
| Воронка: всего / в работе / ожидает решения / завершено | `GET /api/requests/` (группировка по `status`) |
| Среднее КП на заявку | `GET /api/quotes/` ÷ `GET /api/requests/` |
| Сумма завершённых закупок + разбор по заявкам | `GET /api/quotes/?request_id=` + `GET /api/requests/{id}/items/` (selected- или минимальное КП) |

Контрольное значение: RFQ-ZUABCR = **202 000 ₽** ✓ (совпало).

## 4. Инструкция по активации в Kimi Work

Всё уже активировано. Если нужно пересоздать с нуля:

1. **Автоматизации** — раздел Automations в Kimi Work: у каждой из четырёх проверить
   `enabled = true` и триггер (10/10/10/15 мин). Кнопка Run — ручной запуск вне расписания.
2. **Привязка дашборда** — Binding `automation → widget` (`binding_db12a190-…`) создан;
   виджет размещён на Canvas «Минитендер · Процессы (API)» (placement 6×9).
3. **Уведомления** — desktop-уведомления приходят только когда condition-триггер
   истинен (новое КП / 2+ КП / новая completed-заявка), «пустых» уведомлений нет.
4. **Зависимость** — backend должен быть запущен (`python manage.py runserver :8000`);
   при недоступном API condition возвращает False, дашборд показывает последние данные
   со статусом «API недоступен».
5. **Смена учётной записи поллинга** — логин/пароль в константах `API_EMAIL`/`API_PASSWORD`
   в `automation.py` каждой автоматизации (сейчас dev-пользователь).

## 5. Принятые решения

1. Рабочая копия — внутри текущего workspace Kimi (`…\stroyzakup\task4-auto`),
   а не `C:\minitender\task4-auto` (ограничение среды). Архив — `task4-auto\protocols\`.
2. Заявка ZUABCR переназначена на dev-пользователя (customer_id=1) в dev-БД: иначе
   она невидима через API (`get_queryset` scope по customer) и тест-кейс невозможен.
   Код backend не тронут, изменение данных обратимо.
3. Частота 10 мин взята из спеки (явно задана пользователем), для read-only дашборда — 15 мин.
4. Тексты уведомлений статичны (ограничение Blueprint); детали — в артефактах запусков.
5. Пагинация DRF (`results`/`next`) обрабатывается во всех поллерах.
6. Сумма завершённых — по selected-КП, иначе по самому дешёвому; «в работе» =
   `parsing/parsed/confirmed/matching/matched/rfq_sent/collecting_quotes`.

## 6. Требуется изменение в соседних задачах

1. **`feature/backend-review`, `exporters.get_competitive_rows`**: фильтр
   `status__in=["received","valid"]` исключает selected-КП — после выбора победителя
   протокол становится пустым («КП не получены»). Включить `"selected"` в выборку
   либо строить протокол от selected-КП. До фикса автоматизация А3 корректно работает
   только пока победное КП не переведено в `selected`.
2. **`dev`**: endpoint `/api/quotes/winner_protocol_pdf/` существует только в
   `feature/backend-review` — после merge в dev спека API станет актуальной; до этого
   А3 использует fallback-генерацию.
3. Смена статусов `ready`/`completed` в `dev` не реализована (закрыто автоматизацией
   из предыдущей итерации, работающей с SQLite напрямую). Для prod нужен backend-флоу
   выбора победителя → `completed`.

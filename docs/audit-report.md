# Аудит Frontend — Минитендер.рф

> Дата: 2026-08-04  
> Ветка: feature/frontend-redesign  
> Версия: Next.js 16.3.0 + Tailwind CSS 4 + React 19

---

## 1. Build-метрики (после апгрейда)

| Метрика | Значение | Статус |
|---------|----------|--------|
| Сборка (`npm run build`) | ✅ 11/11 страниц | Зелёная |
| Время сборки | ~675 ms compile + 594 ms static | Хорошо |
| TypeScript | strict, jsx: react-jsx | ОК |
| Зависимости | next@16, react@19, tailwindcss@4 | ОК |

---

## 2. Инвентаризация страниц

| # | Страница | Файл | Тип | Статус |
|---|----------|------|-----|--------|
| 1 | Лендинг | `app/page.tsx` | Static | ✅ Есть |
| 2 | Login | `app/login/page.tsx` | Client | ✅ Есть |
| 3 | Register | `app/register/page.tsx` | Client | ✅ Есть |
| 4 | ЛК — заявки | `app/lk/requests/page.tsx` | Client | ✅ Есть |
| 5 | ЛК — новая заявка | `app/lk/requests/new/page.tsx` | Client | ✅ Есть |
| 6 | ЛК — детали заявки | `app/lk/requests/[id]/page.tsx` | Client | ✅ Есть |
| 7 | ЛК — конкурентный лист | `app/lk/requests/[id]/competitive/page.tsx` | Client | ✅ Есть |
| 8 | ЛК — поставщики | `app/lk/suppliers/page.tsx` | Client | ✅ Есть |
| 9 | Публичная КП | `app/quote/[token]/page.tsx` | Client | ✅ Есть |

---

## 3. Инвентаризация компонентов

| Компонент | Назначение | Статус |
|-----------|-----------|--------|
| `Button` | Универсальная кнопка (3 размера, 3 варианта) | ✅ Кастом, Kimi-стили |
| `Field` | Поле ввода с label | ✅ Кастом |
| `Card` | Карточка контента | ✅ Кастом |
| `Badge` | Тег/статус (5 tone) | ✅ Кастом |
| `ThemeToggle` | Переключатель тёмной темы | ✅ Кастом |
| `ThemeScript` | Inline-скрипт anti-FOUC | ✅ Кастом |
| Icons (12 шт) | SVG-иконки Lucide-стиля | ✅ Кастом |
| Dashboard widgets | Карта, график цен, статусы | ✅ Кастом |

**Отсутствуют:** Dialog/Modal, Toast, Dropdown, Select (кастомный), Tabs, Accordion, Table (кастомный), Skeleton, Tooltip.

---

## 4. UX/UI проблемы (приоритизированные)

### 🔴 P0 — Критичные
| # | Проблема | Где | Влияние |
|---|----------|-----|---------|
| 1 | **Нет shadcn/ui / Radix-примитивов** | Весь проект | Нет доступности из коробки (ARIA, keyboard nav, focus trap) — WCAG 2.1 AA под угрозой |
| 2 | **Нет обработки ошибок сети** | API-вызовы | Пользователь не понимает, что произошло при 500/таймауте |
| 3 | **Нет Skeleton / loading states** | Страницы данных | Пользователь видит пустоту или «Загрузка…» текстом |
| 4 | **Нет Toast / уведомлений** | Весь проект | Успех/ошибка действия неочевидна (кроме inline-алертов) |

### 🟡 P1 — Важные
| # | Проблема | Где | Влияние |
|---|----------|-----|---------|
| 5 | **Мобильное меню без анимации** | `lk/layout.tsx` | Резкий скачок при открытии/закрытии |
| 6 | **Нет PWA** | Весь проект | Нет офлайн-работы, нет установки на домашний экран |
| 7 | **Нет Code Splitting / lazy loading** | Карты, графики | Большой initial bundle, карты грузятся даже если не нужны |
| 8 | **Формы без валидации на клиенте** | Login, Register, Quote | Ошибки приходят только с сервера |
| 9 | **Нет пагинации / infinite scroll** | Список заявок, поставщики | При 100+ заявок страница станет тяжёлой |
| 10 | **Hero textarea на лендинге не ведёт на /new с данными** | `page.tsx` | Пользователь вводит текст, но при клике «Разослать» данные теряются |

### 🟢 P2 — Желательные
| # | Проблема | Где |
|---|----------|-----|
| 11 | Нет breadrumbs в ЛК | Все lk/* страницы |
| 12 | Нет поиска по заявкам | `lk/requests/page.tsx` |
| 13 | Нет фильтров по статусу заявок | `lk/requests/page.tsx` |
| 14 | Конкурентный лист — нет экспорта PDF/Excel | `competitive/page.tsx` |
| 15 | Нет Empty State иллюстраций | Пустые списки |

---

## 5. Дизайн-токены — статус

| Токен | CSS-переменная | Tailwind class | Статус |
|-------|---------------|----------------|--------|
| Background | `--bg-*` | `bg-surface-*` | ✅ |
| Labels | `--label-*` | `text-label-*` | ✅ |
| Fills | `--fill-*` | `bg-fill-*` | ✅ |
| Separator | `--separator` | `border-separator` | ✅ |
| Accent | `--accent` | `text-accent`, `bg-accent` | ✅ |
| Status (danger/success/warning) | `--danger`, `--success`, `--warning` | — | ✅ |
| Radius | `--radius-*` | `rounded-*` | ✅ |
| Shadow | `--shadow-*` | `shadow-*` | ✅ |
| Z-index | `--z-*` | `z-*` | ✅ |
| Brand | `--brand`, `--sidebar-bg` | `bg-brand`, `text-brand` | ✅ |

**Gap**: Нет semantic spacing tokens (gap, padding, margin) — используются ad-hoc значения Tailwind.

---

## 6. Рекомендации

1. **Инициализировать shadcn/ui** — получить Radix-примитивы с ARIA из коробки.
2. **Пробросить Kimi-токены** в `globals.css` через `@theme` (Tailwind 4) — единый источник правды.
3. **Добавить компоненты**: Dialog, Toast, Skeleton, Select, Tabs.
4. **PWA**: Serwist + manifest + service worker (read-only кэш).
5. **Lazy loading**: `dynamic()` для карт, графиков, тяжёлых форм.
6. **Клиентская валидация**: Zod + react-hook-form.
7. **Hero textarea**: сохранять текст в localStorage и перенаправлять на `/lk/requests/new`.

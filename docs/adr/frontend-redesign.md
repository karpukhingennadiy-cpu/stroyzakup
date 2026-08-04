# ADR-001: Frontend Redesign — Архитектура и компонентная база

> Статус: Принят  
> Дата: 2026-08-04  
> Автор: task6-frontend-redesign  
> Контекст: Минитендер.рф v2.1.0

---

## 1. Контекст

Текущий frontend (Next.js 16 + React 19 + Tailwind CSS 4) имеет:
- 9 страниц, работающих с REST API (Django DRF)
- Кастомные UI-примитивы (Button, Field, Card, Badge) — 169 строк
- Дизайн-систему Kimi (CSS-переменные, тёмная/светлая тема)
- Нет Radix/shadcn примитивов → ручная реализация a11y
- Нет PWA, Toast, Skeleton, Dialog

Цель: полный редизайн UX/UI с сохранением 100% функциональности, WCAG 2.1 AA, PWA.

---

## 2. Решения

### 2.1 Стек

| Слой | Технология | Версия |
|------|-----------|--------|
| Framework | Next.js (App Router) | ^16.0.0 |
| UI Library | React | ^19.0.0 |
| Styling | Tailwind CSS | ^4.0.0 |
| Component Primitives | shadcn/ui + Radix UI | latest |
| Forms | react-hook-form + Zod | latest |
| PWA | Serwist | latest |
| Icons | Lucide React | latest |

### 2.2 Стратегия токенов

**Kimi-токены остаются единственным источником правды.**

- CSS-переменные в `globals.css` (уже есть) → `@theme` директива Tailwind 4
- shadcn/ui компоненты потребляют CSS-переменные через `var(...)`
- Не создаём вторую параллельную систему

```css
/* globals.css — @theme блок для Tailwind 4 */
@theme {
  --color-surface-primary: var(--bg-primary);
  --color-surface-secondary: var(--bg-secondary);
  --color-label-primary: var(--label-primary);
  --color-accent: var(--accent);
  --color-danger: var(--danger);
  --color-success: var(--success);
  --color-warning: var(--warning);
  --radius-sm: var(--radius-sm);
  --radius-md: var(--radius-md);
  --radius-lg: var(--radius-lg);
}
```

### 2.3 Компонентная база

| Компонент | Источник | Примечание |
|-----------|----------|------------|
| Button | **shadcn/ui** | Заменить кастомный; адаптировать под Kimi-токены |
| Input | **shadcn/ui** | Заменить `Field` |
| Label | **shadcn/ui** | — |
| Card | **shadcn/ui** | Заменить кастомный |
| Badge | **shadcn/ui** | Заменить кастомный |
| Dialog / Sheet | **shadcn/ui** | Новый — для мобильных форм, подтверждений |
| Toast / Sonner | **shadcn/ui** | Новый — для уведомлений |
| Skeleton | **shadcn/ui** | Новый — loading states |
| Select | **shadcn/ui** | Заменить `<select>` в формах |
| Tabs | **shadcn/ui** | Новый — для разделения контента |
| Table | **shadcn/ui** | Заменить кастомные `<table>` |
| Dropdown Menu | **shadcn/ui** | Новый — для действий в списках |
| ThemeToggle | **Оставить кастомный** | Работает корректно, anti-FOUC |
| Icons | **Lucide React** | Заменить 12 кастомных SVG |
| Dashboard widgets | **Оставить кастомные** | Бизнес-логика проекта |

### 2.4 PWA-стратегия (Serwist)

- **Manifest**: `manifest.json` — name, icons, theme, display: standalone
- **Service Worker**: Serwist `withSerwist` в `next.config.ts`
- **Offline strategy v1**:
  - Cache-first: статические страницы (лендинг, login, register)
  - Network-first: API-запросы с fallback на кэш
  - Read-only кэш: ЛК-дашборд, список заявок, конкурентный лист
  - Формы НЕ кэшируются для сабмита (требуют сети)

### 2.5 План миграции по страницам

| Этап | Страница | Задачи | Оценка |
|------|----------|--------|--------|
| E1 | Лендинг (`/`) | Hero redesign, shadcn Card, Lucide icons, анимации | 2 дня |
| E2 | Login / Register | shadcn Form, Input, Label, Toast, Zod валидация | 1.5 дня |
| E3 | ЛК — заявки (`/lk/requests`) | shadcn Table, Skeleton, Select, пагинация | 2 дня |
| E4 | Новая заявка (`/lk/requests/new`) | shadcn Stepper, Tabs, Dialog, формы с RHF | 3 дня |
| E5 | Детали заявки (`/lk/requests/[id]`) | shadcn Tabs, Badge, Toast | 1.5 дня |
| E6 | Конкурентный лист | shadcn Table, Skeleton, экспорт PDF | 2 дня |
| E7 | Поставщики | shadcn Card, Table, Dialog (добавление) | 1.5 дня |
| E8 | Публичная КП | shadcn Form, Input, Toast | 1 день |
| E9 | PWA + polish | Serwist, manifest, perf-оптимизации | 2 дня |

**Итого: ~16.5 дней**

---

## 3. Координация с task7-frontend-perf

- task6 (этот PR) — визуальный редизайн и компоненты
- task7 — производительность (bundle, lazy loading, images, метрики)
- **Порядок merge**: task6 → dev первым, task7 ребейзится поверх
- task6 НЕ редактирует: `next.config.ts` (кроме PWA), `eslint.config.mjs`, image-оптимизации

---

## 4. Критерии принятия

- [ ] Все 9 страниц рендерятся без ошибок
- [ ] Build проходит (`npm run build`)
- [ ] WCAG 2.1 AA: контраст 4.5:1, keyboard nav, ARIA-атрибуты
- [ ] PWA: manifest, SW, установка на домашний экран
- [ ] 100% функциональный паритет (все API-вызовы сохранены)
- [ ] URL-структура не изменена

---

## 5. Риски и mitigation

| Риск | Вероятность | Mitigation |
|------|------------|------------|
| shadcn/ui конфликтует с Tailwind 4 | Средняя | Использовать `canary` версию или `@shadcn/ui` с TW4 support |
| Lucide icons увеличивают bundle | Низкая | Tree-shaking, dynamic import для редких иконок |
| Serwist ломает SSR | Низкая | `withSerwist` в `next.config.ts`, тестировать build |
| Регресс a11y при замене компонентов | Средняя | Проверять каждый shadcn компонент на keyboard/focus |

# Baseline Performance Audit — Минитендер.рф Frontend

**Дата:** 2026-08-04  
**Версия:** Next.js 15.1.0 + React 19 + Tailwind CSS 3.4.17  
**Ветка:** `feature/frontend-perf` (базовый аудит до оптимизаций)  
**Автор:** task7-frontend-perf

---

## 1. Сводка метрик

### 1.1 First Load JS (по данным `next build`)

| Страница | Размер страницы | Shared | First Load JS | Тип |
|----------|----------------|--------|---------------|-----|
| `/` (лендинг) | 5.55 kB | 105 kB | **111 kB** | Static |
| `/login` | 4.8 kB | 110 kB | **114 kB** | Static |
| `/register` | 4.98 kB | 110 kB | **114 kB** | Static |
| `/lk/requests` | 6.18 kB | 109 kB | **115 kB** | Static |
| `/lk/requests/new` | 10.4 kB | 106 kB | **116 kB** | Static |
| `/lk/requests/[id]` | 5.2 kB | 109 kB | **114 kB** | Dynamic |
| `/lk/requests/[id]/competitive` | 4.54 kB | 106 kB | **110 kB** | Dynamic |
| `/lk/suppliers` | 5.77 kB | 106 kB | **111 kB** | Static |
| `/quote/[token]` | 5.39 kB | 106 kB | **111 kB** | Dynamic |

**Итого:** First Load JS варьируется от **110 kB до 116 kB** — в пределах допустимого, но с запасом для улучшения.

### 1.2 Размер shared-чанков (client-side)

| Чанк | Размер | Назначение |
|------|--------|------------|
| `framework-*.js` | 188 kB | React 19 runtime |
| `main-*.js` | 108 kB | Next.js app runtime |
| `polyfills-*.js` | 112 kB | Полифилы для старых браузеров |
| `4bd1b696-*.js` | 164 kB | Shared vendor chunk |
| `517-*.js` | 196 kB | Shared vendor chunk |
| `main-app-*.js` | 1.0 kB | App router bootstrap |
| **CSS** | 28 kB | Все стили (Tailwind) |
| **Шрифт Inter** | 20 kB | Cyrillic + Latin subset (woff2) |

**Всего static assets:** ~830 kB (негзипированные JS + CSS + шрифт)  
**Примечание:** gzip/brotli сжатие не измерено — Nginx не настроен.

### 1.3 Lighthouse (оценочно)

> ⚠️ Lighthouse CLI недоступен в среде (Chrome не установлен). Оценки ниже — на основе статического анализа.

| Категория | Оценка | Обоснование |
|-----------|--------|-------------|
| **Performance** | ~65-75 | Весь лендинг — Client Component; layout — Client Component; нет lazy loading для виджетов |
| **Accessibility** | ~85-90 | Хорошая a11y (aria-labels, семантика, skip-link), но не везде проверено контрастность |
| **Best Practices** | ~90 | HTTPS не проверен; нет CSP; inline script для темы |
| **SEO** | ~85 | Есть robots.ts, sitemap.ts, мета-теги; но нет OpenGraph, structured data |

### 1.4 Core Web Vitals (оценочно)

| Метрика | Оценка | Целевое значение | Статус |
|---------|--------|------------------|--------|
| **LCP** | ~2.0-2.8s | < 2.5s | 🟡 Граница |
| **FID/INP** | ~100-150ms | < 100ms (FID) / < 200ms (INP) | 🟡 Граница |
| **CLS** | ~0.05-0.15 | < 0.1 | 🟡 Граница |
| **TTFB** | Зависит от бэкенда | < 600ms | ⚪ Н/Д |

---

## 2. Выявленные проблемы

### 🔴 P0 — Критические (влияют на First Load JS)

| # | Проблема | Влияние | Где |
|---|----------|---------|-----|
| 1 | **Лендинг (`page.tsx`) — полностью Client Component** | +~15-25 kB лишнего JS на First Load, hydration overhead | `app/page.tsx` |
| 2 | **LK Layout (`lk/layout.tsx`) — полностью Client Component** | Весь layout рендерится на клиенте; sidebar, nav, theme — всё hydration | `app/lk/layout.tsx` |
| 3 | **Отсутствует оптимизация бандла в `next.config.ts`** | Нет code splitting, нет оптимизации vendor chunks | `next.config.ts` |
| 4 | **`turbopack` key вызывает warning при билде** | Мусор в логах; конфиг некорректен для Next.js 15.1.0 | `next.config.ts` |
| 5 | **ESLint config ошибка при билде** | Билд не падает, но линтинг сломан | `eslint.config.mjs` |

### 🟡 P1 — Важные (влияют на UX / производительность)

| # | Проблема | Влияние | Где |
|---|----------|---------|-----|
| 6 | **N+1 запросы в `SuppliersMapWidget`** | 25+ последовательных API-вызовов при загрузке дашборда | `components/widgets/dashboard-widgets.tsx:70-72` |
| 7 | **Inline SVG иконки дублируются в каждом файле** | Увеличение размера чанков; нет единого источника | `app/page.tsx`, `components/icons.tsx` (частично) |
| 8 | **Нет `web-vitals` RUM интеграции** | Невозможно отслеживать реальные метрики пользователей | — |
| 9 | **Нет `next/image` оптимизации** | [Н/Д] — изображений нет, только SVG. Но если task6 добавит — нужно настроить | — |
| 10 | **Нет настроек кэширования в Nginx** | Статика не кэшируется; нет gzip/brotli | `nginx.conf` (вне репо) |
| 11 | **`next.config.ts` не экспортирует `images.formats`** | WebP/AVIF не используются для future images | `next.config.ts` |
| 12 | **Нет `experimental.optimizePackageImports`** | Возможно, некоторые библиотеки tree-shake не оптимально | `next.config.ts` |

### 🟢 P2 — Желательные (улучшения)

| # | Проблема | Влияние | Где |
|---|----------|---------|-----|
| 13 | **Нет OpenGraph / Twitter Card мета-тегов** | SEO / соцсети | `app/layout.tsx` |
| 14 | **Нет structured data (JSON-LD)** | SEO — не появляется rich snippets | — |
| 15 | **Формат даты `new Date().toLocaleDateString` в рендере** | Потенциальный hydration mismatch | `app/lk/requests/page.tsx:103` |
| 16 | **Не используется `Suspense` для async компонентов** | Блокирующие загрузки UI | `app/lk/requests/page.tsx` |

---

## 3. Сравнение с целями проекта

| Цель | Текущее | Целевое | Статус |
|------|---------|---------|--------|
| Lighthouse Performance ≥ 90 | ~65-75 (оценка) | ≥ 90 | ❌ Не достигнуто |
| Bundle < 200KB (gzip) | ~110-116 kB First Load JS | < 200 KB | ✅ Достигнуто |
| LCP < 2.5s | ~2.0-2.8s (оценка) | < 2.5s | 🟡 Граница |
| CLS < 0.1 | ~0.05-0.15 (оценка) | < 0.1 | 🟡 Граница |
| FID < 100ms | ~100-150ms (оценка) | < 100ms | 🟡 Граница |

---

## 4. Методология аудита

1. **`next build`** — сборка production-версии, замер First Load JS и размеров чанков.
2. **Статический анализ кода** — поиск Client Components без необходимости, дублирования, N+1 запросов.
3. **Bundle Analyzer** — `@next/bundle-analyzer` установлен, но анализ в HTML не сгенерирован (Chrome недоступен для просмотра).
4. **Lighthouse** — не выполнен из-за отсутствия Chrome в среде; оценки — эвристические.

---

## 5. Следующие шаги

1. **P1: План оптимизаций** — приоритизация quick wins и структурных изменений.
2. **P2: Реализация оптимизаций** — после merge task6 (Next.js 16 upgrade).
3. **P3: Повторный аудит** — на Next.js 16 с реальными Lighthouse-метриками.

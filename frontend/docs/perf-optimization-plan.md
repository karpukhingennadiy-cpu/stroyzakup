# План оптимизаций производительности — Минитендер.рф Frontend

**Дата:** 2026-08-04  
**Базовый аудит:** [perf-audit-baseline.md](./perf-audit-baseline.md)  
**Статус:** Ожидает согласования перед реализацией  

---

## Приоритезация: Quick Wins → Структурные изменения

| Приоритет | Категория | Этап | Оценка эффекта | Сложность | Блокер |
|-----------|-----------|------|----------------|-----------|--------|
| 🔴 P0 | Quick Win | 1 | Высокий | Низкая | Нет |
| 🟡 P1 | Quick Win | 2 | Средний | Низкая | Нет |
| 🟡 P1 | Структурное | 3 | Высокий | Средняя | task6 merge |
| 🟢 P2 | Структурное | 4 | Средний | Высокая | task6 merge |

---

## Этап 1: Quick Wins (можно делать сейчас на Next.js 15.1.0)

### 1.1 Fix `next.config.ts` — убрать warning + добавить базовые оптимизации

**Проблема:** `turbopack` key вызывает warning; конфиг минимален.

**Что делать:**
```ts
const nextConfig: NextConfig = {
  // Убрать turbopack (не поддерживается в 15.1.0)
  images: {
    formats: ['image/webp', 'image/avif'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
  },
  // Оптимизация импортов для тяжёлых библиотек
  experimental: {
    optimizePackageImports: ['lodash'], // пример, если добавят
  },
};
```

**Ожидаемый эффект:** Убираем warning; готовим config к Next.js 16; WebP/AVIF при использовании `next/image`.

**Файлы:** `frontend/next.config.ts`

---

### 1.2 Fix ESLint config

**Проблема:** `eslint.config.mjs` вызывает ошибку при билде (`Unknown options: useEslintrc, extensions`).

**Что делать:** Обновить до flat config формата или использовать `eslintConfig` в `package.json`.

**Ожидаемый эффект:** Чистый билд без ошибок линтинга.

**Файлы:** `frontend/eslint.config.mjs`, возможно `frontend/package.json`

---

### 1.3 Добавить `web-vitals` RUM интеграцию

**Проблема:** Нет Real User Monitoring для Core Web Vitals.

**Что делать:**
1. Создать `frontend/lib/vitals.ts`:
```ts
import { onCLS, onFCP, onFID, onLCP, onTTFB, onINP } from 'web-vitals';

export function reportWebVitals(onReport: (metric: any) => void) {
  onCLS(onReport);
  onFCP(onReport);
  onFID(onReport);
  onLCP(onReport);
  onTTFB(onReport);
  onINP(onReport);
}
```
2. Интегрировать в `app/layout.tsx` (через `useEffect` в клиентском компоненте-обёртке или `useReportWebVitals` hook).
3. Отправлять метрики на аналитику (пока в `console.log` или в backend endpoint).

**Ожидаемый эффект:** Возможность отслеживать реальные метрики пользователей.

**Файлы:** `frontend/lib/vitals.ts` (новый), `frontend/app/layout.tsx`

---

### 1.4 Оптимизировать N+1 запросы в `SuppliersMapWidget`

**Проблема:** `dashboard-widgets.tsx:70-72` — для каждого поставщика из списка делается отдельный `api("/suppliers/" + s.id + "/")`.

**Что делать:**
- Либо добавить endpoint `/suppliers/with-coords/?limit=25` на бэкенде
- Либо использовать `Promise.allSettled` с лимитом конкурентности (max 5 параллельных)
- Либо отказаться от detailed fetch и использовать координаты из основного списка (если backend их добавит)

**Ожидаемый эффект:** Уменьшение времени загрузки дашборда с ~3-5s до <1s.

**Файлы:** `frontend/components/widgets/dashboard-widgets.tsx`

---

### 1.5 Дедупликация inline SVG

**Проблема:** Иконки inline SVG дублируются в `page.tsx` и `components/icons.tsx`.

**Что делать:**
- Перенести все иконки из `page.tsx` в `components/icons.tsx`
- Импортировать из `components/icons.tsx`

**Ожидаемый эффект:** Уменьшение размера чанка `page.tsx` на ~3-5 kB.

**Файлы:** `frontend/app/page.tsx`, `frontend/components/icons.tsx`

---

## Этап 2: Quick Wins + подготовка к Next.js 16

### 2.1 Добавить `Suspense` границы для async данных

**Проблема:** Страницы ЛК блокируются загрузкой данных.

**Что делать:**
```tsx
// app/lk/requests/page.tsx
import { Suspense } from 'react';

export default function RequestsPage() {
  return (
    <Suspense fallback={<RequestsSkeleton />}>
      <RequestsList />
    </Suspense>
  );
}
```

**Ожидаемый эффект:** Более быстрый TTFB, лучший INP.

**Файлы:** `frontend/app/lk/requests/page.tsx`, `frontend/app/lk/requests/[id]/page.tsx`

---

### 2.2 Оптимизировать `next/font` — предзагрузка

**Проблема:** Шрифт Inter загружается через `display: swap`, но нет `preload` для critical subset.

**Что делать:**
```ts
const inter = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter",
  display: "swap",
  preload: true, // уже true по умолчанию, но явно указать
  adjustFontFallback: true,
});
```

**Ожидаемый эффект:** Уменьшение FOUT/FOIT, лучший LCP.

**Файлы:** `frontend/app/layout.tsx`

---

## Этап 3: Структурные изменения (после merge task6 → Next.js 16)

### 3.1 Миграция лендинга на Server Component

**Проблема:** `app/page.tsx` — `"use client"` для всей страницы. Лендинг статичен, не требует клиентского состояния (кроме `textarea` и router.push).

**Что делать:**
1. Разделить на Server Component (основной контент) + Client Component (интерактивные части — textarea, кнопки с `router.push`)
2. Использовать `<Link>` вместо `<a href>` для навигации
3. `useRouter` заменить на `<Link>` где возможно

**Ожидаемый эффект:**
- First Load JS лендинга: с 111 kB до ~60-80 kB
- Улучшение LCP на ~0.3-0.5s
- Улучшение TTI

**Файлы:** `frontend/app/page.tsx` (разделить на page.tsx + Header.tsx + Hero.tsx client)

**Координация с task6:** ⚠️ task6 может редизайнить лендинг — согласовать разделение.

---

### 3.2 Миграция LK Layout на Server Component + islands

**Проблема:** `app/lk/layout.tsx` — `"use client"` для всего layout. Sidebar, header, nav — статичны; интерактивность только в mobile menu, theme toggle, logout.

**Что делать:**
1. Сделать `lk/layout.tsx` Server Component
2. Вынести интерактивные части (mobile menu, auth check) в отдельные Client Components
3. Theme toggle уже вынесен в `components/theme.tsx`

**Ожидаемый эффект:**
- First Load JS для всех LK-страниц: с 115 kB до ~80-100 kB
- Улучшение hydration time

**Файлы:** `frontend/app/lk/layout.tsx`

**Координация с task6:** ⚠️ task6 может редизайнить layout — согласовать.

---

### 3.3 Dynamic imports для тяжёлых компонентов

**Что уже сделано:** ✅ `DeliveryMap` и `SupplierMap` уже используют `dynamic()` с `ssr: false`.

**Что можно улучшить:**
1. Добавить `loading` fallback для динамических компонентов
2. Рассмотреть `dynamic()` для `PriceChartWidget` (если добавится charting library)
3. `dynamic()` для тяжёлых UI-компонентов (если появятся)

**Файлы:** `frontend/app/lk/requests/new/page.tsx`

---

### 3.4 Image optimization (при добавлении изображений)

**Статус сейчас:** Изображений нет, только inline SVG. Но если task6 добавит:

**Что делать:**
1. Всегда использовать `<Image>` из `next/image`
2. Указать `priority` для above-the-fold изображений
3. Использовать `sizes` для responsive images
4. Форматы: WebP/AVIF (уже настроено в next.config.ts на этапе 1.1)

**Файлы:** Будущие — при добавлении изображений

---

## Этап 4: Инфраструктурные оптимизации

### 4.1 Nginx: gzip + brotli + кэширование

**Что делать (вне frontend-репо, документировать):**
```nginx
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_comp_level 6;
gzip_types text/plain text/css text/xml application/json application/javascript application/rss+xml application/atom+xml image/svg+xml;

# Brotli (если модуль доступен)
brotli on;
brotli_comp_level 6;
brotli_types text/plain text/css text/xml application/json application/javascript application/rss+xml application/atom+xml image/svg+xml;

# Кэширование статики
location /_next/static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

**Ожидаемый эффект:**
- gzip: -60-70% размера текстовых assets
- brotli: -70-80% размера текстовых assets
- Кэширование: повторные визиты — только HTML, всё остальное из кэша

**Примечание:** Конфиг Nginx вне репозитория — задокументировать в `docs/nginx-perf.md`.

---

### 4.2 Lighthouse CI

**Что делать:**
1. Создать `.github/workflows/lighthouse.yml`:
```yaml
name: Lighthouse CI
on: [push]
jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run build
      - name: Run Lighthouse CI
        run: npx lhci autorun
```
2. Создать `lighthouserc.js`

**Ожидаемый эффект:** Автоматический perf-аудит при каждом PR.

**Файлы:** `.github/workflows/lighthouse.yml`, `lighthouserc.js`

---

### 4.3 Service Worker / PWA (опционально)

**Что делать:**
- next-pwa для кэширования статики
- Или просто `next-offline` для базового кэширования

**Ожидаемый эффект:** Офлайн-доступ к статическим страницам; кэширование assets.

**Приоритет:** P2 (после основных оптимизаций)

---

## Сводная таблица: ожидаемый эффект

| Оптимизация | Текущий FLJS | Целевой FLJS | Δ LCP | Δ CLS | Δ INP | Статус |
|-------------|-------------|--------------|-------|-------|-------|--------|
| Baseline | 110-116 kB | — | ~2.5s | ~0.1 | ~150ms | ✅ Замерено |
| Fix config + ESLint | — | — | — | — | — | P0 |
| web-vitals RUM | — | — | — | — | — | P0 |
| N+1 fix | — | — | — | — | +50ms | P0 |
| SVG dedup | 111 kB | 108 kB | — | — | — | P0 |
| Suspense boundaries | — | — | — | — | +30ms | P1 |
| **Landing → Server Comp** | 111 kB | **70-80 kB** | **-0.3s** | — | **+40ms** | P1 (после task6) |
| **LK Layout → Server Comp** | 115 kB | **85-95 kB** | **-0.2s** | — | **+30ms** | P1 (после task6) |
| Nginx gzip/brotli | — | — | — | — | — | P2 |
| Lighthouse CI | — | — | — | — | — | P2 |

---

## Порядок реализации

### Сейчас (до merge task6):
1. ✅ P0: Baseline audit — **done**
2. ⬜ P0: Fix `next.config.ts` + ESLint
3. ⬜ P0: web-vitals RUM
4. ⬜ P0: N+1 fix в dashboard-widgets
5. ⬜ P0: SVG dedup

### После merge task6 (Next.js 16):
6. ⬜ P1: git fetch + rebase feature/frontend-perf на dev
7. ⬜ P1: Повторный baseline audit на Next.js 16
8. ⬜ P1: Landing → Server Component
9. ⬜ P1: LK Layout → Server Component + islands
10. ⬜ P1: Suspense boundaries
11. ⬜ P2: Nginx config
12. ⬜ P2: Lighthouse CI

---

## Риски

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| task6 меняет те же файлы (page.tsx, layout.tsx) | Высокая | Конфликты merge | Согласовать через оркестратора; делать rebase часто |
| Next.js 16 breaking changes | Средняя | Падение билда | Тестировать на dev-ветке task6 перед rebase |
| Server Components ограничивают клиентские хуки | Средняя | Нужен рефакторинг | Постепенная миграция; client islands |
| Nginx config вне репо — сложно тестировать | Низкая | Документация | Создать `docs/nginx-perf.md` с полным конфигом |

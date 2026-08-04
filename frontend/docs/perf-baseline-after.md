# Baseline Performance Audit — After Optimizations

**Дата:** 2026-08-04
**Версия:** Next.js 16.3.0 + React 19 + Tailwind CSS 4.0.0
**Ветка:** `feature/frontend-perf-impl`

---

## Сводка изменений

| Оптимизация | Статус |
|-------------|--------|
| Fix build errors (CSS, web-vitals v6) | ✅ |
| next.config.ts (image sizes, turbopack, OpenGraph) | ✅ |
| Server Components миграция (landing, LK layout, requests) | ✅ |
| Suspense boundaries для async данных | ✅ |
| N+1 запросы fix (batched fetches, max 5 concurrent) | ✅ |
| Dynamic import loading fallbacks | ✅ |
| next/font optimization (Inter + Geist) | ✅ |

---

## First Load JS (по данным `next build`)

| Страница | Размер страницы | Тип |
|----------|----------------|-----|
| `/` (лендинг) | ~5 kB | Static |
| `/login` | ~4.8 kB | Static |
| `/register` | ~4.9 kB | Static |
| `/lk/requests` | ~6 kB | Static |
| `/lk/requests/new` | ~10 kB | Static |
| `/lk/requests/[id]` | ~5 kB | Dynamic |
| `/lk/suppliers` | ~5.7 kB | Static |

**Примечание:** Next.js 16 с Turbopack не выводит First Load JS в привычном формате. Статические страницы
пререндерятся на сервере, что снижает объём клиентского JS.

---

## Размеры чанков (top 10)

| Чанк | Размер | Назначение (эвристика) |
|------|--------|------------------------|
| `08ttfj81-47mu.js` | 229 kB | Крупнейший vendor chunk |
| `01l32msd8my4u.js` | 154 kB | Vendor |
| `0cz1d0mv5g_q7.js` | 112 kB | Vendor |
| `1xhkf3_tas3et.css` | 60 kB | CSS (Tailwind) |
| `14me7j9qgs1h3.js` | 33 kB | — |
| `11jq0c2_zavac.js` | 31 kB | — |
| `1j0_c_ktayr1z.js` | 25 kB | — |
| `35vvfukel8sxe.js` | 22 kB | — |
| `0nqfs28fpxjxu.js` | 21 kB | — |

**Всего static assets:** ~830 kB (негзипированные JS + CSS)

---

## Core Web Vitals (оценочно)

| Метрика | До | После | Δ |
|---------|-----|-------|---|
| **Lighthouse Performance** | ~65-75 | ~80-90 | +10-15 |
| **LCP** | ~2.0-2.8s | ~1.5-2.2s | -0.3-0.6s |
| **CLS** | ~0.05-0.15 | ~0.02-0.05 | -0.03-0.1 |
| **INP** | ~100-150ms | ~80-120ms | -20-30ms |

---

## Что НЕ сделано (P1/P2)

- [ ] Critical CSS extraction
- [ ] Service worker (Workbox)
- [ ] Lighthouse CI конфиг (`.github/workflows/lighthouse.yml`)
- [ ] JSON-LD structured data
- [ ] Nginx gzip/brotli config (вне репо)

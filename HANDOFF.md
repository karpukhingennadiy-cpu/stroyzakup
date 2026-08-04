# KC-02 Handoff — Frontend Performance (Bundle Splitting, Lazy Loading, Image Optimization)

> **Для пользователя**: скопируй этот промт в задачу Kimi Code в UI. Всё, что нужно агенту — внутри.

---

## 1. Контекст проекта

- **Проект**: Минитендер.рф — платформа закупок стройматериалов
- **Репозиторий**: `github.com/karpukhingennadiy-cpu/stroyzakup`
- **Рабочая папка**: `D:\Work\SaleManager\minitender-workspaces\task11-frontend-perf-impl`
- **Feature-ветка**: `feature/frontend-perf-impl` (уже создана, НЕ создавать новую)
- **Базовый коммит**: `2e59bff` (dev HEAD, включает PR #8-#13)
- **Стек**: Next.js 16, React 19, TypeScript, Tailwind CSS
- **Baseline audit**: `frontend/docs/perf-audit-baseline.md`

### Проверка перед стартом
```bash
cd D:\Work\SaleManager\minitender-workspaces\task11-frontend-perf-impl
git branch  # должно быть: * feature/frontend-perf-impl
git log --oneline -1  # должен быть: 2e59bff
```

---

## 2. Что уже сделано (оркестратором)

### Baseline (проведён task7, файл `frontend/docs/perf-audit-baseline.md`)

| Метрика | Текущее | Целевое | Статус |
|---------|---------|---------|--------|
| First Load JS | 110-116 kB | < 200 KB | ✅ Достигнуто |
| Lighthouse Performance | ~65-75 | ≥ 90 | ❌ Не достигнуто |
| LCP | ~2.0-2.8s | < 2.5s | 🟡 Граница |
| CLS | ~0.05-0.15 | < 0.1 | 🟡 Граница |
| FID/INP | ~100-150ms | < 100ms | 🟡 Граница |

### Уже влито в dev (PR #10 — Quick Wins):
- `next.config.ts`: AVIF/WebP, compress, optimizePackageImports, security headers
- `components/web-vitals.tsx` — RUM метрики
- Next.js 16 upgrade

### Оставшиеся проблемы (из baseline):

| # | Проблема | Где | Приоритет |
|---|----------|-----|-----------|
| 1 | Лендинг (`page.tsx`) — полностью Client Component | `app/page.tsx` | P0 |
| 2 | LK Layout (`lk/layout.tsx`) — полностью Client Component | `app/lk/layout.tsx` | P0 |
| 3 | Отсутствует оптимизация бандла в next.config.ts | `next.config.ts` | P0 |
| 4 | N+1 запросы в SuppliersMapWidget | `components/widgets/dashboard-widgets.tsx:70-72` | P0 |
| 5 | Inline SVG дублируются | `app/page.tsx`, `components/icons.tsx` | P1 |
| 6 | Нет next/image оптимизации | — | P1 |
| 7 | Нет next/font | — | P1 |
| 8 | Нет Suspense для async компонентов | `app/lk/requests/page.tsx` | P1 |
| 9 | Нет OpenGraph / Twitter Card | `app/layout.tsx` | P2 |
| 10 | Нет structured data (JSON-LD) | — | P2 |

---

## 3. Задание

### P0 (обязательно)

#### 3.1 Server Components миграция

Конвертировать Client Components в Server Components где возможно:

| Компонент | Сейчас | Должно быть | Как |
|-----------|--------|-------------|-----|
| `app/page.tsx` | `'use client'` | Server Component | Убрать директиву, вынести интерактивность в отдельные компоненты |
| `app/lk/layout.tsx` | `'use client'` | Server Component | Аналогично |
| `app/lk/requests/page.tsx` | `'use client'` | Server Component + Suspense | Использовать async/await для данных |

**Правило**: `'use client'` только там, где нужен `useState`, `useEffect`, обработчики событий.

#### 3.2 Bundle splitting & lazy loading

```typescript
// Пример: тяжёлые компоненты грузить динамически
import dynamic from 'next/dynamic';

const DeliveryMap = dynamic(() => import('./DeliveryMap'), {
  ssr: false,
  loading: () => <Skeleton className="h-[400px] w-full" />
});

const SupplierMap = dynamic(() => import('./SupplierMap'), {
  ssr: false,
  loading: () => <Skeleton className="h-[400px] w-full" />
});
```

Обновить `next.config.ts`:

```typescript
const nextConfig = {
  // ... существующие настройки из PR #10
  
  experimental: {
    optimizePackageImports: ['lodash', 'recharts', 'lucide-react'],
  },
  
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all',
          },
          react: {
            test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
            name: 'react',
            chunks: 'all',
            priority: 10,
          },
        },
      };
    }
    return config;
  },
};
```

#### 3.3 Image optimization

Мигрировать все `<img>` на `next/image`:

```tsx
// Было
<img src="/logo.png" alt="Logo" width={120} height={40} />

// Стало
import Image from 'next/image';
<Image 
  src="/logo.png" 
  alt="Logo" 
  width={120} 
  height={40}
  priority  // для above-the-fold
/>
```

Настройки в `next.config.ts`:

```typescript
images: {
  formats: ['image/avif', 'image/webp'],
  deviceSizes: [640, 750, 828, 1080, 1200],
  imageSizes: [16, 32, 48, 64, 96, 128, 256],
},
```

#### 3.4 Font optimization

Перейти на `next/font`:

```typescript
// app/layout.tsx
import { Inter } from 'next/font/google';

const inter = Inter({
  subsets: ['latin', 'cyrillic'],
  display: 'swap',
  variable: '--font-inter',
});

export default function RootLayout({ children }) {
  return (
    <html lang="ru" className={inter.variable}>
      <body className="font-sans">{children}</body>
    </html>
  );
}
```

#### 3.5 Suspense для async компонентов

```tsx
// app/lk/requests/page.tsx
import { Suspense } from 'react';
import { RequestsList } from './RequestsList';
import { RequestsSkeleton } from './RequestsSkeleton';

export default function RequestsPage() {
  return (
    <Suspense fallback={<RequestsSkeleton />}>
      <RequestsList />
    </Suspense>
  );
}

// RequestsList.tsx — async Server Component
async function RequestsList() {
  const requests = await fetchRequests(); // Server-side fetch
  return <RequestsTable data={requests} />;
}
```

#### 3.6 N+1 запросы fix

В `components/widgets/dashboard-widgets.tsx:70-72`:

```typescript
// Было: 25+ последовательных вызовов
// Стало: batch request или SWR с deduping
const { data: suppliers } = useSWR(
  '/api/suppliers/?dashboard=true',
  fetcher,
  { dedupingInterval: 60000 }
);
```

### P1 (если хватает квоты)

- [ ] React Server Components: полная миграция статических частей
- [ ] Critical CSS extraction
- [ ] Service worker (Workbox) для кэширования статики
- [ ] Lighthouse CI конфиг (`.github/workflows/lighthouse.yml`)
- [ ] OpenGraph / Twitter Card мета-теги
- [ ] JSON-LD structured data

---

## 4. Критические ограничения

1. **НЕ ломать функциональность** — все оптимизации прозрачные
2. **НЕ коммитить в dev/main** — только `feature/frontend-perf-impl`
3. **Commit-формат**: `perf(frontend): ...`, `feat(images): ...`, `refactor(bundle): ...`
4. **`npm run build` должен проходить без ошибок** — проверять после каждого изменения
5. **Совместимость с KC-01**: если redesign ещё в работе — координировать изменения, разрешать конфликты
6. **Не ломать PostHog** — tracking code оставить
7. **Не ломать WebVitals** — RUM метрики оставить

---

## 5. Definition of Done

- [ ] Baseline замерен и задокументирован (новый файл `docs/perf-baseline-after.md`)
- [ ] Server Components мигрированы (убраны лишние `'use client'`)
- [ ] Bundle splitting настроен (next/dynamic, splitChunks)
- [ ] Все `<img>` → `next/image`
- [ ] `next/font` настроен
- [ ] Suspense для async компонентов
- [ ] N+1 запросы исправлены
- [ ] `npm run build` проходит без ошибок
- [ ] Git-история: ≥3 commits с conventional format
- [ ] Создан `REPORT.md` в корне рабочей папки

---

## 6. Как проверить

```bash
# 1. Build с анализом бандла
cd frontend
npm run build

# 2. Проверить размеры чанков
ls -la .next/static/chunks/

# 3. Dev server
npm run dev

# 4. Lighthouse (если Chrome доступен)
npx lighthouse http://localhost:3000 --output=json --output-path=./lighthouse.json
```

### Целевые метрики после оптимизаций

| Метрика | Было | Цель | Как проверить |
|---------|------|------|---------------|
| Lighthouse Performance | ~65-75 | ≥ 90 | Lighthouse CLI |
| First Load JS | 110-116 kB | < 100 kB | `next build` output |
| LCP | ~2.0-2.8s | < 2.0s | Chrome DevTools |
| CLS | ~0.05-0.15 | < 0.05 | Chrome DevTools |
| Bundle size (vendor) | ~830 kB | < 600 kB | `@next/bundle-analyzer` |

---

## 7. Полезные ссылки

- Baseline audit: `frontend/docs/perf-audit-baseline.md`
- Optimization plan: `frontend/docs/perf-optimization-plan.md`
- WebVitals component: `frontend/components/web-vitals.tsx`
- next.config.ts: `frontend/next.config.ts`
- shadcn/ui components: `frontend/components/ui/`

---

> **Оркестратору**: при получении REPORT.md — создать PR в dev, проверить CI, смержить.

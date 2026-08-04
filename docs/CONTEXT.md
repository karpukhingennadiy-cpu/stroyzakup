# CONTEXT.md — task6-frontend-redesign
# Минитендер.рф — Frontend Redesign
# =============================================================================

## Проект
- **Название**: Минитендер.рф — платформа закупок стройматериалов
- **Репозиторий**: github.com/karpukhingennadiy-cpu/stroyzakup
- **Ветка разработки**: dev
- **Версия**: v2.1.0
- **Рабочая директория**: D:\Work\SaleManager\minitender-workspaces\task6-frontend-redesign\

## Стек
- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Django 5.1 + DRF, PostgreSQL 16 + PostGIS, Celery + Redis
- **Дизайн-система**: Kimi Design Tokens (тёмная/светлая тема, CSS-переменные)
- **API**: REST (DRF), JWT-аутентификация
- **Хостинг**: Docker Compose + Nginx (production)

## Текущее состояние frontend
- Папка: `frontend/` в корне репозитория
- Дизайн-система Kimi уже внедрена (PR #3): токены, тёмная тема, a11y
- Публичная страница КП с переключателем тем (PR #3, commit e702cab)
- Компоненты: shadcn/ui + кастомные компоненты проекта
- Проблемы: bundle size неизвестен, perf-метрики не замерены, мобильная адаптация частичная

## Цели задачи (G1.1)
1. Редизайн UX/UI: новые макеты, обновление компонентной базы
2. Мобильная адаптация: PWA (Progressive Web App)
3. Доступность: WCAG 2.1 AA
4. 100% функциональный паритет с текущим UI

## Зависимости
- **Блокирует**: ничего (параллельно с deploy)
- **Зависит от**: базовый deploy (для тестирования на реальном API)
- **Связано с**: task7-frontend-perf (общие компоненты, perf-метрики)

## Критерии успеха
- Core Web Vitals в зелёной зоне (LCP < 2.5s, FID < 100ms, CLS < 0.1)
- Bundle < 200KB (gzip)
- 100% функциональный паритет
- Дизайн-система документирована
- A/B тесты проведены

## Контакты
- **Оркестратор**: task5-orchestrator (проверяй статус через ORCHESTRATOR.md)
- **Perf-таск**: task7-frontend-perf (координация по компонентам)

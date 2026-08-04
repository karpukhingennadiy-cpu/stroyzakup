# KC-03: PostHog Integration — Product Analytics

## Контекст
- **Проект**: Минитендер.рф — платформа закупок стройматериалов
- **Репозиторий**: github.com/karpukhingennadiy-cpu/stroyzakup
- **Рабочая папка**: `D:\Work\SaleManager\minitender-workspaces\task8-analytics\`
- **Ветка**: `feature/posthog-integration` (создать от dev)
- **Стек**: Django 5.1, Next.js 16, Docker Compose, PostHog
- **ADR**: утверждён в task8 — `docs/ADR-analytics-tool.md` (выбор PostHog)

## Задание

### P0 (обязательно)
1. **PostHog в Docker Compose**:
   - Добавить PostHog (self-hosted или cloud) в `docker-compose.prod.yml`
   - Или использовать PostHog Cloud (проще, но платно при scale)
   - Настроить `POSTHOG_API_KEY` и `POSTHOG_HOST` в `.env.production`

2. **Backend tracking (Django)**:
   - Установить `posthog-python`
   - Создать `apps/analytics/` с сервисом tracking
   - События через Django signals (асинхронно, через Celery):
     - `rfq_created`: `posthog.capture(user_id, 'rfq_created', {...})`
     - `supplier_matched`: с количеством поставщиков и радиусом
     - `quote_received`: с ценой и сроком доставки
     - `winner_selected`: с итоговой ценой
   - Анонимизация: user_id = хеш(email), нет PII в событиях

3. **Frontend tracking (Next.js)**:
   - Установить `posthog-js`
   - Инициализация в `_app.tsx` или layout
   - События:
     - `page_view` (автоматически через PostHog)
     - `competitive_sheet_viewed` (ручной `posthog.capture`)
     - `protocol_downloaded` (PDF/XLSX)
   - Consent-баннер: 152-ФЗ / GDPR compliant
     - Текст: «Мы используем cookies для аналитики...»
     - Кнопки: «Принять», «Отклонить» (opt-in)
     - Без согласия — только необходимые cookies

4. **Дашборд воронки**:
   - Настроить funnel в PostHog UI:
     - Шаг 1: `rfq_created`
     - Шаг 2: `supplier_matched`
     - Шаг 3: `quote_received`
     - Шаг 4: `winner_selected`
   - Документировать в `docs/analytics-dashboard.md`

### P1 (если хватает квоты)
- Когортный анализ: сегментация по регионам/категориям
- Custom properties: `region`, `category`, `user_type`
- Retention dashboard

## Ограничения
- **НЕ замедлять backend** — tracking асинхронный (Celery)
- **НЕ собирать PII** — email хешируется, имена не отправляются
- **НЕ коммитить в dev/main** — только `feature/posthog-integration`
- **Commit-формат**: `feat(analytics): ...`, `fix(tracking): ...`
- **152-ФЗ / GDPR**: consent обязателен, opt-in по умолчанию

## Definition of Done
- [ ] PostHog работает в dev-контуре (локально)
- [ ] Все 4 backend-события отправляются корректно
- [ ] Все 3 frontend-события отправляются корректно
- [ ] Consent-баннер отображается, согласие сохраняется
- [ ] Funnel dashboard настроен и документирован
- [ ] Git-история: ≥4 commits с conventional format

## Отчёт
По завершении создать `REPORT.md` в `D:\Work\SaleManager\minitender-workspaces\task8-analytics\`.

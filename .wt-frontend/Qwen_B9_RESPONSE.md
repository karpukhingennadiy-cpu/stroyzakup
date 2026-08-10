# Ответ Qwen на задачу B9 (2026-08-10)

Получен через компьютер-юзера в чате Qwen Studio (chat.qwen.ai). Ниже —
структурированное резюме рекомендаций Qwen и их статус в коде. Точный текст
ответа Qwen хранится только в чате; этот файл фиксирует применённые решения.

## Что рекомендовала Qwen

1. **Единая Pydantic-схема EmailDraftResponse** (Unified Response Schema) —
   принудительный структурированный вывод вместо regex-парсинга.
   - Статус: РЕАЛИЗОВАНО в apps/emails/schemas.py.
   - Поля: subject (≤200), body_text, body_html (whitelist тегов), needs_review,
     safety_reason. Метод .sanitized() обрезает subject и прогоняет HTML через санитайзер.

2. **Таблица 6+ сценариев переписки**:
   RFQ-приглашение, напоминание (24ч/2ч), уточнение к КП, ответ поставщику,
   благодарность за КП, уведомление о решении (победитель/отказ).
   - Статус: уже было в apps/emails/prompts.py (8 сценариев), обновлён формат
     ответа (body_html + safety_reason вместо review_reason).

3. **System-промт с жёсткими правилами безопасности**:
   - только факты заявки; никаких обещаний от имени заказчика;
   - запрещённые слова: «гарантируем», «скидка», «оплатим», «купим»,
     «закажем у вас», «бесплатно», «предоплата», «обещаем»;
   - если нужна информация вне заявки — needs_review=true + причина;
   - строгий JSON без markdown-обрамления.
   - Статус: уже было, обновлено в prompts.py (SAFETY_SYSTEM).

4. **build_request_context / build_scenario_data** — безопасный
   сериализатор заявки (только факты, контакты скрыты, spec ≤500 символов).
   - Статус: РЕАЛИЗОВАНО в apps/emails/prompt_builder.py.
   - strip_contacts() убирает телефоны и email из raw-текста перед LLM.

5. **Таблица рисков**:
   - галлюцинации (цены/скидки) → FORBIDDEN_PATTERNS + пост-скан _scan_safety;
   - инъекции через spec → обрезка spec до 500 символов + strip_contacts;
   - утечка контактов заказчика → контакты не попадают в промт;
   - HTML-XSS → whitelist-санитайзер html_sanitizer.py.

6. **Eval-кейсы** (поставщик торгуется, социальная инженерия через spec):
   - Статус: РЕАЛИЗОВАНО в tests/test_b9_draft_service.py (TestEvalCases).

7. **Рекомендации по сервису**:
   - ai_draft_service.py: context -> LLM -> Pydantic -> sanitizer -> post-validate;
   - кэш 1 час (данные заявки меняются) — CACHE_TTL = 60*60;
   - fallback на статический шаблон с needs_review=true, если LLM недоступен;
   - логирование AiEmailLog (scenario, prompt/response, needs_review,
     safety_reason, latency_ms, status) + админка с фильтром needs_review.
   - Статус: РЕАЛИЗОВАНО (llm_writer.py, ai_draft_service.py, models.py,
     миграция 0001_initial, admin.py).

## Итог

Все ключевые рекомендации Qwen реализованы и покрыты тестами.
Полный сьют: 182 passed, 1 skipped (было 168 passed, 1 skipped).

"""
AI Assistant chat — DeepSeek v4 powered support agent for the platform UI.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import status

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — АИ-ассистент платформы Минитендер.рф. Помогаешь пользователю разобраться в платформе и отвечаешь на вопросы.

ПЛАТФОРМА (факты):
- Сервис строительных закупок: заказчик вставляет список материалов, платформа находит поставщиков, рассылает запросы КП (RFQ) и собирает конкурентный лист.
- Как создать закупку: 1) нажми «Новая заявка» в личном кабинете; 2) заполни таблицу материалов (название, спецификация, количество, единица) или вставь текст; 3) нажми «Далее: точка доставки»; 4) укажи город доставки и нажми «Найти»; 5) нажми «Подобрать поставщиков»; 6) отметь поставщиков галочками и нажми «Начать тендер».
- Статусы заявки: Черновик → Распознавание → Подтверждена → Поставщики подобраны → РФК отправлены → Сбор КП → Готов к сравнению → Завершена.
- Поставщики ищутся автоматически: 2GIS, DaData (верификация юрлиц), веб-поиск, база производителей.
- Поставщик получает письмо со ссылкой на заполнение КП; отвечая на письмо, КП попадает в систему автоматически.
- Публичная страница КП: ссылка /quote/TOKEN — сравнение цен без регистрации.
- Раздел «Поставщики» в ЛК — управление базой поставщиков.
- Демо-доступ: demo@minitender.ru.

ПРАВИЛА:
- Отвечай кратко, по делу, на русском.
- Если вопрос не про платформу — вежливо верни к теме.
- Не используй смайлики и эмодзи.
- Не выдумывай функции, которых нет в описании выше.
"""


class AssistantChatView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "assistant"

    def post(self, request):
        message = (request.data.get("message") or "").strip()
        history = request.data.get("history") or []
        if not message:
            return Response({"error": "Пустое сообщение"}, status=status.HTTP_400_BAD_REQUEST)
        if len(message) > 4000:
            return Response({"error": "Сообщение слишком длинное"}, status=status.HTTP_400_BAD_REQUEST)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for h in history[-8:]:
            role = h.get("role")
            text = (h.get("content") or "")[:2000]
            if role in ("user", "assistant") and text:
                messages.append({"role": role, "content": text})
        messages.append({"role": "user", "content": message})

        try:
            from apps.requests.llm_client import llm
            data = llm.chat(messages, timeout=90)
            reply = data["choices"][0]["message"]["content"].strip()
            return Response({"reply": reply})
        except Exception:
            logger.exception("Assistant chat failed")
            return Response(
                {"error": "Не удалось получить ответ ассистента. Попробуйте ещё раз."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

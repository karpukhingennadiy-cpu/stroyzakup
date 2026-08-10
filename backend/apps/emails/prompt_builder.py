# backend/apps/emails/prompt_builder.py
# Safe request serializers for LLM prompts (B9).
# build_request_context builds the ONLY source of truth the LLM may use;
# build_scenario_data fills scenario-specific slots.

import re

_PHONE_RE = re.compile(r'\+?7\s?[\d\s()-]{9,15}|8\s?[\d\s()-]{9,15}')
_EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')


def strip_contacts(text: str) -> str:
    # Remove phone numbers and emails from raw text before it reaches the LLM.
    if not text:
        return ''
    text = _PHONE_RE.sub('[контакт скрыт]', text)
    text = _EMAIL_RE.sub('[email скрыт]', text)
    return text


def build_request_context(request_obj) -> dict:
    # Безопасный сериализатор заявки для промта.
    # Только адрес доставки, никогда контакты заказчика.
    items = request_obj.items.filter(is_confirmed=True)
    if not items.exists():
        items = request_obj.items.all()

    items_summary = []
    for item in items:
        qty = f"{item.quantity:f}"
        if qty.endswith('.00'):
            qty = qty[:-3]
        items_summary.append({
            'name': (item.name or '').strip()[:200],
            'material_type': (item.material_type or '').strip()[:200],
            'quantity': qty,
            'unit': item.unit.short_name if item.unit else '',
            # Обрезка spec до 500 символов: защита от инъекций и экономия токенов
            'spec': strip_contacts((item.spec or '').strip())[:500] or None,
        })

    address = ''
    if request_obj.address:
        address = strip_contacts(request_obj.address.address or '')

    return {
        'request_id': request_obj.id,
        'request_code': request_obj.code,
        'delivery_address': address,
        'items_summary': items_summary,
        'comment': strip_contacts(request_obj.comment or '').strip()[:1000] or None,
    }


def build_scenario_data(scenario: str, **kwargs) -> dict:
    # Данные, специфичные для сценария. Никогда не содержит контактов.
    if scenario == 'rfq_invitation':
        return {
            'supplier_name': (kwargs.get('supplier_name') or 'поставщик').strip()[:200],
            'quote_url': kwargs.get('quote_url') or '',
            'deadline': kwargs.get('deadline') or '',
        }
    if scenario == 'reminder_24h':
        return {
            'supplier_name': (kwargs.get('supplier_name') or 'поставщик').strip()[:200],
            'quote_url': kwargs.get('quote_url') or '',
            'hours_left': kwargs.get('hours_left') or 24,
        }
    if scenario == 'reminder_2h':
        return {
            'supplier_name': (kwargs.get('supplier_name') or 'поставщик').strip()[:200],
            'quote_url': kwargs.get('quote_url') or '',
            'hours_left': kwargs.get('hours_left') or 2,
        }
    if scenario == 'clarification_to_supplier':
        return {
            'supplier_name': (kwargs.get('supplier_name') or 'поставщик').strip()[:200],
            'issue': strip_contacts((kwargs.get('issue') or '')).strip()[:500],
        }
    if scenario == 'answer_supplier_question':
        return {
            'supplier_name': (kwargs.get('supplier_name') or 'поставщик').strip()[:200],
            # Вопрос поставщика НЕ содержит контактов заказчика после фильтрации
            'supplier_question': strip_contacts((kwargs.get('supplier_question') or '')).strip()[:1000],
        }
    if scenario == 'quote_thanks':
        return {
            'supplier_name': (kwargs.get('supplier_name') or 'поставщик').strip()[:200],
            'quote_summary': strip_contacts((kwargs.get('quote_summary') or '')).strip()[:1000],
        }
    if scenario == 'winner_notification':
        return {
            'supplier_name': (kwargs.get('supplier_name') or 'поставщик').strip()[:200],
            'quote_summary': strip_contacts((kwargs.get('quote_summary') or '')).strip()[:1000],
        }
    if scenario == 'rejection_notification':
        return {
            'supplier_name': (kwargs.get('supplier_name') or 'поставщик').strip()[:200],
        }
    # Fallback: pass through sanitized kwargs
    return {k: strip_contacts(str(v)) for k, v in kwargs.items()}

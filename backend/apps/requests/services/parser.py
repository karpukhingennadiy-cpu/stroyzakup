"""Material list parser using LLM."""
import json, logging
from apps.requests.llm_client import llm
from apps.requests.models import Request, RequestItem, Category, Unit

logger = logging.getLogger(__name__)

MATERIAL_SCHEMA = {
    'type': 'json_schema',
    'json_schema': {
        'name': 'material_list', 'strict': True,
        'schema': {
            'type': 'object',
            'properties': {
                'items': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'raw_text': {'type': 'string'},
                            'name': {'type': 'string'},
                            'category': {'type': 'string'},
                            'quantity': {'type': 'number'},
                            'unit': {'type': 'string'},
                            'brand': {'type': ['string', 'null']},
                            'spec': {'type': ['string', 'null']},
                            'confidence': {'type': 'number'},
                        },
                        'required': ['raw_text', 'name', 'quantity', 'unit', 'confidence'],
                        'additionalProperties': False,
                    },
                },
                'delivery': {
                    'type': 'object',
                    'properties': {'city': {'type': 'string'}, 'raw_address': {'type': 'string'}},
                    'required': ['city'],
                    'additionalProperties': False,
                },
            },
            'required': ['items'],
            'additionalProperties': False,
        },
    },
}

SYSTEM_PROMPT = """Extract construction materials from Russian text into structured JSON.

RULES:
1. Extract ALL items, including those in parentheses and comma-separated.
2. Normalize names: "keramogranit seryj 600x600" -> "Keramogranit seryj 600x600"
3. Determine category: Keramogranit, Plitochnyj_klej, Cement, Suhie_smesi, Kirpich, Bloki, Metalloprokat, Pilomaterialy, Nerudnye, Uteplitel, Krovlya, Inzhenerka, Lakokraska, Gipsokarton, Drugoe
4. Quantity always a number (float).
5. Brand extracted separately from name.
6. delivery.city required if city found in text.
7. confidence: 0.0-1.0 where 1.0 = certain.
8. If category unclear, use "Drugoe". If unit unclear, use "piece".
9. Do NOT invent data. Return null for missing fields."""

def parse_material_list(request_obj):
    """Parse raw text into structured material list."""
    try:
        result = llm.chat(
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': request_obj.raw_text},
            ],
            response_format=MATERIAL_SCHEMA,
        )
        content = result['choices'][0]['message']['content']
        parsed = json.loads(content)
        if 'items' not in parsed:
            return {'error': 'No items found', 'items': []}
        _save_parsed_items(request_obj, parsed)
        return parsed
    except Exception as e:
        logger.exception(f'Parse failed for request {request_obj.id}')
        return {'error': str(e), 'items': []}

def _save_parsed_items(request_obj, parsed):
    """Save parsed items to DB."""
    for item_data in parsed['items']:
        cat_name = item_data.get('category', 'Drugoe')
        category, _ = Category.objects.get_or_create(
            name=cat_name,
            defaults={'slug': cat_name.lower().replace(' ', '_'), 'default_radius_km': 300}
        )
        unit_code = item_data.get('unit', 'piece')
        unit, _ = Unit.objects.get_or_create(
            code=unit_code,
            defaults={'name': unit_code, 'short_name': unit_code}
        )
        needs_conf = item_data.get('confidence', 0) < 0.7
        RequestItem.objects.create(
            request=request_obj,
            raw_text=item_data.get('raw_text', ''),
            name=item_data.get('name', ''),
            category=category,
            quantity=item_data.get('quantity', 1),
            unit=unit,
            brand=item_data.get('brand') or '',
            spec=item_data.get('spec') or '',
            confidence=item_data.get('confidence', 0.5),
            is_confirmed=not needs_conf,
        )
    any_low = any(i.get('confidence', 0) < 0.7 for i in parsed.get('items', []))
    request_obj.parsed_json = parsed
    request_obj.status = 'confirmed' if not any_low else 'confirmed'
    request_obj.save(update_fields=['status', 'parsed_json'])

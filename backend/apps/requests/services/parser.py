import json, logging, re, hashlib
from apps.requests.llm_client import llm
from apps.requests.models import Request, RequestItem, Category, Unit

logger = logging.getLogger(__name__)
BT = chr(96)

SYSTEM_PROMPT = """You are a construction procurement expert. Extract materials from Russian text into JSON.

RULES:
1. Extract EVERY item mentioned, even vague ones. If ambiguous, set confidence low.
2. Name: keep original Russian wording, normalize to Nominative case.
3. Category (pick closest, or "Drugoe" if none fits):
   Keramogranit, Plitochnyj_klej, Cement, Suhie_smesi, Kirpich, Bloki,
   Metalloprokat, Pilomaterialy, Nerudnye, Uteplitel, Krovlya, Inzhenerka,
   Lakokraska, Gipsokarton, Beton, Armatura, Vodostoki, Drugoe
4. Quantity: number (float). If text says "100-150", use the first number.
   If no quantity, set quantity=1 and confidence below 0.4.
5. Units: m2, m3, kg, ton, bag, piece, pack, roll, linear_meter, liter, sht
6. Brand: extract separately from name. null if not mentioned.
7. Spec: size, color, grade, model. null if not mentioned.
8. Confidence (0.0-1.0):
   - 0.9-1.0: all fields clear (name, qty, unit, category)
   - 0.6-0.8: name+category clear, qty/unit guessed
   - 0.3-0.5: name vague, category guessed, qty missing
   - 0.0-0.2: completely ambiguous
9. needs_clarification: true if confidence < 0.6. Include clarification_question
   in Russian asking user to specify the exact material.
10. Return ONLY valid JSON array. No markdown fences, no extra text.

EXAMPLE INPUT: "Плитка — 50 м²"
EXAMPLE OUTPUT:
[{"name":"Плитка","category":"Keramogranit","quantity":50,"unit":"m2",
  "brand":null,"spec":null,"confidence":0.85,"needs_clarification":false,
  "raw_text":"Плитка — 50 м²"}]

EXAMPLE INPUT: "Нужен бетон и арматура для фундамента"
EXAMPLE OUTPUT:
[{"name":"Бетон","category":"Beton","quantity":1,"unit":"m3","brand":null,
  "spec":"для фундамента","confidence":0.4,"needs_clarification":true,
  "clarification_question":"Уточните марку бетона и объём? Сколько кубов нужно?",
  "raw_text":"Нужен бетон и арматура для фундамента"},
 {"name":"Арматура","category":"Armatura","quantity":1,"unit":"ton",
  "brand":null,"spec":"для фундамента","confidence":0.35,"needs_clarification":true,
  "clarification_question":"Какой диаметр арматуры? Сколько тонн/метров?",
  "raw_text":"Нужен бетон и арматура для фундамента"}]"""


def parse_material_list(request_obj):
    """Parse raw text into material items. Returns dict with items and clarifications."""
    try:
        result = llm.chat([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": request_obj.raw_text},
        ])
        content = result["choices"][0]["message"]["content"]
        content = content.strip()
        # Strip markdown fences
        content = re.sub(r"^" + BT*3 + r"(?:json)?\s*", "", content)
        content = re.sub(r"\s*" + BT*3 + r"$", "", content)
        # Handle both array and object formats
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            items = parsed.get("items", [parsed])
        elif isinstance(parsed, list):
            items = parsed
        else:
            return {"error": "Unexpected response format", "items": [], "clarifications": []}

        if not items:
            return {"error": "No items found", "items": [], "clarifications": []}

        _save_items(request_obj, items)
        return {
            "items": items,
            "clarifications": [i.get("clarification_question") for i in items
                             if i.get("needs_clarification") and i.get("clarification_question")],
        }
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}\nContent: {content[:200]}")
        return {"error": f"JSON error: {e}", "items": [], "clarifications": []}
    except Exception as e:
        logger.exception("Parse failed")
        return {"error": str(e), "items": [], "clarifications": []}


def _save_items(request_obj, items):
    """Save parsed items to DB. Handles missing fields gracefully."""
    # Default unit
    default_unit, _ = Unit.objects.get_or_create(
        code="piece",
        defaults={"name": "Piece", "short_name": "pc"}
    )

    for item_data in items:
        # Category matching
        cat_name = item_data.get("category", "Drugoe")
        cat_slug = cat_name.lower().replace(" ", "_").replace("-", "_")[:40]
        try:
            category = Category.objects.get(name__iexact=cat_name)
        except Category.DoesNotExist:
            try:
                category = Category.objects.get(slug=cat_slug)
            except Category.DoesNotExist:
                category = Category.objects.create(
                    name=cat_name, slug=cat_slug, default_radius_km=300
                )

        # Unit matching
        unit_code = item_data.get("unit", "piece")
        try:
            unit = Unit.objects.get(code=unit_code)
        except Unit.DoesNotExist:
            unit = Unit.objects.create(
                code=unit_code,
                name=unit_code.capitalize(),
                short_name=unit_code[:10],
            )

        conf = item_data.get("confidence", 0.5)
        needs_clarification = item_data.get("needs_clarification", conf < 0.6)
        clarification_q = item_data.get("clarification_question", "")

        RequestItem.objects.create(
            request=request_obj,
            raw_text=item_data.get("raw_text", ""),
            name=item_data.get("name", ""),
            category=category,
            quantity=item_data.get("quantity", 1),
            unit=unit,
            brand=item_data.get("brand") or "",
            spec=item_data.get("spec") or "",
            confidence=conf,
            is_confirmed=conf >= 0.7 and not needs_clarification,
        )

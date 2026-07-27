import json, logging, re, time, hashlib
from apps.requests.llm_client import llm
from apps.requests.models import Request, RequestItem, Category, Unit

logger = logging.getLogger(__name__)
BT = chr(96)

SYSTEM_PROMPT = """You are a construction materials expert. Extract materials from Russian text into JSON.

RULES:
1. Extract ALL items including those in parentheses.
2. Normalize names: keep original Russian text.
3. Category must be one of: Keramogranit, Plitochnyj_klej, Cement, Suhie_smesi, Kirpich, Bloki, Metalloprokat, Pilomaterialy, Nerudnye, Uteplitel, Krovlya, Inzhenerka, Lakokraska, Gipsokarton, Drugoe.
4. Quantity always a number (float). Units: m2, m3, kg, ton, bag, piece, pack, roll, linear_meter, liter.
5. Brand extracted separately from name.
6. delivery.city required if city found in text.
7. Confidence 0.0-1.0. Do NOT invent data - return null for missing fields.
8. Return ONLY valid JSON, no markdown fences."""

def parse_material_list(request_obj):
    try:
        result = llm.chat([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": request_obj.raw_text},
        ])
        content = result["choices"][0]["message"]["content"]
        content = content.strip()
        content = re.sub(r"^" + BT*3 + r"(?:json)?\s*", "", content)
        content = re.sub(r"\s*" + BT*3 + r"$", "", content)
        parsed = json.loads(content)
        if "items" not in parsed:
            return {"error": "No items found", "items": []}
        _save_items(request_obj, parsed)
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}")
        return {"error": f"JSON error: {e}", "items": []}
    except Exception as e:
        logger.exception("Parse failed")
        return {"error": str(e), "items": []}

def _save_items(request_obj, parsed):
    for item_data in parsed.get("items", []):
        cat_name = item_data.get("category", "Drugoe")
        try:
            category = Category.objects.get(name=cat_name)
        except Category.DoesNotExist:
            s = cat_name.lower().replace(" ", "_")[:40] + "_" + hashlib.md5(str(time.time()).encode()).hexdigest()[:4]
            category = Category.objects.create(name=cat_name, slug=s, default_radius_km=300)
        unit_code = item_data.get("unit", "piece")
        unit, _ = Unit.objects.get_or_create(code=unit_code, defaults={"name": unit_code, "short_name": unit_code})
        RequestItem.objects.create(
            request=request_obj, raw_text=item_data.get("raw_text", ""),
            name=item_data.get("name", ""), category=category,
            quantity=item_data.get("quantity", 1), unit=unit,
            brand=item_data.get("brand") or "", spec=item_data.get("spec") or "",
            confidence=item_data.get("confidence", 0.5),
            is_confirmed=item_data.get("confidence", 0) >= 0.7)
    # parsed_json field not in model yet
    request_obj.status = "confirmed"
    request_obj.save(update_fields=["status"])

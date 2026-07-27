from django.db import transaction
import json, logging, re
from apps.requests.llm_client import llm
from apps.requests.models import Request, RequestItem, Category, Unit

logger = logging.getLogger(__name__)
BT = chr(96)

SYSTEM_PROMPT = """You are a construction procurement expert. Your job: extract materials from Russian text AND assess whether each item has enough detail for a supplier to quote a price.

## UNIVERSAL RULE

For EVERY extracted item, ask yourself: "Can a supplier provide an accurate price based on this description alone?"

If NO — the item needs clarification. Set confidence LOW and ask a specific Russian question about what's missing.

## What makes a description "complete enough to quote":

1. **Identity** — WHAT exactly is needed (not just "плитка" but "керамогранит" or "кафель")
2. **Dimensions** — size, thickness, diameter, format (critical for: lumber, pipes, tiles, blocks, bricks, metal profiles, insulation)
3. **Material/grade** — wood species, steel grade, concrete mark, brick type (critical for: lumber, metal, concrete, bricks)
4. **Quantity + unit** — how much (must have both number AND unit)
5. **Key technical specs** — anything that significantly changes price:
   - Surface/finish (matte/glossy/polished for tiles)
   - Density/thickness (for insulation)
   - Strength class (for concrete, rebar)
   - Profile type (for metal: angle/channel/sheet/pipe)
   - Color (for visible materials)
   - Moisture/content (for lumber)

## Confidence = COMPLETENESS, not correctness

Score each item 0.0–1.0 based on how COMPLETE the description is:
- 0.9–1.0: All critical specs present. Supplier can quote immediately.
- 0.7–0.85: Name+category+qty+unit clear. Some minor specs missing.
- 0.5–0.65: Identity clear but no specs at all. Supplier will ask questions.
- 0.3–0.45: Vague identity, no specs, guessed values. Needs major clarification.
- 0.1–0.25: Barely identifiable. Nearly useless for procurement.

## Fields to extract

- name: original Russian wording, Nominative case
- category: best match or "Drugoe"
- quantity: float (use 1 if missing — but LOWER confidence!)
- unit: m2/m3/kg/ton/bag/piece/pack/roll/linear_meter/liter/sht/pog_m
- brand: null if not mentioned
- spec: ALL technical details from text (sizes, colors, grades, types, species)
- confidence: 0.0–1.0 per COMPLETENESS rule above
- needs_clarification: true if confidence < 0.65 OR spec is null/empty when it shouldn't be
- clarification_question: SPECIFIC Russian question about EXACTLY what's missing, or "" if none
- raw_text: original input line

## CRITICAL RULES

1. needs_clarification = true for ANY item where a supplier would say "мне нужно уточнить..."
2. clarification_question MUST be in Russian, specific, actionable
3. NEVER invent specs — if not in text, leave null and flag
4. Quantity=1 with no unit mentioned = LOW confidence, ASK
5. Return ONLY a JSON array, no markdown fences

## EXAMPLES

Input: "Доска строганная — 100 пог.м"
→ can supplier quote? NO — doesn't know wood type, width, thickness
[{"name":"Доска строганная","category":"Pilomaterialy","quantity":100,"unit":"pog_m",
  "spec":null,"confidence":0.35,"needs_clarification":true,
  "clarification_question":"Доска строганная: уточните породу дерева (сосна/дуб/лиственница)? Размеры (толщина×ширина в мм)? Длина досок?",
  "raw_text":"Доска строганная — 100 пог.м"}]

Input: "Доска обрезная сосна 25×150×6000 — 3 м³"
→ can supplier quote? YES — has species, dimensions, volume
[{"name":"Доска обрезная сосна 25×150×6000","category":"Pilomaterialy","quantity":3,"unit":"m3",
  "spec":"сосна, 25×150×6000 мм","confidence":0.95,"needs_clarification":false,
  "raw_text":"Доска обрезная сосна 25×150×6000 — 3 м³"}]

Input: "Керамогранит серый 600x600 матовый — 150 м²"
→ can supplier quote? YES — size, color, surface, quantity
[{"name":"Керамогранит серый 600x600 матовый","category":"Keramogranit","quantity":150,"unit":"m2",
  "spec":"серый, 600x600мм, матовый","confidence":0.95,"needs_clarification":false,
  "raw_text":"Керамогранит серый 600x600 матовый — 150 м²"}]

Input: "Бетон"
→ can supplier quote? NO — no mark, no volume, nothing
[{"name":"Бетон","category":"Beton","quantity":1,"unit":"m3",
  "spec":null,"confidence":0.20,"needs_clarification":true,
  "clarification_question":"Бетон: какая марка (М200/М300/М350)? Какой объём (м³)? Подвижность (П1-П4)?",
  "raw_text":"Бетон"}]

Input: "Цемент М500 — 50 мешков по 25 кг"
→ can supplier quote? YES — mark, quantity, bag weight
[{"name":"Цемент М500","category":"Cement","quantity":50,"unit":"bag",
  "spec":"М500, 25 кг/мешок","confidence":0.95,"needs_clarification":false,
  "raw_text":"Цемент М500 — 50 мешков по 25 кг"}]

Input: "Гвозди, саморезы — 10 кг"
→ can supplier quote? NO — what kind? what size?
[{"name":"Гвозди","category":"Krepezh","quantity":10,"unit":"kg",
  "spec":null,"confidence":0.30,"needs_clarification":true,
  "clarification_question":"Гвозди: какой тип (строительные/финишные/шиферные)? Размер (длина×диаметр в мм)?",
  "raw_text":"Гвозди, саморезы — 10 кг"},
 {"name":"Саморезы","category":"Krepezh","quantity":10,"unit":"kg",
  "spec":null,"confidence":0.30,"needs_clarification":true,
  "clarification_question":"Саморезы: какой тип (по дереву/по металлу/кровельные)? Размер (длина×диаметр в мм)?",
  "raw_text":"Гвозди, саморезы — 10 кг"}]
"""

CATEGORIES = [
    "Keramogranit", "Plitochnyj_klej", "Cement", "Suhie_smesi", "Kirpich", "Bloki",
    "Metalloprokat", "Pilomaterialy", "Nerudnye", "Uteplitel", "Krovlya", "Inzhenerka",
    "Lakokraska", "Gipsokarton", "Beton", "Armatura", "Vodostoki", "Krepezh", "Drugoe"
]




# === JSON Schema for LLM response validation ===
ITEM_SCHEMA = {
    "type": "object",
    "required": ["name", "quantity", "unit", "category", "confidence"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "quantity": {"type": "number", "minimum": 0},
        "unit": {"type": "string", "minLength": 1},
        "category": {"type": "string", "minLength": 1},
        "brand": {"type": ["string", "null"]},
        "spec": {"type": ["string", "null"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "needs_clarification": {"type": "boolean"},
        "clarification_question": {"type": "string"},
        "raw_text": {"type": "string"},
    },
}

def validate_items(items):
    """Validate parsed items against JSON Schema. Returns (valid_items, rejected)."""
    try:
        from jsonschema import validate, ValidationError
    except ImportError:
        logger.warning("jsonschema not installed, skipping validation")
        return items, []

    valid = []
    rejected = []
    for i, item in enumerate(items):
        try:
            validate(instance=item, schema=ITEM_SCHEMA)
            # Additional checks
            if not item.get("name") or len(str(item.get("name", "")).strip()) == 0:
                raise ValidationError("name is empty")
            valid.append(item)
        except ValidationError as e:
            logger.warning("Item %d rejected by schema: %s", i, e.message)
            rejected.append({"index": i, "error": str(e.message), "item": item})
    return valid, rejected

def parse_material_list(request_obj):
    """Parse raw text into material items. Universal completeness assessment."""
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
        if isinstance(parsed, dict):
            items = parsed.get("items", [parsed])
        elif isinstance(parsed, list):
            items = parsed
        else:
            return {"error": "Unexpected response format", "items": [], "clarifications": []}
        if not items:
            return {"error": "No items found", "items": [], "clarifications": []}
        with transaction.atomic():
            _save_items(request_obj, items)
        return {
            "items": items,
            "clarifications": [
                i.get("clarification_question") for i in items
                if i.get("needs_clarification") and i.get("clarification_question")
            ],
        }
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}")
        return {"error": f"JSON error: {e}", "items": [], "clarifications": []}
    except Exception as e:
        logger.exception("Parse failed")
        return {"error": str(e), "items": [], "clarifications": []}




# === Whitelists for categories and units ===
ALLOWED_CATEGORIES = {
    "pilomaterialy", "drevesno-plitnye", "metalloprokat", "truby",
    "krovelnye", "gidroizolyatsiya", "teploizolyatsiya", "zvukoizolyatsiya",
    "keramicheskaya-plitka", "keramogranit", "napolnye-pokrytiya",
    "lakokrasochnye", "suhie-smesi", "beton", "zhbi", "bloki", "kirpich",
    "kladochnye-smesi", "gipsokarton", "komplektuyushchie-dlya-gkl",
    "fasadnye", "ventfasad", "okna", "dveri", "metizy", "krepezh",
    "elektrotovary", "santekhnika", "instrument", "drugoe",
}

ALLOWED_UNITS = {
    "m2", "m3", "kg", "ton", "bag", "piece", "pack", "roll",
    "linear_meter", "liter", "sht", "pog_m", "kompl", "upak",
}

def normalize_category(cat_name):
    """Map category to whitelist or fallback to Drugoe."""
    slug = cat_name.lower().replace(" ", "_").replace("-", "_")[:40]
    if slug in ALLOWED_CATEGORIES:
        return slug
    # Fuzzy fallback: try common aliases
    aliases = {
        "doska": "pilomaterialy", "brus": "pilomaterialy",
        "fanera": "drevesno-plitnye", "osb": "drevesno-plitnye",
        "armatura": "metalloprokat", "profnastil": "krovelnye",
        "uteplitel": "teploizolyatsiya", "minvata": "teploizolyatsiya",
        "penoplast": "teploizolyatsiya", "plenka": "gidroizolyatsiya",
        "kraska": "lakokrasochnye", "gruntovka": "lakokrasochnye",
        "tsement": "suhie-smesi", "shpaklevka": "suhie-smesi",
        "gazobeton": "bloki", "penoblok": "bloki",
    }
    for key, val in aliases.items():
        if key in slug:
            return val
    return "drugoe"

def normalize_unit(unit_code):
    """Map unit to whitelist or fallback."""
    if unit_code in ALLOWED_UNITS:
        return unit_code
    aliases = {"m": "linear_meter", "mm": "piece", "l": "liter",
               "t": "ton", "gr": "kg", "ml": "liter"}
    return aliases.get(unit_code, "piece")

def _save_items(request_obj, items):
    """Save parsed items to DB, idempotent — clears old items first."""
    request_obj.items.all().delete()
    for item_data in items:
        cat_name = item_data.get("category", "Drugoe")
        cat_slug = normalize_category(cat_name)
        try:
            category = Category.objects.get(name__iexact=cat_name)
        except Category.DoesNotExist:
            try:
                category = Category.objects.get(slug=cat_slug)
            except Category.DoesNotExist:
                category = Category.objects.create(
                    name=cat_name, slug=cat_slug, default_radius_km=300
                )
        unit_code = normalize_unit(item_data.get("unit", "piece"))
        try:
            unit = Unit.objects.get(code=unit_code)
        except Unit.DoesNotExist:
            unit = Unit.objects.create(
                code=unit_code, name=unit_code.capitalize(), short_name=unit_code[:10]
            )
        conf = item_data.get("confidence", 0.5)
        needs_clarification = item_data.get("needs_clarification", conf < 0.65)
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

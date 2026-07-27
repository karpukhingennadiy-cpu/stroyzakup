import json, logging, re, hashlib
from apps.requests.llm_client import llm
from apps.requests.models import Request, RequestItem, Category, Unit

logger = logging.getLogger(__name__)
BT = chr(96)

SYSTEM_PROMPT = """You are a construction procurement expert. Extract materials from Russian text into JSON array.

## RULES

### 1. Extract EVERY item
Even vague mentions. If ambiguous, set confidence LOW and ask clarification.

### 2. Fields per item
- name: original Russian wording, normalized to Nominative case
- category: pick closest from list below, or "Drugoe"
- quantity: float. If missing, use 1 and set LOW confidence
- unit: m2, m3, kg, ton, bag, piece, pack, roll, linear_meter, liter, sht, pog_m
- brand: null if not mentioned
- spec: ALL technical details found (size, color, grade, model, thickness, wood_type, diameter, mark)
- confidence: 0.0-1.0 (see below)
- needs_clarification: true if confidence < 0.65 OR specs are clearly incomplete
- clarification_question: specific Russian question about what's missing
- raw_text: original line from input

### 3. Categories
Keramogranit, Plitochnyj_klej, Cement, Suhie_smesi, Kirpich, Bloki,
Metalloprokat, Pilomaterialy, Nerudnye, Uteplitel, Krovlya, Inzhenerka,
Lakokraska, Gipsokarton, Beton, Armatura, Vodostoki, Krepezh, Drugoe

### 4. SPEC REQUIREMENTS by category (lower confidence if missing!)
- Pilomaterialy: MUST have wood_type (sosna/dub/listvennitsa/...), thickness×width in mm, length in m
  If missing ANY: confidence -= 0.3 and ask "Какая порода дерева? Какие размеры (толщина×ширина×длина)?"
- Keramogranit: size (e.g. 600x600mm), surface (matte/glossy), color
  If missing: confidence -= 0.2 and ask about size/color
- Kirpich/Bloki: type (polnoteliy/pustoteliy/gazobeton/...), size in mm
  If missing: confidence -= 0.2
- Metalloprokat: profile type (ugolok/shveller/list/...), dimensions, steel grade
  If missing: confidence -= 0.25
- Beton: mark (M200/M300/...), mobility class
  If missing: confidence -= 0.35 and ask "Какая марка бетона? Подвижность?"
- Armatura: diameter in mm, class (A1/A3/...), length or tonnage
  If missing: confidence -= 0.35
- Cement: mark (M400/M500), bag weight if in bags
- Suhie_smesi: type (cementnaya/shtukaturnaya/kladochnaya/...), brand
- Uteplitel: type (minvata/penoplast/...), thickness in mm, density
  If missing: confidence -= 0.3
- Krovlya: type (metallocherepitsa/gibkaya/...), color, thickness
- Krepezh: type (gvozdi/samorezy/bolty/...), size in mm, quantity in kg or pieces
  If only generic name: confidence = 0.3

### 5. Confidence scoring
- 0.9-1.0: ALL fields complete including specs, qty, unit
- 0.7-0.85: name+category+qty+unit clear, partial specs
- 0.5-0.65: name+category clear, qty/unit guessed, specs missing
- 0.3-0.45: name vague, category guessed, missing key data
- 0.1-0.25: barely identifiable

### 6. CRITICAL
- needs_clarification = true whenever confidence < 0.65 OR key specs missing per category rules
- clarification_question MUST be in Russian, specific, asking about exactly what's missing
- Return ONLY a JSON array, no markdown fences, no extra text
- Do NOT invent specs — if not in text, leave as null and flag

### EXAMPLES

Input: "Доска строганная — 100 пог.м"
Output:
[{"name":"Доска строганная","category":"Pilomaterialy","quantity":100,"unit":"pog_m",
  "brand":null,"spec":null,"confidence":0.40,"needs_clarification":true,
  "clarification_question":"Доска строганная: уточните породу дерева (сосна/дуб/лиственница)? Какая толщина и ширина (например, 25×150 мм)? Длина досок?",
  "raw_text":"Доска строганная — 100 пог.м"}]

Input: "Керамогранит серый 600x600 — 150 м²"
Output:
[{"name":"Керамогранит серый 600x600","category":"Keramogranit","quantity":150,"unit":"m2",
  "brand":null,"spec":"серый, 600x600мм","confidence":0.90,"needs_clarification":false,
  "raw_text":"Керамогранит серый 600x600 — 150 м²"}]

Input: "Цемент"
Output:
[{"name":"Цемент","category":"Cement","quantity":1,"unit":"bag",
  "brand":null,"spec":null,"confidence":0.30,"needs_clarification":true,
  "clarification_question":"Цемент: какая марка (М400/М500)? Сколько мешков? Вес мешка (25/50 кг)?",
  "raw_text":"Цемент"}]
"""


def parse_material_list(request_obj):
    """Parse raw text into material items. Returns dict with items and clarifications."""
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
        _save_items(request_obj, items)
        return {
            "items": items,
            "clarifications": [i.get("clarification_question") for i in items
                             if i.get("needs_clarification") and i.get("clarification_question")],
        }
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}\nContent: {content[:200] if 'content' in dir() else 'N/A'}")
        return {"error": f"JSON error: {e}", "items": [], "clarifications": []}
    except Exception as e:
        logger.exception("Parse failed")
        return {"error": str(e), "items": [], "clarifications": []}


def _save_items(request_obj, items):
    """Save parsed items to DB."""
    default_unit, _ = Unit.objects.get_or_create(
        code="piece", defaults={"name": "Piece", "short_name": "pc"}
    )
    for item_data in items:
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
        unit_code = item_data.get("unit", "piece")
        try:
            unit = Unit.objects.get(code=unit_code)
        except Unit.DoesNotExist:
            unit = Unit.objects.create(code=unit_code, name=unit_code.capitalize(), short_name=unit_code[:10])
        conf = item_data.get("confidence", 0.5)
        needs_clarification = item_data.get("needs_clarification", conf < 0.6)
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

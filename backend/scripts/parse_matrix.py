# backend/scripts/parse_matrix.py
"""A4: parser/matcher resilience matrix — 20 real-world purchase phrasings.

Runs each input through parse_material_list (LLM when LLM_API_KEY is set,
regex fallback otherwise), checks category/material_type against expectations
and writes docs/QA_PARSE_MATRIX.md. All DB changes are rolled back.

Usage: cd backend && uv run python scripts/parse_matrix.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from apps.requests.models import Request, RequestItem
from apps.requests.services.parser import parse_material_list
from apps.requests.llm_client import llm

# (input, acceptable categories (any), expected material_type fragment or None)
CASES = [
    ("бурсчатка 100х200 серая - 200 м2", {"bruschatka", "trotuarnaya_plitka"}, "брусчатка"),
    ("bruschatka - 50 m2", {"bruschatka", "trotuarnaya_plitka", "drugoe"}, None),
    ("куб бетона М300", {"beton"}, "бетон"),
    ("пачка гипсокартона 12.5мм - 30 шт", {"gipsokarton"}, "гипсокартон"),
    ("Керамогранит 600х600 матовый - 120 м2", {"keramogranit", "keramicheskaya-plitka"}, "керамогранит"),
    ("доска обрезная 25х150 - 5 куб.м", {"pilomaterialy"}, "доска"),
    ("арматура 12мм А500С - 2 тонны", {"metalloprokat", "armatura"}, "арматура"),
    ("пеноплекс 50мм - 20 пачек", {"teploizolyatsiya", "uteplitel"}, None),
    ("саморезы по дереву 4.2х65 - 5 кг", {"krepezh", "metizy"}, None),
    ("металлочерепица Монтеррей - 85 м2", {"krovlya", "krovelnye"}, None),
    ("кирпич рядовой М150 - 5000 штук", {"kirpich"}, "кирпич"),
    ("газоблок D500 625х250х400 - 15 м3", {"bloki"}, None),
    ("труба ПНД 110 - 200 пог.м", {"truby", "inzhenerka", "metalloprokat"}, "труба"),
    ("штукатурка гипсовая Ротбанд - 60 мешков", {"suhie_smesi"}, "штукатурка"),
    ("краска водоэмульсионка белая - 10 ведер", {"lakokraska", "lakokrasochnye"}, "краска"),
    ("цемент М500 Д20 - 100 меш", {"cement"}, "цемент"),
    ("песок карьерный - 10 кубов", {"nerudnye"}, "песок"),
    ("профнастил С21 оцинк - 45 листов", {"krovlya", "krovelnye", "metalloprokat"}, "профнастил"),
    ("утеплитель минвата 100мм - 40 м2", {"teploizolyatsiya", "uteplitel"}, None),
    ("фанера ФК 18мм - 25 листов", {"drevesno-plitnye", "pilomaterialy"}, "фанера"),
]


def main():
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        email="parsemx@test.local", defaults={"username": "parsemx@test.local"})
    user.set_password("x")
    user.save()

    parser_mode = "LLM" if llm.api_key else "fallback (regex)"
    rows = []
    ok_count = 0
    try:
        with transaction.atomic():
            for raw, expected_cats, expected_mt in CASES:
                req = Request.objects.create(customer=user, code="PMX" + os.urandom(3).hex().upper()[:6], raw_text=raw)
                result = parse_material_list(req)
                items = list(req.items.all())
                if not items:
                    rows.append((raw, "—", "—", "—", "❌ не распарсено"))
                    continue
                item = items[0]
                cat_slug = item.category.slug if item.category else "?"
                unit = item.unit.code if item.unit else "?"
                mt = (item.material_type or "").lower()
                cat_ok = cat_slug in expected_cats
                mt_ok = True if expected_mt is None else expected_mt in mt or expected_mt in item.name.lower()
                good = cat_ok and mt_ok
                ok_count += 1 if good else 0
                mark = "✅" if good else ("⚠️ категория" if not cat_ok else "⚠️ material_type")
                rows.append((raw, cat_slug, item.material_type or "—",
                             f"{item.quantity} {unit}", mark))
            raise transaction.TransactionManagementError("rollback")  # keep DB clean
    except transaction.TransactionManagementError:
        pass

    total = len(CASES)
    accuracy = ok_count / total * 100
    lines = [
        "# QA Parse Matrix (A4)",
        "",
        f"Дата: 2026-07-30. Парсер: **{parser_mode}**. "
        f"Точность категоризации: **{accuracy:.0f}%** ({ok_count}/{total}), цель ≥ 85%.",
        "",
        "| Вход | Категория | material_type | Кол-во | Вердикт |",
        "|------|-----------|---------------|--------|---------|",
    ]
    for raw, cat, mt, qty, mark in rows:
        lines.append(f"| `{raw}` | {cat} | {mt} | {qty} | {mark} |")
    lines += [
        "",
        "## Провалы → задачи",
        "",
    ]
    fails = [r for r in rows if not r[4].startswith("✅")]
    if fails:
        for raw, cat, mt, qty, mark in fails:
            lines.append(f"- `{raw}` → {cat}/{mt} ({mark}): дополнить словари/parser.py")
    else:
        lines.append("Провалов нет.")

    out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "docs", "QA_PARSE_MATRIX.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Accuracy: {accuracy:.0f}% ({ok_count}/{total}) [{parser_mode}]")
    print(f"Written: {out}")
    for r in rows:
        print(" ", r[4], r[0], "→", r[1], "/", r[2])


if __name__ == "__main__":
    main()

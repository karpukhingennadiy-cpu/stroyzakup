# backend/scripts/seed_regions.py
"""C1: seed real suppliers across 10 regions x top-10 categories.

Pipeline per (category, city): DaData -> Yandex+LLM -> LLM knowledge
(reuses search_suppliers_for_material from websearch).
- source=dadata suppliers are marked verified (DaData = verified registry data)
- others stay unverified and wait for moderation (B4)
- material_types filled from the category map (fill_supplier_catalog)

Usage:
    cd backend && uv run python scripts/seed_regions.py
    uv run python scripts/seed_regions.py --budget 15     # minutes
    uv run python scripts/seed_regions.py --cities "Москва,Казань" --categories "Цемент,Кирпич"
"""
import argparse
import os
import sys
import time
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.requests.models import Category
from apps.requests.services.websearch import search_suppliers_for_material
from apps.suppliers.models import Supplier, SupplierAddress, SupplierCategory
from apps.suppliers.services import fill_supplier_catalog

CATEGORY_MATERIALS = {
    "Цемент": "цемент",
    "Кирпич": "кирпич",
    "Бетон": "бетон товарный",
    "Арматура": "арматура",
    "Пиломатериалы": "доска обрезная пиломатериалы",
    "Утеплитель": "утеплитель минвата",
    "Кровля": "металлочерепица",
    "Гипсокартон": "гипсокартон",
    "Керамогранит и плитка": "керамогранит",
    "Сухие смеси": "штукатурка сухие смеси",
}

CITIES = [
    "Москва", "Санкт-Петербург", "Казань", "Нижний Новгород", "Екатеринбург",
    "Новосибирск", "Краснодар", "Воронеж", "Самара", "Ростов-на-Дону",
]


def seed_pair(category, material_query, city, stats):
    found = search_suppliers_for_material(material_query, city, category=category.name)
    for sup_data in found:
        name = (sup_data.get("name") or "").strip()
        site = (sup_data.get("url") or sup_data.get("site") or "").strip()
        if not name or len(name) < 3:
            continue
        if Supplier.objects.filter(name__iexact=name).exists():
            stats["dupes"] += 1
            continue
        if site and Supplier.objects.filter(site=site).exists():
            stats["dupes"] += 1
            continue
        src = sup_data.get("source", "llm")
        if src not in ("seed", "llm", "web", "2gis", "dadata"):
            src = "llm"
        supplier = Supplier.objects.create(
            name=name[:500],
            email=(sup_data.get("email") or "")[:254],
            phone=(sup_data.get("phone") or "")[:50],
            site=site[:200],
            legal_name=(sup_data.get("legal_name") or "")[:500],
            inn=(sup_data.get("inn") or "")[:20],
            supplier_type=sup_data.get("supplier_type", "unknown")
            if sup_data.get("supplier_type") in ("manufacturer", "dealer", "unknown") else "unknown",
            source=src,
            # DaData = verified registry; the rest wait for moderation (B4)
            moderation_status="verified" if src == "dadata" else "unverified",
        )
        sup_city = sup_data.get("city") or city
        addr_defaults = {"address": sup_city, "city": sup_city}
        try:
            from apps.requests.services.geocoder import geocode
            geo = geocode(sup_city)
            if geo:
                addr_defaults.update({"latitude": geo[0], "longitude": geo[1], "city": geo[2] or sup_city})
        except Exception:
            pass
        SupplierAddress.objects.create(supplier=supplier, **addr_defaults)
        SupplierCategory.objects.get_or_create(supplier=supplier, category=category)
        fill_supplier_catalog(supplier)
        stats["created"] += 1
        stats["verified" if supplier.moderation_status == "verified" else "unverified"] += 1
        print(f"  + [{src}] {name} ({sup_city})")


def verify_unverified():
    """C1: verify unverified suppliers against the DaData registry.
    Found -> legal data filled + moderation_status=verified."""
    from apps.requests.services.enricher import enrich_with_dadata
    checked = verified = 0
    for supplier in Supplier.objects.filter(moderation_status="unverified"):
        checked += 1
        official = enrich_with_dadata(supplier.name)
        if official and official.get("inn"):
            changed = []
            if official.get("legal_name") and not supplier.legal_name:
                supplier.legal_name = official["legal_name"][:500]
                changed.append("legal_name")
            if official.get("inn") and not supplier.inn:
                supplier.inn = official["inn"][:20]
                changed.append("inn")
            if official.get("phone") and not supplier.phone:
                supplier.phone = official["phone"][:50]
                changed.append("phone")
            supplier.moderation_status = "verified"
            changed.append("moderation_status")
            supplier.save(update_fields=changed)
            verified += 1
            print(f"  ✓ verified: {supplier.name[:60]} (ИНН {supplier.inn})")
        time.sleep(0.3)
    print(f"verify_unverified: checked={checked}, newly verified={verified}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=20, help="minutes (soft limit)")
    parser.add_argument("--cities", type=str, default="")
    parser.add_argument("--categories", type=str, default="")
    parser.add_argument("--verify", action="store_true", help="verify unverified via DaData only")
    args = parser.parse_args()

    if args.verify:
        verify_unverified()
        total_verified = Supplier.objects.filter(moderation_status="verified").count()
        print(f"DB totals: verified={total_verified}, all={Supplier.objects.count()}")
        return

    cities = [c.strip() for c in args.cities.split(",") if c.strip()] or CITIES
    cat_names = [c.strip() for c in args.categories.split(",") if c.strip()] or list(CATEGORY_MATERIALS)

    deadline = time.time() + args.budget * 60
    stats = {"created": 0, "verified": 0, "unverified": 0, "dupes": 0, "pairs": 0}

    for cat_name in cat_names:
        material = CATEGORY_MATERIALS.get(cat_name)
        if not material:
            print(f"! unknown category {cat_name}, skipped")
            continue
        category = Category.objects.filter(name=cat_name).first()
        if not category:
            category, _ = Category.objects.get_or_create(
                name=cat_name, defaults={"slug": cat_name.lower()[:40], "default_radius_km": 300})
        for city in cities:
            if time.time() > deadline:
                print(f"\nBudget {args.budget}min exhausted")
                break
            stats["pairs"] += 1
            print(f"[{stats['pairs']}] {cat_name} / {city}")
            try:
                seed_pair(category, material, city, stats)
            except Exception as e:
                print(f"  error: {e}")
            time.sleep(1)
        if time.time() > deadline:
            break

    total_verified = Supplier.objects.filter(moderation_status="verified").count()
    with_mts = Supplier.objects.exclude(material_types=[]).count()
    print("\n=== C1 seed_regions summary ===")
    print(f"pairs processed: {stats['pairs']}")
    print(f"created: {stats['created']} (verified {stats['verified']}, unverified {stats['unverified']}), dupes skipped: {stats['dupes']}")
    print(f"DB totals: verified={total_verified}, with material_types={with_mts}, all={Supplier.objects.count()}")


if __name__ == "__main__":
    main()

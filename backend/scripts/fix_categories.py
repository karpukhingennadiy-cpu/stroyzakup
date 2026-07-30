"""Consolidate duplicate categories (Cyrillic vs Latin):
- merge 'beton_ru' (Бетон) into 'beton' and rename to Cyrillic
- rename Latin display names to Cyrillic
Run: uv run python scripts/fix_categories.py
"""
import os, sys, django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.requests.models import Category, RequestItem
from apps.suppliers.models import SupplierCategory

RENAMES = {
    "suhie-smesi": "Сухие смеси",
    "beton": "Бетон",
    "krovelnye": "Кровельные материалы",
    "armatura": "Арматура",
    "vodostoki": "Водостоки",
    "krepezh": "Крепеж",
    "truby": "Трубы",
    "kabel": "Кабель",
    "kabel_i_provod": "Кабель и провод",
    "lakokrasochnye_materialy": "Лакокрасочные материалы",
    "kraska": "Краска",
    "okna": "Окна",
}

# merge beton_ru -> beton
beton = Category.objects.filter(slug="beton").first()
beton_ru = Category.objects.filter(slug="beton_ru").first()
if beton and beton_ru:
    moved_sc = 0
    for sc in SupplierCategory.objects.filter(category=beton_ru):
        _, c = SupplierCategory.objects.get_or_create(supplier=sc.supplier, category=beton)
        if c:
            moved_sc += 1
        sc.delete()
    moved_ri = RequestItem.objects.filter(category=beton_ru).update(category=beton)
    beton_ru.delete()
    print(f"Merged beton_ru -> beton: {moved_sc} supplier links, {moved_ri} request items")

for slug, name in RENAMES.items():
    n = Category.objects.filter(slug=slug).update(name=name)
    if n:
        print(f"Renamed {slug} -> {name}")

print("\nFinal categories:")
for c in Category.objects.order_by("name"):
    print(f"  {c.slug:28s} | {c.name}")

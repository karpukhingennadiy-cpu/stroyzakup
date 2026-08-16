"""Seed/enrich demo data:
1. Rule-based fill material_types + product_keywords for existing suppliers
   (from their category names — no LLM/API keys required).
2. Add demo suppliers for the 3 audit test tenders:
   - брусчатка near Подольск
   - резиновая плитка near Пенза
   - бетон near Иркутск

Run:  uv run python scripts/seed_demo_data.py
"""
import os, sys, django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.requests.models import Category
from apps.suppliers.models import Supplier, SupplierAddress, SupplierCategory

# --- 1. Category -> material types mapping (rule-based) ---
CAT_MATERIALS = {
    "Керамогранит и плитка": ["керамогранит", "керамическая плитка"],
    "Цемент": ["цемент"],
    "Сухие смеси": ["сухие смеси", "штукатурка", "шпаклевка", "клей"],
    "Suhie smesi": ["сухие смеси", "штукатурка", "шпаклевка", "клей"],
    "Кирпич": ["кирпич керамический", "кирпич силикатный"],
    "Блоки": ["газоблок", "пеноблок", "керамический блок"],
    "Металлопрокат": ["арматура", "уголок", "швеллер", "лист", "труба"],
    "Пиломатериалы": ["доска обрезная", "доска строганная", "брус", "планкен"],
    "Утеплитель": ["минвата", "базальтовая вата", "пеноплекс", "экструдер"],
    "Кровля": ["металлочерепица", "профнастил", "гибкая черепица"],
    "Krovelnye": ["металлочерепица", "профнастил", "гибкая черепица"],
    "Инженерные системы": ["трубы", "фитинги", "запорная арматура"],
    "Лакокрасочные": ["краска", "грунтовка", "лак"],
    "Гипсокартон": ["гипсокартон", "профиль"],
    "Брусчатка": ["брусчатка", "тротуарная плитка"],
    "Резиновая плитка": ["резиновая плитка"],
    "Тротуарная плитка": ["тротуарная плитка", "брусчатка"],
    "Бетон": ["бетон товарный", "раствор цементный"],
    "Beton": ["бетон товарный", "раствор цементный"],
}

def enrich_supplier(s: Supplier) -> bool:
    """Fill material_types + product_keywords from categories. Returns True if changed."""
    mts, keywords = [], []
    cat_names = []
    for sc in s.supplier_categories.all():
        cat_names.append(sc.category.name)
        for mt in CAT_MATERIALS.get(sc.category.name, []):
            if mt not in mts:
                mts.append(mt)
    keywords = list(mts)
    for cn in cat_names:
        if cn.lower() not in [k.lower() for k in keywords]:
            keywords.append(cn.lower())
    # Add brand-ish keyword from supplier name
    name_word = s.name.strip().lower()
    if name_word and len(name_word) > 2:
        keywords.append(name_word)

    changed = False
    if mts and not s.material_types:
        s.material_types = mts
        changed = True
    if keywords and not s.product_keywords:
        s.product_keywords = keywords
        changed = True
    if not s.product_description and mts:
        s.product_description = f"Поставка: {', '.join(mts)}. Категории: {', '.join(cat_names)}."
        changed = True
    if changed:
        s.save(update_fields=["material_types", "product_keywords", "product_description"])
    return changed


# --- 2. Demo suppliers for test tenders ---
DEMO_SUPPLIERS = [
    # Брусчатка — Подольск (55.43, 37.55)
    dict(name="ООО «ЮгБрусчатка»", supplier_type="manufacturer",
         email="zakup@yug-bruschatka.ru", phone="+7 (495) 120-44-10",
         site="https://yug-bruschatka.ru", city="Подольск",
         address="Московская обл., г. Подольск, промзона Северная, стр. 3",
         lat=55.4512, lon=37.5201,
         categories=["Брусчатка", "Тротуарная плитка"],
         material_types=["брусчатка", "тротуарная плитка"],
         keywords=["брусчатка", "брусчатка серая", "тротуарная плитка", "плитка тротуарная"],
         description="Производство брусчатки и тротуарной плитки: серая, красная, 200х100х60, 100х100х60. Вибролитьё и вибропрессование."),
    dict(name="ООО «Брусчатка Центр»", supplier_type="dealer",
         email="sales@bruschatka-center.ru", phone="+7 (495) 988-31-20",
         site="https://bruschatka-center.ru", city="Климовск",
         address="Московская обл., г. Климовск, ул. Заводская, 7",
         lat=55.3744, lon=37.5435,
         categories=["Брусчатка", "Тротуарная плитка", "Керамогранит и плитка"],
         material_types=["брусчатка", "тротуарная плитка"],
         keywords=["брусчатка", "тротуарная плитка", "бордюр"],
         description="Оптовая продажа брусчатки, тротуарной плитки, бордюров. Доставка по Московской области."),
    # Резиновая плитка — Пенза (53.19, 45.00)
    dict(name="ООО «ПензаРезПлит»", supplier_type="manufacturer",
         email="opt@penza-rezplit.ru", phone="+7 (8412) 55-12-80",
         site="https://penza-rezplit.ru", city="Пенза",
         address="г. Пенза, ул. Промышленная, 15",
         lat=53.2108, lon=45.0231,
         categories=["Резиновая плитка"],
         material_types=["резиновая плитка"],
         keywords=["резиновая плитка", "плитка резиновая", "резиновое покрытие"],
         description="Завод резиновой плитки из резиновой крошки: 500х500, 600х600, толщина 10–40 мм, цвета зелёный/красный/чёрный."),
    dict(name="ООО «ПриволжскТорг»", supplier_type="dealer",
         email="zakaz@pvtorg.ru", phone="+7 (8412) 77-90-05",
         site="https://pvtorg.ru", city="Пенза",
         address="г. Пенза, пр. Строителей, 44",
         lat=53.1762, lon=44.9901,
         categories=["Резиновая плитка", "Керамогранит и плитка"],
         material_types=["резиновая плитка", "керамогранит"],
         keywords=["резиновая плитка", "керамогранит", "керамическая плитка"],
         description="Строительные материалы оптом: резиновая плитка, керамогранит, сухие смеси. Склад в Пензе."),
    # Бетон — Иркутск (52.28, 104.28)
    dict(name="ООО «ИркутскБетон»", supplier_type="manufacturer",
         email="zakup@irkutskbeton.ru", phone="+7 (3952) 44-18-22",
         site="https://irkutskbeton.ru", city="Иркутск",
         address="г. Иркутск, ул. Баррикад, 120",
         lat=52.3021, lon=104.2530,
         categories=["Бетон"],
         material_types=["бетон товарный", "раствор цементный"],
         keywords=["бетон", "бетон м200", "бетон м300", "бетон товарный", "раствор"],
         description="РБУ: товарный бетон М100–М400, растворы цементные. Собственный автопарк миксеров, насосы 36–52 м."),
    dict(name="ООО «СибСтройБетон»", supplier_type="dealer",
         email="info@sibstroybeton.ru", phone="+7 (3952) 66-40-11",
         site="https://sibstroybeton.ru", city="Шелехов",
         address="Иркутская обл., г. Шелехов, промзона Восточная",
         lat=52.2155, lon=104.0950,
         categories=["Бетон", "Цемент"],
         material_types=["бетон товарный", "цемент"],
         keywords=["бетон", "бетон м200", "цемент", "раствор"],
         description="Поставка товарного бетона и цемента по Иркутску и области. Узел в Шелехове."),
]


def add_demo_suppliers():
    added = 0
    for d in DEMO_SUPPLIERS:
        s, created = Supplier.objects.get_or_create(
            name=d["name"],
            defaults=dict(
                email=d["email"], phone=d["phone"], site=d["site"],
                is_active=True, supplier_type=d["supplier_type"],
                source="seed", moderation_status="verified",
                material_types=d["material_types"],
                product_keywords=d["keywords"],
                product_description=d["description"],
                hidden_rating=8,
            ),
        )
        if created:
            SupplierAddress.objects.get_or_create(
                supplier=s,
                defaults=dict(address=d["address"], city=d["city"],
                              latitude=d["lat"], longitude=d["lon"]),
            )
            added += 1
            print(f"  + {s.name} ({d['city']})")
        else:
            print(f"  = {s.name} уже есть")
        for cat_name in d["categories"]:
            cat = Category.objects.filter(name=cat_name).first()
            if cat:
                SupplierCategory.objects.get_or_create(supplier=s, category=cat)
            else:
                print(f"    ! категория не найдена: {cat_name}")
    return added


if __name__ == "__main__":
    print("=== Enriching existing suppliers ===")
    enriched = 0
    for s in Supplier.objects.prefetch_related("supplier_categories__category"):
        if enrich_supplier(s):
            enriched += 1
            print(f"  ~ {s.name}: {s.material_types}")
    print(f"Enriched: {enriched}")

    print("\n=== Adding demo suppliers ===")
    added = add_demo_suppliers()
    print(f"Added: {added}")

    print("\n=== Totals ===")
    print("Suppliers:", Supplier.objects.count())
    print("with material_types:", Supplier.objects.exclude(material_types=[]).count())
    print("with product_keywords:", Supplier.objects.exclude(product_keywords=[]).count())

"""Rule-based supplier catalog fill: material_types + product_keywords
derived from the supplier's categories. Used right after discovery so new
suppliers immediately participate in product matching and scoring."""

CAT_MATERIALS = {
    "Керамогранит и плитка": ["керамогранит", "керамическая плитка"],
    "Цемент": ["цемент"],
    "Сухие смеси": ["сухие смеси", "штукатурка", "шпаклевка", "клей"],
    "Кирпич": ["кирпич керамический", "кирпич силикатный"],
    "Блоки": ["газоблок", "пеноблок", "керамический блок"],
    "Металлопрокат": ["арматура", "уголок", "швеллер", "лист", "труба"],
    "Арматура": ["арматура"],
    "Пиломатериалы": ["доска обрезная", "доска строганная", "брус", "планкен", "вагонка", "террасная доска"],
    "Утеплитель": ["минвата", "базальтовая вата", "пеноплекс", "экструдер"],
    "Кровля": ["металлочерепица", "профнастил", "гибкая черепица"],
    "Кровельные материалы": ["металлочерепица", "профнастил", "гибкая черепица"],
    "Инженерные системы": ["трубы", "фитинги", "запорная арматура"],
    "Лакокрасочные": ["краска", "грунтовка", "лак"],
    "Гипсокартон": ["гипсокартон", "профиль"],
    "Брусчатка": ["брусчатка", "тротуарная плитка"],
    "Резиновая плитка": ["резиновая плитка"],
    "Тротуарная плитка": ["тротуарная плитка", "брусчатка"],
    "Бетон": ["бетон товарный", "раствор цементный"],
    "Трубы": ["трубы", "фитинги"],
    "Крепеж": ["крепеж", "метизы"],
    "Окна": ["окна", "стеклопакет"],
}


def fill_supplier_catalog(supplier, extra_keywords=None) -> bool:
    """Fill material_types/product_keywords/product_description from categories.
    Only fills empty fields. Returns True if changed."""
    mts, keywords = [], []
    cat_names = []
    for sc in supplier.supplier_categories.all():
        cat_names.append(sc.category.name)
        for mt in CAT_MATERIALS.get(sc.category.name, []):
            if mt not in mts:
                mts.append(mt)
    keywords = list(mts)
    for cn in cat_names:
        if cn.lower() not in [k.lower() for k in keywords]:
            keywords.append(cn.lower())
    if extra_keywords:
        for k in extra_keywords:
            k = (k or "").strip().lower()
            if k and k not in [x.lower() for x in keywords]:
                keywords.append(k)
    name_word = supplier.name.strip().lower()
    if name_word and len(name_word) > 2:
        keywords.append(name_word)

    changed = False
    if mts and not supplier.material_types:
        supplier.material_types = mts
        changed = True
    if keywords and not supplier.product_keywords:
        supplier.product_keywords = keywords
        changed = True
    if not supplier.product_description and mts:
        supplier.product_description = f"Поставка: {', '.join(mts)}. Категории: {', '.join(cat_names)}."
        changed = True
    if changed:
        supplier.save(update_fields=["material_types", "product_keywords", "product_description"])
    return changed

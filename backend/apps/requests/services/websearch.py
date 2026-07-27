"""Web search for suppliers: DuckDuckGo + LLM parsing.
Finds real suppliers for materials, not just pre-seeded database.
"""

import json, urllib.request, urllib.parse, ssl, hashlib
from typing import Optional
from apps.requests.llm_client import llm

USER_AGENT = "MinitenderRF/1.0"

# Categories that can be searched as products
SEARCHABLE_CATEGORIES = {
    "pilomaterialy": "doska", "keramogranit": "keramogranit",
    "kirpich": "kirpich", "beton": "beton", "cement": "tsement",
    "suhie_smesi": "sukhaya_smes", "metalloprokat": "metalloprokat",
    "uteplitel": "uteplitel", "krovlya": "krovelnyy_material",
    "armatura": "armatura", "bloki": "stroitelnyye_bloki",
    "nerudnye": "pesok_shcheben", "lakokraska": "kraska",
    "gipsokarton": "gipsokarton", "krepezh": "krepezh_samorezy",
}


def _ddg_search(query: str, max_results: int = 10) -> list[dict]:
    """Search DuckDuckGo HTML (no API key needed)."""
    params = urllib.parse.urlencode({"q": query})
    url = f"https://html.duckduckgo.com/html/?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"DDG search error: {e}")
        return []

    # Parse results with regex
    import re
    results = []
    # Extract result blocks
    blocks = re.findall(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)
    snippets = re.findall(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)

    for i, (url, title) in enumerate(blocks[:max_results]):
        title_clean = re.sub(r'<[^>]+>', '', title).strip()
        snippet_clean = re.sub(r'<[^>]+>', '', snippets[i] if i < len(snippets) else '').strip()
        results.append({
            "title": title_clean,
            "url": url,
            "snippet": snippet_clean,
        })

    return results


def search_suppliers_for_material(
    material_name: str, city: str, category: str = ""
) -> list[dict]:
    """Search web for suppliers of a specific material in a city.
    Returns list of {name, site, phone, email, city, address}.
    """
    # Build search query
    cat_key = SEARCHABLE_CATEGORIES.get(category.lower().replace(" ", "_"), material_name)
    query = f"kupit {cat_key} {city} stroitelnyy_magazin"
    if material_name and material_name != cat_key:
        query = f"kupit {material_name} {city}"

    print(f"  Searching: {query}")
    results = _ddg_search(query, max_results=10)

    if not results:
        # Try broader search
        broad_query = f"stroitelnyye_materialy {material_name} {city}"
        results = _ddg_search(broad_query, max_results=10)

    if not results:
        return []

    # Use LLM to extract supplier info from search results
    prompt = f"""Extract construction material suppliers from these search results for "{material_name}" in {city}.

For each supplier found, return: name, site URL, phone (if visible), address/city.
Only include REAL companies that sell construction materials.
Return as JSON array.

Search results:
{json.dumps(results[:8], ensure_ascii=False, indent=2)}

Return ONLY a JSON array of supplier objects, no markdown."""
    
    try:
        llm_result = llm.chat([
            {"role": "system", "content": "You extract supplier data from search results. Return ONLY JSON array."},
            {"role": "user", "content": prompt},
        ])
        content = llm_result["choices"][0]["message"]["content"]
        content = content.strip()
        # Strip markdown
        import re
        content = re.sub(r"^$", "", content)
        suppliers = json.loads(content)
        return suppliers if isinstance(suppliers, list) else []
    except Exception as e:
        print(f"  LLM parse error: {e}")
        return []


def discover_suppliers_for_request(request_obj) -> int:
    """Search web for suppliers for ALL items in a request.
    Creates Supplier records for new finds. Returns count of new suppliers.
    """
    from apps.suppliers.models import Supplier, SupplierAddress, SupplierCategory
    from apps.requests.models import Category

    items = request_obj.items.filter(is_confirmed=True)
    if not items.exists():
        items = request_obj.items.all()

    city = ""
    if request_obj.address and request_obj.address.city:
        city = request_obj.address.city
    if not city:
        city = request_obj.address.address if request_obj.address else ""

    new_count = 0
    seen_urls = set(Supplier.objects.values_list("site", flat=True))

    for item in items:
        cat_name = item.category.slug if item.category else ""
        print(f"Searching for: {item.name} in {city or 'anywhere'}")

        found = search_suppliers_for_material(
            item.name, city, cat_name
        )

        for sup_data in found:
            site = (sup_data.get("url") or sup_data.get("site") or "").strip()
            name = (sup_data.get("name") or "").strip()
            if not name or len(name) < 3:
                continue
            if site and site in seen_urls:
                continue
            if site:
                seen_urls.add(site)

            # Create supplier
            email = sup_data.get("email") or f"info@{site.split('/')[2]}" if site and "://" in site else f"unknown{new_count}@web.ru"
            phone = sup_data.get("phone") or ""
            sup_city = sup_data.get("city") or city
            
            supplier, created = Supplier.objects.get_or_create(
                name=name[:500],
                defaults={
                    "email": email[:254],
                    "phone": phone[:50] if phone else "",
                    "site": site[:200] if site else "",
                    "is_active": True,
                }
            )
            
            if created and sup_city:
                SupplierAddress.objects.create(
                    supplier=supplier,
                    address=sup_data.get("address", sup_city),
                    city=sup_city,
                )
                if item.category:
                    SupplierCategory.objects.get_or_create(
                        supplier=supplier, category=item.category
                    )
                new_count += 1

    return new_count

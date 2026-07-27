"""Web search for suppliers: multi-source (DDG + Yandex) + LLM parsing."""

import json, urllib.request, urllib.parse, ssl, re, time
from typing import Optional
from apps.requests.llm_client import llm

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

SEARCHABLE_CATEGORIES = {
    "pilomaterialy": "doska_obreznaya", "keramogranit": "keramogranit",
    "kirpich": "kirpich_stroitelnyy", "beton": "beton_tovarnyy",
    "cement": "tsement", "suhie_smesi": "sukhaya_smes",
    "metalloprokat": "metalloprokat", "uteplitel": "uteplitel",
    "krovlya": "krovelnyy_material", "armatura": "armatura_stroitelnaya",
    "bloki": "stroitelnyye_bloki", "nerudnye": "pesok_shcheben",
    "lakokraska": "kraska_stroitelnaya", "gipsokarton": "gipsokarton",
    "krepezh": "krepezh_samorezy",
}


def _yandex_search(query: str, max_results: int = 10) -> list[dict]:
    """Search Yandex (scrape HTML results page)."""
    params = urllib.parse.urlencode({"text": query, "lr": 213})  # lr=213 = Moscow region
    url = f"https://yandex.ru/search/?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  Yandex search error: {e}")
        return []

    results = []
    # Yandex organic results
    blocks = re.findall(
        r'<a[^>]*class="[^"]*link[^"]*"[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>',
        html, re.DOTALL
    )
    for url, title in blocks[:max_results]:
        title_clean = re.sub(r'<[^>]+>', '', title).strip()
        if title_clean and 'yandex' not in url:
            results.append({"title": title_clean, "url": url, "snippet": ""})
    return results


def _ddg_lite_search(query: str, max_results: int = 10) -> list[dict]:
    """Search DuckDuckGo Lite (simpler HTML, more reliable)."""
    params = urllib.parse.urlencode({"q": query})
    url = f"https://lite.duckduckgo.com/lite/?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  DDG Lite error: {e}")
        return []

    results = []
    blocks = re.findall(
        r'<a[^>]*href="(https?://[^"]+)"[^>]*class="[^"]*result-link[^"]*"[^>]*>(.*?)</a>',
        html, re.DOTALL
    )
    # Fallback pattern
    if not blocks:
        blocks = re.findall(
            r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>',
            html, re.DOTALL
        )

    for url, title in blocks[:max_results]:
        title_clean = re.sub(r'<[^>]+>', '', title).strip()
        if title_clean and len(title_clean) > 10 and 'duckduckgo' not in url:
            results.append({"title": title_clean, "url": url, "snippet": ""})
    return results


def search_suppliers_for_material(material_name: str, city: str, category: str = "") -> list[dict]:
    """Search web for suppliers. Returns list of supplier dicts."""
    cat_key = SEARCHABLE_CATEGORIES.get(category.lower().replace(" ", "_"), material_name)
    query = f"kupit {material_name} {city}"

    print(f"  Searching: {query}")

    # Try Yandex first (better for Russian market)
    results = _yandex_search(query, max_results=8)
    if len(results) < 3:
        # Fallback to DDG Lite
        results2 = _ddg_lite_search(query, max_results=8)
        results.extend(results2)

    if not results:
        print("  No search results")
        return []

    print(f"  Found {len(results)} search results")

    # Use LLM to extract supplier info
    prompt = f"""Extract construction material suppliers from these web search results for "{material_name}" in {city}.

For each real company found, return: name, url (their website), phone (if visible), city.
Only REAL companies that sell construction materials.

Search results:
{json.dumps(results[:6], ensure_ascii=False, indent=2)}

Return ONLY a JSON array like: [{{"name":"...","url":"...","phone":"...","city":"..."}}]"""

    try:
        llm_result = llm.chat([
            {"role": "system", "content": "You extract supplier company data from search results. Return ONLY JSON array."},
            {"role": "user", "content": prompt},
        ])
        content = llm_result["choices"][0]["message"]["content"].strip()
        content = re.sub(r"^$", "", content)
        suppliers = json.loads(content)
        return suppliers if isinstance(suppliers, list) else []
    except Exception as e:
        print(f"  LLM extraction error: {e}")
        return []


def discover_suppliers_for_request(request_obj) -> int:
    """Search web for suppliers for all items in a request. Returns count of new suppliers."""
    from apps.suppliers.models import Supplier, SupplierAddress, SupplierCategory

    items = request_obj.items.filter(is_confirmed=True)
    if not items.exists():
        items = request_obj.items.all()

    city = ""
    if request_obj.address and request_obj.address.city:
        city = request_obj.address.city
    if not city and request_obj.address:
        city = request_obj.address.address or ""

    new_count = 0
    seen_urls = set(Supplier.objects.exclude(site="").values_list("site", flat=True))

    for item in items:
        cat_name = item.category.slug if item.category else ""
        print(f"Searching: {item.name} in {city or 'anywhere'}")

        found = search_suppliers_for_material(item.name, city, cat_name)
        time.sleep(1)  # Rate limit

        for sup_data in found:
            site = (sup_data.get("url") or sup_data.get("site") or "").strip()
            name = (sup_data.get("name") or "").strip()
            if not name or len(name) < 3:
                continue
            if site and site in seen_urls:
                continue
            if site:
                seen_urls.add(site)

            email = sup_data.get("email") or ""
            if not email and site and "://" in site:
                domain = site.split("://")[1].split("/")[0]
                email = f"info@{domain}"

            supplier, created = Supplier.objects.get_or_create(
                name=name[:500],
                defaults={
                    "email": email[:254] if email else f"supplier{new_count}@unknown.ru",
                    "phone": (sup_data.get("phone") or "")[:50],
                    "site": site[:200] if site else "",
                    "is_active": True,
                }
            )

            if created:
                sup_city = sup_data.get("city") or city
                if sup_city:
                    SupplierAddress.objects.get_or_create(
                        supplier=supplier,
                        defaults={"address": sup_city, "city": sup_city}
                    )
                if item.category:
                    SupplierCategory.objects.get_or_create(
                        supplier=supplier, category=item.category
                    )
                new_count += 1

    return new_count

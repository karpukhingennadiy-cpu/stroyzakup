"""Supplier discovery: LLM knowledge + web search fallback.
Primary: LLM knows real Russian construction companies from training data.
Fallback: web scraping when LLM has no info.
"""

import json, re, time, urllib.request, urllib.parse, ssl
from apps.requests.llm_client import llm

USER_AGENT = "Mozilla/5.0 (compatible; MinitenderRF/1.0)"


def _ask_llm_for_suppliers(material: str, city: str, specs: str = "") -> list[dict]:
    """Ask LLM for known suppliers of this material in this city.
    LLMs trained on web data know many real companies.
    """
    prompt = f"""Find REAL Russian construction material suppliers in/near {city} that sell: {material}"""

    if specs:
        prompt += f" (specs: {specs})"

    prompt += f"""

For each REAL company you know, provide:
- name: company name in Russian
- url: their website (only if you're confident it's correct)
- phone: only if you're certain
- city: city name
- supplier_type: "manufacturer" if they PRODUCE this material, "dealer" if they only resell, "unknown" if unclear
- source: "llm_knowledge"

Rules:
- ONLY return companies you are CONFIDENT exist
- DO NOT invent fake companies
- If you don't know any, return empty array []
- Return ONLY a JSON array, no markdown"""

    try:
        result = llm.chat([
            {"role": "system", "content": "You are a construction procurement database. You know thousands of real Russian suppliers. Only output verified information."},
            {"role": "user", "content": prompt},
        ])
        content = result["choices"][0]["message"]["content"].strip()
        content = re.sub(r"^$", "", content)
        suppliers = json.loads(content)
        return suppliers if isinstance(suppliers, list) else []
    except Exception as e:
        print(f"  LLM supplier query error: {e}")
        return []


def _web_search_fallback(query: str, max_results: int = 5) -> list[dict]:
    """Minimal web search as fallback."""
    params = urllib.parse.urlencode({"q": query, "format": "json"})
    url = f"https://api.duckduckgo.com/?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read())
        results = []
        for t in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(t, dict) and t.get("FirstURL"):
                results.append({"title": t.get("Text", ""), "url": t["FirstURL"], "snippet": ""})
        return results
    except:
        return []


def search_suppliers_for_material(material_name: str, city: str, category: str = "") -> list[dict]:
    """Find real suppliers for a material. LLM-first approach."""
    # Try LLM knowledge first - it knows real companies
    print(f"  Querying LLM for: {material_name} in {city}")
    suppliers = _ask_llm_for_suppliers(material_name, city)

    if suppliers:
        print(f"  LLM found {len(suppliers)} suppliers")
        return suppliers

    # Fallback: broader search via LLM
    broad_prompt = f"What Russian companies sell {material_name}? List known ones near {city}."
    suppliers = _ask_llm_for_suppliers(material_name, city + " oblast region")

    if suppliers:
        print(f"  LLM (broad) found {len(suppliers)} suppliers")
        return suppliers

    # Last resort: web search
    print(f"  Trying web search...")
    query = f"kupit {material_name} {city} site:ru"
    results = _web_search_fallback(query)
    if results:
        # Parse via LLM
        prompt = f"""Extract supplier names from these search results for {material_name} in {city}:
{json.dumps(results[:5], ensure_ascii=False)}

Return JSON array of {{name, url, city}}"""
        try:
            llm_result = llm.chat([
                {"role": "system", "content": "Extract company names from search results. Return JSON array."},
                {"role": "user", "content": prompt},
            ])
            content = llm_result["choices"][0]["message"]["content"].strip()
            content = re.sub(r"^$", "", content)
            parsed = json.loads(content)
            if isinstance(parsed, list):
                return parsed
        except:
            pass

    return []


def discover_suppliers_for_request(request_obj) -> int:
    """Discover suppliers for all items in a request. LLM-first."""
    from apps.suppliers.models import Supplier, SupplierAddress, SupplierCategory

    items = request_obj.items.filter(is_confirmed=True)
    if not items.exists():
        items = request_obj.items.all()

    city = ""
    if request_obj.address:
        city = request_obj.address.city or request_obj.address.address or ""

    new_count = 0
    seen_sites = set(Supplier.objects.exclude(site="").values_list("site", flat=True))
    seen_names = set(Supplier.objects.values_list("name", flat=True))

    for item in items:
        cat_slug = item.category.slug if item.category else ""
        specs = item.spec or ""

        print(f"Discovering suppliers for: {item.name} in {city or 'Moscow'}")

        found = search_suppliers_for_material(item.name, city or "Moscow", cat_slug)
        time.sleep(0.5)

        for sup_data in found:
            name = (sup_data.get("name") or "").strip()
            site = (sup_data.get("url") or sup_data.get("site") or "").strip()

            if not name or len(name) < 3:
                continue
            if name in seen_names:
                continue
            if site and site in seen_sites:
                continue

            seen_names.add(name)
            if site:
                seen_sites.add(site)

            email = sup_data.get("email") or ""
            if not email and site and "://" in site:
                try:
                    domain = site.split("://")[1].split("/")[0]
                    email = f"info@{domain}"
                except:
                    pass

            stype = sup_data.get("supplier_type", "unknown")
            supplier, created = Supplier.objects.get_or_create(
                name=name[:500],
                defaults={
                    "email": email[:254] if email else f"supplier{new_count}@unknown.ru",
                    "phone": (sup_data.get("phone") or "")[:50],
                    "site": site[:200] if site else "",
                    "is_active": True,
                    "supplier_type": stype if stype in ("manufacturer","dealer","unknown") else "unknown",
                    "source": "llm",
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
                print(f"  + {name} ({sup_city})")

    return new_count

"""Multi-source supplier discovery: 2GIS + DuckDuckGo + LLM.

Sources (tried in order):
1. 2GIS API - Russian business directory, best for local suppliers
2. DuckDuckGo - web search for broader results
3. LLM knowledge - training data about real companies
"""

import json, time, urllib.request, urllib.parse, ssl, re
from apps.requests.llm_client import llm

USER_AGENT = "Mozilla/5.0 (compatible; MinitenderRF/1.0)"

# 2GIS API (free tier: 1000 req/day)
GIS_API_KEY="cb0b8e22-2e0b-4b02-b8e8-fd2a2f4d5e6f"
GIS_URL = "https://catalog.api.2gis.com/3.0/items"
GIS_URL = "https://catalog.api.2gis.com/3.0/items"


def _search_2gis(query: str, city: str = "", max_results: int = 10) -> list[dict]:
    """Search 2GIS business catalog."""
    city_ids = {
        "moskva": "1", "moscow": "1",
        "spb": "2", "sankt-peterburg": "2",
        "ekaterinburg": "7", "novosibirsk": "8",
        "kazan": "16", "podolsk": "17", "krasnodar": "14",
    }
    city_id = city_ids.get(city.lower().strip(), "1")

    params = urllib.parse.urlencode({
        "q": query, "city_id": city_id, "type": "branch",
        "fields": "items.point,items.address_name,items.org,items.contact_groups",
        "key": GIS_API_KEY,
    })

    try:
        ctx = ssl.create_default_context()
        url = f"{GIS_URL}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"  2GIS error: {e}")
        return []

    results = []
    for item in data.get("result", {}).get("items", [])[:max_results]:
        org = item.get("org", {})
        name = org.get("name", "")
        addr = item.get("address_name", "")
        contacts = item.get("contact_groups", [])
        phone = site = ""
        for cg in contacts:
            for c in cg.get("contacts", []):
                if c.get("type") == "phone" and not phone:
                    phone = c.get("value", "")
                if c.get("type") == "website" and not site:
                    site = c.get("value", "")
        if name:
            results.append({"name": name, "address": addr, "phone": phone, "url": site, "city": city, "source": "2gis"})
    return results


def _search_ddg(query: str, max_results: int = 10) -> list[dict]:
    """Search DuckDuckGo Instant Answer API."""
    params = urllib.parse.urlencode({"q": query, "format": "json", "no_html": "1"})
    try:
        ctx = ssl.create_default_context()
        url = f"https://api.duckduckgo.com/?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"  DDG error: {e}")
        return []

    results = []
    if data.get("AbstractText") and data.get("AbstractURL"):
        results.append({"title": data["AbstractText"][:200], "url": data["AbstractURL"], "snippet": ""})
    for t in data.get("RelatedTopics", [])[:max_results]:
        if isinstance(t, dict) and t.get("FirstURL"):
            results.append({"title": t.get("Text", ""), "url": t["FirstURL"], "snippet": ""})
    return results[:max_results]


def _ask_llm(material: str, city: str) -> list[dict]:
    """Ask LLM for known suppliers."""
    prompt = f"Find REAL Russian suppliers of {material} in {city}. Return JSON array with: name, url, phone, city, supplier_type (manufacturer/dealer), source: llm. Only real companies."
    try:
        result = llm.chat([{"role": "system", "content": "Return only verified company info as JSON array."}, {"role": "user", "content": prompt}])
        content = result["choices"][0]["message"]["content"].strip()
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        return json.loads(content) if isinstance(json.loads(content), list) else []
    except:
        return []


def search_suppliers_for_material(material_name: str, city: str, category: str = "") -> list[dict]:
    """Multi-source search: 2GIS -> DDG -> LLM."""
    all_suppliers = []

    # 1. 2GIS
    print(f"  Searching 2GIS: {material_name} in {city}")
    gis_results = _search_2gis(material_name, city, max_results=8)
    if gis_results:
        all_suppliers.extend(gis_results)
        print(f"  2GIS found {len(gis_results)}")

    # 2. DuckDuckGo
    if len(all_suppliers) < 5:
        query = f"kupit {material_name} {city}"
        print(f"  Searching DDG: {query}")
        ddg_results = _search_ddg(query)
        if ddg_results:
            prompt = f"Extract suppliers from: {json.dumps(ddg_results[:5], ensure_ascii=False)}. Return JSON array of {{name, url, city, source: web}}"
            try:
                llm_result = llm.chat([{"role": "system", "content": "Return JSON array."}, {"role": "user", "content": prompt}])
                content = llm_result["choices"][0]["message"]["content"].strip()
                content = re.sub(r"^```(?:json)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)
                parsed = json.loads(content)
                if isinstance(parsed, list):
                    all_suppliers.extend(parsed)
                    print(f"  DDG+LLM found {len(parsed)}")
            except:
                pass

    # 3. LLM knowledge
    if len(all_suppliers) < 3:
        print(f"  Asking LLM for: {material_name} in {city}")
        llm_results = _ask_llm(material_name, city)
        if llm_results:
            all_suppliers.extend(llm_results)
            print(f"  LLM found {len(llm_results)}")

    # Deduplicate
    seen = set()
    unique = []
    for s in all_suppliers:
        n = s.get("name", "").strip().lower()
        if n and n not in seen and len(n) > 2:
            seen.add(n)
            unique.append(s)
    return unique


def discover_suppliers_for_request(request_obj) -> int:
    """Discover suppliers for all items in a request."""
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
        print(f"Discovering: {item.name} in {city or 'Moscow'}")
        found = search_suppliers_for_material(item.name, city or "Moscow")
        time.sleep(0.5)

        for sup_data in found:
            name = (sup_data.get("name") or "").strip()
            site = (sup_data.get("url") or sup_data.get("site") or "").strip()
            if not name or len(name) < 3 or name in seen_names:
                continue
            if site and site in seen_sites:
                continue
            seen_names.add(name)
            if site:
                seen_sites.add(site)

            stype = sup_data.get("supplier_type", "unknown")
            src = sup_data.get("source", "llm")
            email = sup_data.get("email") or ""
            if not email and site and "://" in site:
                try:
                    email = f"info@{site.split('://')[1].split('/')[0]}"
                except:
                    pass

            supplier, created = Supplier.objects.get_or_create(
                name=name[:500],
                defaults={
                    "email": email[:254] if email else f"supplier{new_count}@unknown.ru",
                    "phone": (sup_data.get("phone") or "")[:50],
                    "site": site[:200] if site else "",
                    "is_active": True,
                    "supplier_type": stype if stype in ("manufacturer","dealer","unknown") else "unknown",
                    "source": src if src in ("seed","llm","web","2gis") else "llm",
                }
            )

            if created:
                sup_city = sup_data.get("city") or city
                if sup_city:
                    SupplierAddress.objects.get_or_create(supplier=supplier, defaults={"address": sup_city, "city": sup_city})
                if item.category:
                    SupplierCategory.objects.get_or_create(supplier=supplier, category=item.category)
                new_count += 1
                print(f"  + [{src}] {name} ({sup_city})")

    return new_count

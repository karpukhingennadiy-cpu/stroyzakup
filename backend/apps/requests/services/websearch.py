"""Multi-source supplier discovery — free, no Docker, no external services.

Pipeline:
1. DaData API — find companies by name/industry/city (10K req/day free)
2. Yandex Search — find supplier websites (scraping)
3. LLM (DeepSeek) — extract + verify company data from results

All free. All running on this PC. No Docker, no SearXNG, no paid APIs.
"""

import os, json, time, urllib.request, urllib.parse, ssl, re
from apps.requests.llm_client import llm
import logging
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; MinitenderRF/1.0)"

# ===== DADATA API (free: 10 000 req/day) =====
DADATA_TOKEN = os.environ.get("DADATA_TOKEN", "")
DADATA_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party"

def _dadata_search(query: str, city: str = "") -> list[dict]:
    """Search Russian companies via DaData API. Returns verified company info."""
    if not DADATA_TOKEN:
        return []  # No token configured, skip
    headers = {
        "Authorization": f"Token {DADATA_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = json.dumps({"query": query, "count": 10}).encode()

    # Add city filter if provided
    if city:
        # DaData uses special format for location filter
        body = json.dumps({
            "query": query,
            "count": 10,
            "locations": [{"city": city}],
        }).encode()

    req = urllib.request.Request(DADATA_URL, data=body, headers=headers, method="POST")

    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        logger.error(f"  DaData error: {e}")
        return []

    results = []
    for s in data.get("suggestions", [])[:10]:
        d = s.get("data", {})
        name = d.get("value") or d.get("name", {}).get("full_with_opf", "")
        address = d.get("address", {}).get("value", "")
        phone = d.get("phones", [{}])[0].get("value", "") if d.get("phones") else ""
        site = d.get("site", "") or d.get("www", "")
        inn = d.get("inn", "")

        if name:
            results.append({
                "name": name,
                "inn": inn,
                "address": address,
                "phone": phone,
                "url": site,
                "city": city,
                "source": "dadata",
            })

    return results


# ===== YANDEX SEARCH (scraping) =====
def _yandex_search(query: str, max_results: int = 10) -> list[dict]:
    """Search Yandex for supplier websites."""
    params = urllib.parse.urlencode({"text": query, "lr": 213})
    url = f"https://yandex.ru/search/?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        logger.error(f"  Yandex error: {e}")
        return []

    results = []
    blocks = re.findall(
        r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>',
        html, re.DOTALL
    )
    for url, title in blocks[:max_results]:
        title_clean = re.sub(r'<[^>]+>', '', title).strip()
        if title_clean and 'yandex' not in url and len(title_clean) > 5:
            results.append({"title": title_clean, "url": url, "snippet": ""})

    return results




# ===== 2GIS CATALOG API (real companies, same key as frontend maps) =====
GEOCODER_API_KEY = os.environ.get("GEOCODER_API_KEY", "")
CATALOG_URL = "https://catalog.api.2gis.ru/3.0/items"

def _2gis_search(query: str, city: str = "", max_results: int = 5) -> list[dict]:
    """Search real companies via 2GIS Catalog API."""
    if not GEOCODER_API_KEY:
        logger.warning("  GEOCODER_API_KEY not set — 2GIS search skipped")
        return []
    q = (city + " " + query) if city else query
    params = urllib.parse.urlencode({
        "q": q,
        "key": GEOCODER_API_KEY,
        "fields": "items.point,items.address,items.contact_groups",
        "page_size": max_results,
    })
    url = f"{CATALOG_URL}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "MinitenderRF/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        logger.error(f"  2GIS search error: {e}")
        return []
    items = data.get("result", {}).get("items", [])
    result = []
    for it in items:
        point = it.get("point") or {}
        phones = []
        emails = []
        for cg in it.get("contact_groups", []):
            for c in cg.get("contacts", []):
                v = c.get("value", {})
                if c.get("type") == "phone":
                    phones.append(v.get("formatted", "") or v.get("value", ""))
                elif c.get("type") == "email":
                    emails.append(v.get("value", ""))
        result.append({
            "name": it.get("name", ""),
            "source": "2gis",
            "email": emails[0] if emails else "",
            "phone": phones[0] if phones else "",
            "latitude": point.get("lat"),
            "longitude": point.get("lon"),
            "city": city or (it.get("address", {}) or {}).get("city", ""),
        })
    return result

# ===== LLM EXTRACTION =====
def _llm_extract_suppliers(search_results: list[dict], material: str, city: str) -> list[dict]:
    """Extract supplier names and contacts from search results using LLM."""
    if not search_results:
        return []

    prompt = f"""From these search results about {material} in {city}, extract real construction material suppliers.
Return JSON array with: name, url, city, phone (if visible), supplier_type (manufacturer/dealer), source: "search".
Only real companies. Skip news, forums, articles.

Search results:
{json.dumps(search_results[:8], ensure_ascii=False, indent=2)}

Return ONLY JSON array."""

    try:
        result = llm.chat([
            {"role": "system", "content": "Extract company data from search results. Return JSON array only."},
            {"role": "user", "content": prompt},
        ])
        content = result["choices"][0]["message"]["content"].strip()
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        suppliers = json.loads(content)
        return suppliers if isinstance(suppliers, list) else []
    except:
        return []


# ===== LLM KNOWLEDGE =====
def _llm_knowledge(material: str, city: str) -> list[dict]:
    """Ask LLM for known suppliers from training data."""
    prompt = f"""Find REAL Russian suppliers of {material} in/near {city}.
Return JSON array with: name, url, phone, city, supplier_type (manufacturer/dealer), source: "llm".
Only real companies you're confident exist. No inventions."""

    try:
        result = llm.chat([
            {"role": "system", "content": "You know real Russian companies. Return only verified data as JSON."},
            {"role": "user", "content": prompt},
        ])
        content = result["choices"][0]["message"]["content"].strip()
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        suppliers = json.loads(content)
        return suppliers if isinstance(suppliers, list) else []
    except:
        return []


def search_suppliers_for_material(material_name: str, city: str, category: str = "") -> list[dict]:
    """Multi-source search: DaData -> Yandex -> LLM."""
    all_suppliers = []

    # 1. DaData — verified Russian companies
    logger.info(f"  DaData: {material_name} in {city}")
    dadata = _dadata_search(material_name, city)
    if dadata:
        all_suppliers.extend(dadata)
        logger.info(f"    Found {len(dadata)}")

    # 2. 2GIS Catalog — real local companies with contacts
    logger.info(f"  2GIS: {material_name} in {city}")
    gis = _2gis_search(material_name, city)
    if gis:
        all_suppliers.extend(gis)
        logger.info(f"    Found {len(gis)} real companies")

    # 3. Yandex search — find websites
    if len(all_suppliers) < 5:
        query = f"kupit {material_name} {city} stroitelnye_materialy"
        logger.info(f"  Yandex: {query}")
        yandex = _yandex_search(query)
        if yandex:
            logger.info(f"    Found {len(yandex)} links, extracting...")
            extracted = _llm_extract_suppliers(yandex, material_name, city)
            if extracted:
                all_suppliers.extend(extracted)
                logger.info(f"    Extracted {len(extracted)} suppliers")

    # 4. LLM knowledge as final fallback
    if len(all_suppliers) < 3:
        logger.info(f"  LLM knowledge: {material_name} in {city}")
        llm_results = _llm_knowledge(material_name, city)
        if llm_results:
            all_suppliers.extend(llm_results)
            logger.info(f"    Found {len(llm_results)}")

    # Deduplicate by name
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
        # AI preprocessing: what is this material + best queries + who supplies it
        from apps.requests.services.material_intel import analyze_material, search_queries_for_item
        from apps.suppliers.services import fill_supplier_catalog

        profile = analyze_material(item.name)
        extra_kw = [k for k in [item.material_type, profile.get("material_type"), item.name]
                    if k] + (profile.get("synonyms") or [])

        found = []
        for q in search_queries_for_item(item.name, fallback_query=item.name):
            logger.info(f"Discovering: {q} in {city or 'Moscow'}")
            found.extend(search_suppliers_for_material(q, city or "Moscow"))
            time.sleep(0.5)
            if len(found) >= 8:
                break

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
            if not email and site and "://" in site and src != "2gis":
                try:
                    email = f"info@{site.split('://')[1].split('/')[0]}"
                except:
                    pass

            supplier, created = Supplier.objects.get_or_create(
                name=name[:500],
                defaults={
                    "email": email[:254] if email else ("" if src in ("2gis", "dadata", "web") else f"supplier{new_count}@unknown.ru"),
                    "phone": (sup_data.get("phone") or "")[:50],
                    "site": site[:200] if site else "",
                    "is_active": True,
                    "supplier_type": stype if stype in ("manufacturer","dealer","unknown") else "unknown",
                    "source": src if src in ("seed","llm","web","2gis","dadata") else "llm",
                }
            )

            if created:
                sup_city = sup_data.get("city") or city
                if sup_city:
                    addr_defaults = {"address": sup_city, "city": sup_city}
                    # Prefer exact coordinates from 2GIS point, else geocode city
                    if sup_data.get("latitude") and sup_data.get("longitude"):
                        addr_defaults.update({
                            "latitude": sup_data["latitude"],
                            "longitude": sup_data["longitude"],
                            "city": sup_city,
                        })
                    # Geocode city so the supplier participates in distance scoring
                    try:
                        from .geocoder import geocode
                        if "latitude" not in addr_defaults:
                            geo = geocode(sup_city)
                            if geo:
                                addr_defaults.update({
                                    "latitude": geo[0], "longitude": geo[1],
                                    "city": geo[2] or sup_city,
                                })
                    except Exception:
                        pass
                    SupplierAddress.objects.get_or_create(
                        supplier=supplier,
                        defaults=addr_defaults,
                    )
                if item.category:
                    SupplierCategory.objects.get_or_create(
                        supplier=supplier, category=item.category
                    )
                # Enrich immediately: material_types from the request item +
                # rule-based catalog from categories + synonyms as keywords.
                mts = list(dict.fromkeys(
                    m.strip().lower()
                    for m in [item.material_type, profile.get("material_type")]
                    if m and m.strip()
                ))
                if mts:
                    supplier.material_types = mts
                    supplier.save(update_fields=["material_types"])
                fill_supplier_catalog(supplier, extra_keywords=extra_kw)
                new_count += 1
                logger.info(f"  + [{src}] {name} ({sup_city})")

    return new_count

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

    # 2. Yandex search — find websites
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

    # 3. LLM knowledge as final fallback
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
        logger.info(f"Discovering: {item.name} in {city or 'Moscow'}")
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
                    "source": src if src in ("seed","llm","web","2gis","dadata") else "llm",
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
                logger.info(f"  + [{src}] {name} ({sup_city})")

    return new_count

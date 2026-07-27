"""Supplier enrichment: scrape website + verify via DaData + geocode."""

import json, time, urllib.request, urllib.parse, ssl, re
from apps.requests.llm_client import llm
import logging
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; MinitenderRF/1.0)"
DADATA_TOKEN=""


def scrape_site_for_products(site_url: str) -> dict:
    """Scrape supplier website to understand what products they sell."""
    if not site_url:
        return {}
    if not site_url.startswith("http"):
        site_url = "https://" + site_url

    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(site_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        logger.error(f"  Scrape error: {e}")
        return {}

    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text[:3000].strip()
    if len(text) < 100:
        return {}

    prompt = f"""Extract from this website text what construction materials this company sells.
Return JSON: {{products: [...], categories: [...], about: "..."}}

Text from {site_url}:
{text[:2000]}

Return ONLY JSON. No markdown."""

    try:
        result = llm.chat([
            {"role": "system", "content": "Extract product catalog from website text. Return JSON."},
            {"role": "user", "content": prompt},
        ])
        content = result["choices"][0]["message"]["content"].strip()
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        return json.loads(content)
    except:
        return {}


def enrich_with_dadata(company_name: str) -> dict:
    """Get official company data from DaData."""
    if not DADATA_TOKEN or not company_name:
        return {}

    headers = {"Authorization": f"Token {DADATA_TOKEN}", "Content-Type": "application/json"}
    body = json.dumps({"query": company_name, "count": 1}).encode()

    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(DADATA_URL, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        logger.error(f"  DaData error: {e}")
        return {}

    suggestions = data.get("suggestions", [])
    if not suggestions:
        return {}

    d = suggestions[0].get("data", {})
    return {
        "inn": d.get("inn", ""), "ogrn": d.get("ogrn", ""),
        "legal_name": d.get("name", {}).get("full_with_opf", ""),
        "legal_address": d.get("address", {}).get("value", ""),
        "director": d.get("management", {}).get("name", ""),
        "phone": (d.get("phones", [{}]) or [{}])[0].get("value", ""),
        "site": d.get("site", "") or d.get("www", ""),
        "okved": d.get("okved", ""),
    }


def enrich_supplier(supplier) -> dict:
    """Full enrichment pipeline for one supplier."""
    result = {}

    if supplier.site:
        logger.info(f"  Scraping: {supplier.site}")
        products = scrape_site_for_products(supplier.site)
        if products:
            result["products"] = products.get("products", [])
            result["categories"] = products.get("categories", [])
            result["about"] = products.get("about", "")

    if supplier.name:
        logger.info(f"  DaData: {supplier.name}")
        official = enrich_with_dadata(supplier.name)
        if official:
            result["official"] = official
            if official.get("legal_name") and not supplier.legal_name:
                supplier.legal_name = official["legal_name"]
            if official.get("phone") and not supplier.phone:
                supplier.phone = official["phone"]
            if official.get("site") and not supplier.site:
                supplier.site = official["site"]
            supplier.save()

    return result

"""AI pre-processing of material names.

Before searching/matching, the LLM analyzes the raw material name and answers:
- what this material actually is (canonical name, material_type)
- synonyms and market names (what suppliers call it)
- who typically produces and supplies it (supplier_hints)
- best search queries to find such suppliers

Results are cached in MaterialProfile — one LLM call per unique material.
Falls back to a minimal profile when LLM is unavailable.
"""

import json
import logging
import os
import re

from apps.requests.llm_client import llm
from apps.requests.models import MaterialProfile

logger = logging.getLogger(__name__)


def _intel_disabled() -> bool:
    """Disable LLM analysis in tests or when explicitly turned off."""
    return (
        os.environ.get("MATERIAL_INTEL_DISABLED") == "1"
        or "PYTEST_CURRENT_TEST" in os.environ
    )

BT = chr(96)

_SYSTEM = """You are an expert in the Russian construction materials market.
For a given raw material name from a purchase request, analyze it and return JSON:
{
  "canonical_name": "общепринятое название материала (кратко)",
  "material_type": "конкретный тип материала (например: планкен, брусчатка, резиновая плитка)",
  "category_hint": "одна категория: pilomaterialy|beton|kirpich|bloki|metalloprokat|keramogranit|suhie_smesi|cement|uteplitel|krovlya|gipsokarton|krepezh|bruschatka|rezinovaya_plitka|trotuarnaya_plitka|drugoe",
  "synonyms": ["синонимы и рыночные названия", "как этот товар называют поставщики"],
  "search_queries": ["2-4 поисковых запроса для поиска поставщиков этого материала"],
  "supplier_hints": ["кто производит: напр. деревообрабатывающий цех, лесопильный завод", "кто поставляет: напр. база пиломатериалов, строймаркет"]
}
Rules:
- Strip dimensions/specs from canonical_name (they are not part of the material identity)
- synonyms must be REAL market terms used by Russian suppliers
- Return ONLY JSON, no markdown"""


def _normalize_query(name: str) -> str:
    q = (name or "").strip().lower()
    q = re.sub(r"\s+", " ", q)
    return q[:300]


def _fallback_profile(name: str) -> dict:
    """Minimal profile without LLM."""
    clean = re.sub(r"\d+[хx×*]\S*", "", _normalize_query(name)).strip()
    return {
        "canonical_name": clean or name,
        "material_type": "",
        "category_hint": "",
        "synonyms": [],
        "search_queries": [clean or name],
        "supplier_hints": [],
    }


def analyze_material(name: str, use_cache: bool = True) -> dict:
    """Return material profile dict. Cached in MaterialProfile per normalized name."""
    query = _normalize_query(name)
    if not query:
        return _fallback_profile(name)

    if use_cache:
        cached = MaterialProfile.objects.filter(query=query).first()
        if cached:
            return {
                "canonical_name": cached.canonical_name,
                "material_type": cached.material_type,
                "category_hint": cached.category_hint,
                "synonyms": cached.synonyms or [],
                "search_queries": cached.search_queries or [],
                "supplier_hints": cached.supplier_hints or [],
            }

    if _intel_disabled() or not llm.api_key:
        return _fallback_profile(name)

    try:
        result = llm.chat([
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": name},
        ])
        content = result["choices"][0]["message"]["content"].strip()
        content = re.sub(r"^" + BT * 3 + r"(?:json)?\s*", "", content)
        content = re.sub(r"\s*" + BT * 3 + r"$", "", content)
        data = json.loads(content)
        profile = {
            "canonical_name": str(data.get("canonical_name") or "")[:300],
            "material_type": str(data.get("material_type") or "")[:200],
            "category_hint": str(data.get("category_hint") or "")[:100],
            "synonyms": [str(s) for s in (data.get("synonyms") or [])][:10],
            "search_queries": [str(s) for s in (data.get("search_queries") or [])][:6],
            "supplier_hints": [str(s) for s in (data.get("supplier_hints") or [])][:8],
        }
    except Exception as e:
        logger.warning("analyze_material LLM failed for %r: %s", name, e)
        return _fallback_profile(name)

    # Cache (ignore race — worst case we analyze twice)
    try:
        MaterialProfile.objects.update_or_create(query=query, defaults=profile)
    except Exception as e:
        logger.warning("MaterialProfile cache write failed: %s", e)
    return profile


def expand_terms_for_item(item_name: str, material_type: str = "") -> set:
    """All search/match terms for a request item: name + canonical + synonyms + material_type."""
    terms = set()
    base = (item_name or "").strip().lower()
    if base and len(base) > 2:
        terms.add(base)
    if material_type:
        terms.add(material_type.strip().lower())
    profile = analyze_material(item_name)
    for key in ("canonical_name", "material_type"):
        v = (profile.get(key) or "").strip().lower()
        if v and len(v) > 2:
            terms.add(v)
    for s in profile.get("synonyms") or []:
        s = s.strip().lower()
        if s and len(s) > 2:
            terms.add(s)
    return terms


def search_queries_for_item(item_name: str, fallback_query: str = "") -> list:
    """Search queries for supplier discovery: LLM-optimized + raw fallback."""
    profile = analyze_material(item_name)
    queries = [q.strip() for q in (profile.get("search_queries") or []) if q.strip()]
    raw = (profile.get("canonical_name") or fallback_query or item_name or "").strip()
    if raw and raw.lower() not in [q.lower() for q in queries]:
        queries.append(raw)
    return queries[:5]

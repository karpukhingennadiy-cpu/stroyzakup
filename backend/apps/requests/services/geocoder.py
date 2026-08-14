"""
Geocoding: address text to lat/lon via 2GIS Catalog API.
Uses the same 2GIS key as the frontend maps (NEXT_PUBLIC_2GIS_KEY).
"""

import os, json, time, urllib.request, urllib.parse
from typing import Optional
import logging
logger = logging.getLogger(__name__)

GEOCODE_URL = "https://catalog.api.2gis.ru/3.0/items"

_last_request = 0.0


def geocode(query: str) -> Optional[tuple[float, float, str, str]]:
    """Convert address text to (lat, lon, city, full_address) via 2GIS."""
    global _last_request

    clean = query.strip()
    for prefix in ["g. ", "g.", "gorod "]:
        if clean.lower().startswith(prefix):
            clean = clean[len(prefix):].strip()
    if not clean:
        return None

    result = _geocode_raw(clean)
    if not result:
        time.sleep(0.5)
        result = _geocode_raw(clean)
    return result


def _geocode_raw(query: str) -> Optional[tuple[float, float, str, str]]:
    global _last_request
    elapsed = time.time() - _last_request
    if elapsed < 0.3:
        time.sleep(0.3 - elapsed)

    params = urllib.parse.urlencode({
        "q": query,
        "key": os.environ.get("YANDEX_API_KEY", "") or os.environ.get("GEOCODER_API_KEY", ""),
        "fields": "items.point,items.address",
        "page_size": 1,
    })
    url = f"{GEOCODE_URL}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "MinitenderRF/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        _last_request = time.time()
    except Exception as e:
        logger.error(f"2GIS geocode error: {e}")
        return None

    try:
        items = data.get("result", {}).get("items", [])
        if not items:
            return None
        item = items[0]
        point = item.get("point") or {}
        lat = point.get("lat")
        lon = point.get("lon")
        if lat is None or lon is None:
            return None
        name = item.get("name", "")
        address = item.get("address_name") or item.get("purpose_name") or name
        return (float(lat), float(lon), name, address)
    except Exception as e:
        logger.error(f"2GIS geocode parse error: {e}")
        return None

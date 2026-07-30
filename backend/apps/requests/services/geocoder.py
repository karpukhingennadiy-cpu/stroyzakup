"""Geocoding: address text to lat/lon via Yandex Geocoder API.
Free tier: 1000 requests/day. Fully Russian service.
"""

import os, json, time, urllib.request, urllib.parse, ssl
from typing import Optional
import logging
logger = logging.getLogger(__name__)

YANDEX_API_KEY = os.environ.get("YANDEX_GEOCODER_KEY", "")
GEOCODE_URL = "https://geocode-maps.yandex.ru/1.x/"

_last_request = 0.0


def geocode(query: str) -> Optional[tuple[float, float, str, str]]:
    """Convert address text to (lat, lon, city, full_address) via Yandex."""
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
        "geocode": query,
        "format": "json",
        "results": 1,
        "apikey": YANDEX_API_KEY,
        "lang": "ru_RU",
    })
    url = f"{GEOCODE_URL}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "MinitenderRF/1.0"})

    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read())
        _last_request = time.time()
    except Exception as e:
        logger.error(f"Yandex geocode error: {e}")
        return None

    try:
        feature = data["response"]["GeoObjectCollection"]["featureMember"]
        if not feature:
            return None
        geo = feature[0]["GeoObject"]
        pos = geo["Point"]["pos"]
        lon_str, lat_str = pos.split()
        lat = float(lat_str)
        lon = float(lon_str)
        full = geo["metaDataProperty"]["GeocoderMetaData"]["text"]
        addr_details = geo["metaDataProperty"]["GeocoderMetaData"]["Address"]
        components = addr_details.get("Components", [])
        city = ""
        # Prefer the most specific level: locality (city) first, then area, then province
        for kind in ("locality", "area", "province"):
            for comp in components:
                if comp["kind"] == kind:
                    city = comp["name"]
                    break
            if city:
                break
        return lat, lon, city, full
    except (KeyError, IndexError, ValueError) as e:
        logger.error(f"Yandex parse error: {e}")
        return None

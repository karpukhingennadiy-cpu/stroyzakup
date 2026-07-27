"""Geocoding: address text to lat/lon via Yandex Geocoder API.
Free tier: 1000 requests/day. Fully Russian service.
"""

import json, time, urllib.request, urllib.parse, ssl
from typing import Optional

YANDEX_API_KEY = "cb0b8e22-2e0b-4b02-b8e8-fd2a2f4d5e6f"
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
        print(f"Yandex geocode error: {e}")
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
        for comp in components:
            if comp["kind"] in ("locality", "area", "province"):
                city = comp["name"]
                break
        return lat, lon, city, full
    except (KeyError, IndexError, ValueError) as e:
        print(f"Yandex parse error: {e}")
        return None

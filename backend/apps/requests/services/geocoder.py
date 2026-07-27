"""Geocoding: address text to lat/lon via OSM Nominatim.
Free, no API key. Rate limit: 1 req/sec (Nominatim policy).
"""

import json, time, urllib.request, urllib.parse, ssl
from typing import Optional

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "MinitenderRF/1.0"

_last_request = 0.0


def geocode(query: str) -> Optional[tuple[float, float, str, str]]:
    """Convert address text to (lat, lon, city, full_address).
    Returns None if geocoding fails. Retries once on failure.
    """
    global _last_request

    # Clean up: remove "г." prefix which confuses Nominatim
    clean = query.strip()
    for prefix in ["г. ", "г.", "город "]:
        if clean.lower().startswith(prefix):
            clean = clean[len(prefix):].strip()

    if not clean:
        return None

    return _geocode_raw(clean) or _geocode_raw(clean)


def _geocode_raw(query: str) -> Optional[tuple[float, float, str, str]]:
    global _last_request
    # Rate limit: ensure at least 1.1s between requests
    elapsed = time.time() - _last_request
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)

    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
        "accept-language": "ru",
    })
    url = f"{NOMINATIM_URL}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read())
        _last_request = time.time()
    except urllib.error.URLError as e:
        print(f"Geocoding network error: {e}")
        return None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None

    if not data:
        return None

    result = data[0]
    lat = float(result["lat"])
    lon = float(result["lon"])
    display_name = result.get("display_name", query)

    # Extract city intelligently
    addr = result.get("address", {})
    city = (
        addr.get("city")
        or addr.get("town")
        or addr.get("village")
        or addr.get("municipality")
        or addr.get("state")  # For "Moscow" which is a state-level entity
        or addr.get("county")
        or ""
    )

    return lat, lon, city, display_name

"""Geocoding: address text to lat/lon via OSM Nominatim."""

import json, time, urllib.request, urllib.parse
from typing import Optional

NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
USER_AGENT = 'MinitenderRF/1.0'

_last_request = 0.0

def geocode(query):
    global _last_request
    elapsed = time.time() - _last_request
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)

    params = urllib.parse.urlencode({'q': query, 'format': 'json', 'limit': 1, 'addressdetails': 1})
    url = f'{NOMINATIM_URL}?{params}'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        _last_request = time.time()
    except Exception as e:
        print(f'Geocoding error: {e}')
        return None

    if not data:
        return None

    result = data[0]
    lat = float(result['lat'])
    lon = float(result['lon'])
    addr = result.get('address', {})
    city = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('municipality') or ''
    return lat, lon, city, result.get('display_name', query)

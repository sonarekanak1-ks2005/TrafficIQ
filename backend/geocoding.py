"""Address geocoding via OSM Nominatim (free, no API key).
Uses public endpoint with proper User-Agent and caching.
"""
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
CACHE_DIR = Path("/tmp/tiq_geo_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
_CACHE_TTL = 30 * 24 * 3600  # 30 days


def _cache_key(q: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in q.lower())[:80]
    return safe or "empty"


def _load_cache(q: str) -> Optional[List[Dict]]:
    p = CACHE_DIR / f"{_cache_key(q)}.json"
    if not p.exists():
        return None
    try:
        if time.time() - p.stat().st_mtime > _CACHE_TTL:
            return None
        return json.loads(p.read_text())
    except Exception:
        return None


def _save_cache(q: str, results: List[Dict]) -> None:
    p = CACHE_DIR / f"{_cache_key(q)}.json"
    try:
        p.write_text(json.dumps(results))
    except Exception:
        pass


def geocode_search(q: str, limit: int = 6, city_center: Optional[List[float]] = None, radius_km: float = 40.0) -> List[Dict]:
    """Search for a place by name/address, optionally biasing to a city."""
    if not q or not q.strip():
        return []
    q_norm = q.strip()
    cached = _load_cache(f"{q_norm}|{city_center}|{radius_km}")
    if cached is not None:
        return cached

    params = {
        "q": q_norm,
        "format": "json",
        "limit": limit,
        "addressdetails": 1,
        "accept-language": "en",
    }
    if city_center and len(city_center) == 2:
        # Bias search around city center via viewbox (roughly radius_km)
        lat, lng = city_center
        deg = radius_km / 111.0
        params["viewbox"] = f"{lng - deg},{lat + deg},{lng + deg},{lat - deg}"
        params["bounded"] = 0
    try:
        r = requests.get(
            NOMINATIM_URL,
            params=params,
            headers={
                "User-Agent": "TrafficIQ/1.0 (contact: dev@trafficiq.app)",
                "Accept": "application/json",
                "Accept-Language": "en",
            },
            timeout=12,
        )
        if r.status_code != 200:
            logger.warning("Nominatim %s -> %s", q_norm, r.status_code)
            return []
        data = r.json()
    except Exception as e:
        logger.warning("Nominatim failed for %s: %s", q_norm, e)
        return []

    out = []
    for item in data[:limit]:
        try:
            lat = float(item["lat"])
            lng = float(item["lon"])
        except Exception:
            continue
        addr = item.get("address", {}) or {}
        city = (
            addr.get("city")
            or addr.get("town")
            or addr.get("village")
            or addr.get("county")
            or addr.get("state")
            or ""
        )
        out.append({
            "display_name": item.get("display_name", ""),
            "lat": lat,
            "lng": lng,
            "type": item.get("type", ""),
            "category": item.get("class", ""),
            "city": city,
            "country": addr.get("country", ""),
        })

    _save_cache(f"{q_norm}|{city_center}|{radius_km}", out)
    return out

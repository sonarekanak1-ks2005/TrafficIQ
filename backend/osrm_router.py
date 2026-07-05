"""OSRM (Open Source Routing Machine) client.

Uses the public demo server at router.project-osrm.org (free, no key).
Returns real driving directions with polyline geometry, distance, duration,
and turn-by-turn steps — replacing our synthetic Dijkstra with a proper
routing engine on the actual OpenStreetMap road network.
"""
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

OSRM_ENDPOINTS = [
    "https://router.project-osrm.org",
    "https://routing.openstreetmap.de/routed-car",  # fallback
]

CACHE_DIR = Path("/tmp/tiq_osrm_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
_CACHE_TTL = 30 * 60  # 30 minutes — traffic changes but base geometry doesn't

_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            headers={
                "User-Agent": "TrafficIQ/1.0 (https://trafficiq.example)",
                "Accept": "application/json",
            },
        )
    return _client


def _cache_key(start: Tuple[float, float], end: Tuple[float, float]) -> str:
    return f"{start[0]:.4f}_{start[1]:.4f}__{end[0]:.4f}_{end[1]:.4f}"


def _load_cache(key: str) -> Optional[Dict]:
    p = CACHE_DIR / f"{key}.json"
    if not p.exists():
        return None
    try:
        if time.time() - p.stat().st_mtime > _CACHE_TTL:
            return None
        return json.loads(p.read_text())
    except Exception:
        return None


def _save_cache(key: str, data: Dict) -> None:
    try:
        (CACHE_DIR / f"{key}.json").write_text(json.dumps(data))
    except Exception:
        pass


async def osrm_route(
    start: Tuple[float, float],
    end: Tuple[float, float],
    alternatives: int = 3,
    timeout: int = 8,
) -> Optional[Dict]:
    """Fetch driving directions between two lat/lng points.
    Returns dict with `routes` list (each with coords/distance_km/duration_min/steps).
    """
    key = _cache_key(start, end)
    cached = _load_cache(key)
    if cached is not None:
        return cached

    start_lat, start_lng = start
    end_lat, end_lng = end
    # OSRM path format: {lng,lat};{lng,lat}
    coords = f"{start_lng},{start_lat};{end_lng},{end_lat}"

    for base in OSRM_ENDPOINTS:
        url = f"{base}/route/v1/driving/{coords}"
        params = {
            "alternatives": "true" if alternatives > 1 else "false",
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
            "annotations": "false",
        }
        try:
            client = _get_client()
            r = await client.get(url, params=params, timeout=timeout)
            if r.status_code != 200:
                logger.warning("OSRM %s -> HTTP %s", base, r.status_code)
                continue
            data = r.json()
            if data.get("code") != "Ok" or not data.get("routes"):
                logger.warning("OSRM %s returned code=%s", base, data.get("code"))
                continue
            routes = []
            for i, rt in enumerate(data["routes"][:alternatives]):
                # geometry is GeoJSON LineString with [lng, lat] pairs — flip to [lat, lng]
                geom = rt.get("geometry", {}) or {}
                if geom.get("type") != "LineString":
                    continue
                coords_ll = [[c[1], c[0]] for c in geom.get("coordinates", [])]
                if len(coords_ll) < 2:
                    continue
                # Collect turn-by-turn steps
                steps: List[Dict] = []
                for leg in rt.get("legs", []):
                    for st in leg.get("steps", []):
                        maneuver = st.get("maneuver", {}) or {}
                        name = st.get("name") or maneuver.get("modifier") or "Continue"
                        loc = maneuver.get("location") or [0, 0]
                        steps.append({
                            "instruction": _format_step(maneuver, name, st),
                            "name": name,
                            "distance_m": st.get("distance", 0),
                            "duration_s": st.get("duration", 0),
                            "coord": [loc[1], loc[0]],
                        })
                # Collect unique street names for a nice summary
                street_names: List[str] = []
                seen = set()
                for leg in rt.get("legs", []):
                    for st in leg.get("steps", []):
                        nm = st.get("name")
                        if nm and nm not in seen:
                            seen.add(nm)
                            street_names.append(nm)
                routes.append({
                    "coords": coords_ll,
                    "distance_km": round(rt.get("distance", 0) / 1000, 2),
                    "duration_min": round(rt.get("duration", 0) / 60, 1),
                    "steps": steps,
                    "street_names": street_names[:15],
                    "index": i,
                })
            if not routes:
                continue
            result = {"routes": routes, "source": "osrm"}
            _save_cache(key, result)
            return result
        except Exception as e:
            logger.warning("OSRM %s failed: %s", base, type(e).__name__)
            continue
    return None


def _format_step(maneuver: Dict, road: str, step: Dict) -> str:
    ma_type = maneuver.get("type", "continue")
    modifier = maneuver.get("modifier", "")
    verb = {
        "depart": "Head",
        "arrive": "Arrive at",
        "turn": "Turn",
        "continue": "Continue",
        "merge": "Merge",
        "on ramp": "Take ramp",
        "off ramp": "Take exit",
        "roundabout": "Enter roundabout",
        "rotary": "Enter rotary",
        "fork": "Keep",
        "end of road": "At end of road",
        "new name": "Continue",
    }.get(ma_type, "Continue")
    direction = f" {modifier}" if modifier else ""
    on_road = f" onto {road}" if road and road != "Continue" else ""
    return f"{verb}{direction}{on_road}".strip()

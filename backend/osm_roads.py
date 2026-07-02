"""OSM roads fetcher via Overpass API.
Fetches major roads for each city bounding box, splits ways at intersections,
and returns segments with:
  - id, name, coords (polyline), from, to, from_node, to_node
  - length_km, lanes, speed_limit, highway type

Segments are cached in-memory (and on disk) per city. Falls back gracefully if
Overpass is unavailable.
"""
import json
import os
import time
from math import radians, sin, cos, asin, sqrt
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

import requests

logger = logging.getLogger(__name__)

CACHE_DIR = Path("/tmp/tiq_osm_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

# Cache invalidation window: 7 days
CACHE_TTL_SEC = 7 * 24 * 3600


def _haversine(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    lat1, lng1 = a
    lat2, lng2 = b
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    aa = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * 6371 * asin(sqrt(aa))


def _bbox_from_center(center: Tuple[float, float], span: float) -> Tuple[float, float, float, float]:
    """Return (south, west, north, east)."""
    lat, lng = center
    half = span / 2
    return (lat - half, lng - half, lat + half, lng + half)


def _overpass_query(bbox: Tuple[float, float, float, float]) -> str:
    s, w, n, e = bbox
    # Include all connecting road types so the graph is well-connected
    return f"""
[out:json][timeout:20];
(
  way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link|residential)$"]
    ({s},{w},{n},{e});
);
out geom;
""".strip()


def _fetch_overpass(query: str, timeout: int = 30) -> Optional[Dict]:
    headers = {
        "User-Agent": "TrafficIQ/1.0 (contact: dev@trafficiq.app)",
        "Accept": "application/json",
    }
    # Try each endpoint up to 2 times with exponential backoff
    for attempt in range(2):
        for endpoint in OVERPASS_ENDPOINTS:
            try:
                logger.info("Overpass fetching from %s (attempt %d)", endpoint, attempt + 1)
                r = requests.post(
                    endpoint,
                    data={"data": query},
                    headers=headers,
                    timeout=timeout,
                )
                if r.status_code == 200:
                    try:
                        return r.json()
                    except Exception as e:
                        logger.warning("Overpass %s returned non-JSON: %s", endpoint, e)
                        continue
                if r.status_code in (429, 504, 502, 503):
                    logger.warning("Overpass %s -> HTTP %s (rate-limited)", endpoint, r.status_code)
                elif r.status_code == 406:
                    logger.warning("Overpass %s -> HTTP 406 (blocked)", endpoint)
                else:
                    logger.warning("Overpass %s -> HTTP %s", endpoint, r.status_code)
            except Exception as e:
                logger.warning("Overpass %s failed: %s", endpoint, type(e).__name__)
        # Backoff before next round
        if attempt == 0:
            time.sleep(3)
    return None


def _speed_limit_default(highway: str) -> int:
    return {
        "motorway": 100,
        "trunk": 80,
        "primary": 70,
        "secondary": 60,
        "tertiary": 50,
        "motorway_link": 60,
        "trunk_link": 50,
        "primary_link": 50,
        "secondary_link": 40,
    }.get(highway, 50)


def _parse_maxspeed(v) -> Optional[int]:
    if not v:
        return None
    try:
        # Handle "60", "60 mph", etc.
        s = str(v).lower()
        if "mph" in s:
            n = int("".join(c for c in s if c.isdigit()))
            return int(n * 1.609)
        return int("".join(c for c in s if c.isdigit()) or 0) or None
    except Exception:
        return None


def _split_ways_at_intersections(elements: List[Dict], max_segments: int = 600) -> List[Dict]:
    """Split ways where they share nodes (intersections).
    Returns list of segments with polyline coords.
    """
    # Count how many ways each node belongs to
    node_way_count: Dict[int, int] = {}
    for el in elements:
        if el.get("type") != "way":
            continue
        for nid in el.get("nodes", []):
            node_way_count[nid] = node_way_count.get(nid, 0) + 1

    segments: List[Dict] = []
    seg_counter = 0

    for el in elements:
        if el.get("type") != "way":
            continue
        way_nodes = el.get("nodes", [])
        geometry = el.get("geometry", [])
        if not way_nodes or not geometry or len(way_nodes) != len(geometry):
            continue

        tags = el.get("tags", {}) or {}
        # Prefer English names when available so cities like Tokyo show Latin script
        name = (
            tags.get("name:en")
            or tags.get("int_name")
            or tags.get("alt_name:en")
            or tags.get("official_name:en")
            or tags.get("name")
            or tags.get("ref")
            or f"OSM way {el.get('id')}"
        )
        highway = tags.get("highway", "unclassified")
        maxspeed = _parse_maxspeed(tags.get("maxspeed")) or _speed_limit_default(highway)
        lanes = 2
        try:
            if tags.get("lanes"):
                lanes = max(1, min(6, int(str(tags["lanes"]).split(";")[0])))
        except Exception:
            lanes = 2

        # Walk the way and cut where a node has >1 incidence (an intersection),
        # or at the very ends.
        cur_coords: List[Tuple[float, float]] = []
        cur_start_node: Optional[int] = None
        for idx, (nid, pt) in enumerate(zip(way_nodes, geometry)):
            lat, lng = round(pt["lat"], 6), round(pt["lon"], 6)
            if not cur_coords:
                cur_coords = [(lat, lng)]
                cur_start_node = nid
                continue
            cur_coords.append((lat, lng))
            is_end = idx == len(way_nodes) - 1
            is_intersection = node_way_count.get(nid, 0) > 1
            if is_end or is_intersection:
                # Finalize segment if it has real length
                if len(cur_coords) >= 2:
                    total_len = 0.0
                    for i in range(len(cur_coords) - 1):
                        total_len += _haversine(cur_coords[i], cur_coords[i + 1])
                    if total_len > 0.03:  # skip <30m stubs
                        seg_counter += 1
                        segments.append({
                            "osm_way_id": el.get("id"),
                            "osm_from_node": cur_start_node,
                            "osm_to_node": nid,
                            "name": name,
                            "highway": highway,
                            "coords": [list(c) for c in cur_coords],
                            "from": list(cur_coords[0]),
                            "to": list(cur_coords[-1]),
                            "length_km": round(total_len, 3),
                            "lanes": lanes,
                            "speed_limit": maxspeed,
                        })
                # Start next segment from this intersection
                cur_coords = [(lat, lng)]
                cur_start_node = nid

    # Sort by importance (named roads first, then by length desc) — but keep all
    segments.sort(key=lambda s: (0 if not s["name"].startswith("OSM way") else 1, -s["length_km"]))
    return segments[:max_segments] if max_segments and len(segments) > max_segments else segments


def _quantize_node(coord: Tuple[float, float]) -> str:
    """Quantize a coordinate into a node key for graph building.
    Uses ~10m grid so nearby but slightly different points merge to the same node.
    """
    lat, lng = coord
    q = 0.0001  # ~11m
    return f"{round(lat / q) * q:.4f}_{round(lng / q) * q:.4f}"


def _finalize_segments(segments: List[Dict], city_key: str) -> List[Dict]:
    """Assign stable IDs. Merge segment endpoints by spatial proximity (~30m) so
    routes connect properly even when OSM ways don't share node IDs at intersections.
    """
    tol_deg = 25.0 / 111000.0  # ~25 meters — precise but still merges genuine intersections
    clusters: Dict[Tuple[int, int], str] = {}

    def cluster_key(pt: Tuple[float, float]) -> str:
        # Check the surrounding 3x3 grid cells so points at cell borders unify too
        base_lat = round(pt[0] / tol_deg)
        base_lng = round(pt[1] / tol_deg)
        for dlat in (0, -1, 1):
            for dlng in (0, -1, 1):
                cand = (base_lat + dlat, base_lng + dlng)
                if cand in clusters:
                    return clusters[cand]
        # New cluster
        key = (base_lat, base_lng)
        clusters[key] = f"c_{len(clusters)}"
        return clusters[key]

    out = []
    for i, s in enumerate(segments):
        from_n = cluster_key(tuple(s["from"]))
        to_n = cluster_key(tuple(s["to"]))
        if from_n == to_n:
            continue
        out.append({
            **s,
            "id": f"{city_key}-osm-{i}",
            "from_node": from_n,
            "to_node": to_n,
        })
    return out


def _subsample_by_importance(segments: List[Dict], target: int) -> List[Dict]:
    """Sub-sample to at most `target` segments, preferring named/higher-priority roads.
    Retains the largest-component graph implicitly since inputs are already filtered.
    """
    if len(segments) <= target:
        return segments
    priority = {
        "motorway": 0, "trunk": 1, "primary": 2, "secondary": 3, "tertiary": 4,
        "motorway_link": 5, "trunk_link": 5, "primary_link": 5, "secondary_link": 6,
        "tertiary_link": 6, "unclassified": 7, "residential": 8,
    }
    def key(s):
        return (
            priority.get(s.get("highway", ""), 9),
            0 if not s["name"].startswith("OSM way") else 1,
            -s["length_km"],
        )
    segments.sort(key=key)
    return segments[:target]


def _cache_path(city_key: str) -> Path:
    return CACHE_DIR / f"{city_key}.json"


def _load_cache(city_key: str) -> Optional[List[Dict]]:
    p = _cache_path(city_key)
    if not p.exists():
        return None
    try:
        age = time.time() - p.stat().st_mtime
        if age > CACHE_TTL_SEC:
            return None
        with open(p, "r") as f:
            data = json.load(f)
        if isinstance(data, list) and data:
            return data
    except Exception as e:
        logger.warning("Cache load failed for %s: %s", city_key, e)
    return None


def _save_cache(city_key: str, segments: List[Dict]) -> None:
    try:
        with open(_cache_path(city_key), "w") as f:
            json.dump(segments, f)
    except Exception as e:
        logger.warning("Cache save failed for %s: %s", city_key, e)


def _keep_largest_component(segments: List[Dict]) -> List[Dict]:
    """Keep only segments in the largest connected component so routes can always be found."""
    if not segments:
        return segments
    from collections import defaultdict, deque
    graph = defaultdict(set)
    for s in segments:
        graph[s["from_node"]].add(s["to_node"])
        graph[s["to_node"]].add(s["from_node"])
    visited = set()
    best_component: set = set()
    for start in list(graph.keys()):
        if start in visited:
            continue
        component = set()
        q = deque([start])
        while q:
            n = q.popleft()
            if n in component:
                continue
            component.add(n)
            for nb in graph[n]:
                if nb not in component:
                    q.append(nb)
        visited.update(component)
        if len(component) > len(best_component):
            best_component = component
    kept = [s for s in segments if s["from_node"] in best_component and s["to_node"] in best_component]
    logger.info("Largest component: %d/%d nodes, %d/%d segments kept",
                len(best_component), len(graph), len(kept), len(segments))
    return kept


def fetch_osm_segments(city_key: str, center: Tuple[float, float], span: float, max_segments: int = 350) -> Optional[List[Dict]]:
    """Fetch real road segments for a city. Returns None if unavailable."""
    cached = _load_cache(city_key)
    if cached is not None:
        logger.info("OSM cache hit for %s: %d segments", city_key, len(cached))
        return cached

    bbox = _bbox_from_center(center, span)
    query = _overpass_query(bbox)
    data = _fetch_overpass(query)
    if not data:
        return None

    elements = data.get("elements", [])
    if not elements:
        return None

    # 1. Split all ways at intersections (no cap yet)
    segments = _split_ways_at_intersections(elements, max_segments=999999)
    if not segments:
        return None
    # 2. Merge nearby endpoints so routing works
    segments = _finalize_segments(segments, city_key)
    # 3. Keep largest connected component for a functional route graph
    segments = _keep_largest_component(segments)
    # 4. Sub-sample to a visualizable set (prefer major roads)
    if len(segments) > max_segments:
        segments = _subsample_by_importance(segments, max_segments)
        # Re-filter to largest component after subsample
        segments = _keep_largest_component(segments)
    if not segments:
        return None

    _save_cache(city_key, segments)
    logger.info("OSM fetched for %s: %d segments", city_key, len(segments))
    return segments

"""Route optimizer.

Primary path: OSRM (Open Source Routing Machine) — real driving directions on
the actual OSM road network with turn-by-turn steps.
Fallback: Dijkstra on our cached OSM segment graph if OSRM is unreachable.
Both paths overlay our simulated congestion so users see live traffic quality
on top of real driving routes.
"""
import heapq
import random
from typing import Dict, List, Optional, Tuple

from city_data import get_segments, get_city
from traffic_engine import congestion_for_segment
from osrm_router import osrm_route


def _compute_osrm_congestion(city_key: str, coords: List[List[float]]) -> Dict:
    """Given an OSRM route polyline, sample congestion from our simulator by
    finding nearby segments for representative points on the route."""
    if not coords:
        return {"avg_congestion": 50.0, "avg_speed_kmph": 30.0}
    segs = get_segments(city_key)
    from math import hypot

    def nearest_seg(pt):
        best = None
        best_d = float("inf")
        for s in segs:
            # Approx distance to midpoint (fast; good enough for sampling)
            m_lat = (s["from"][0] + s["to"][0]) / 2
            m_lng = (s["from"][1] + s["to"][1]) / 2
            d = hypot(pt[0] - m_lat, pt[1] - m_lng)
            if d < best_d:
                best_d = d
                best = s
        return best

    # Sample up to 10 points along the polyline
    n = min(10, max(3, len(coords) // 8))
    step = max(1, len(coords) // n)
    sampled = [coords[i] for i in range(0, len(coords), step)][:n]

    total_cong = 0.0
    total_speed = 0.0
    count = 0
    for pt in sampled:
        s = nearest_seg(pt)
        if s:
            c = congestion_for_segment(city_key, s)
            total_cong += c["congestion"]
            total_speed += c["speed_kmph"]
            count += 1
    if count == 0:
        return {"avg_congestion": 50.0, "avg_speed_kmph": 30.0}
    return {
        "avg_congestion": round(total_cong / count, 1),
        "avg_speed_kmph": round(total_speed / count, 1),
    }


def _build_graph(city_key: str, dt=None) -> Tuple[Dict[str, List[Tuple[str, Dict]]], Dict[str, Tuple[float, float]]]:
    """Graph: node -> list of (neighbor, edge_meta).
    Edge meta includes length_km, congestion, speed, id, name, coords.
    """
    segs = get_segments(city_key)
    graph: Dict[str, List[Tuple[str, Dict]]] = {}
    coords: Dict[str, Tuple[float, float]] = {}

    for s in segs:
        u = s["from_node"]
        v = s["to_node"]
        coords[u] = tuple(s["from"])
        coords[v] = tuple(s["to"])
        c = congestion_for_segment(city_key, s, dt=dt)
        edge = {
            "id": s["id"],
            "name": s["name"],
            "length_km": s["length_km"],
            "congestion": c["congestion"],
            "speed_kmph": c["speed_kmph"],
            "from": s["from"],
            "to": s["to"],
            "coords": s.get("coords") or [s["from"], s["to"]],
        }
        graph.setdefault(u, []).append((v, edge))
        # Bidirectional (reverse polyline too)
        edge_rev = dict(edge)
        edge_rev["from"], edge_rev["to"] = s["to"], s["from"]
        edge_rev["coords"] = list(reversed(edge["coords"]))
        graph.setdefault(v, []).append((u, edge_rev))

    return graph, coords


def _dijkstra(graph, coords, start_node, end_node, weight_fn, avoid_edges=None):
    avoid_edges = avoid_edges or set()
    dist = {start_node: 0.0}
    prev = {}
    pq = [(0.0, start_node)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == end_node:
            break
        if d > dist.get(u, float("inf")):
            continue
        for v, edge in graph.get(u, []):
            if edge["id"] in avoid_edges:
                continue
            w = weight_fn(edge)
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = (u, edge)
                heapq.heappush(pq, (nd, v))

    if end_node not in prev and end_node != start_node:
        return None

    # Reconstruct path
    path_edges = []
    node = end_node
    while node in prev:
        pu, edge = prev[node]
        path_edges.append(edge)
        node = pu
    path_edges.reverse()
    return path_edges


def _nearest_node(coords, target):
    from math import hypot
    best = None
    best_d = float("inf")
    for k, (lat, lng) in coords.items():
        d = hypot(lat - target[0], lng - target[1])
        if d < best_d:
            best_d = d
            best = k
    return best


def _find_segment_by_name(city_key, name):
    if not name:
        return None
    segs = get_segments(city_key)
    name_l = name.lower().strip()
    for s in segs:
        if s["name"].lower() == name_l:
            return s
    for s in segs:
        if name_l in s["name"].lower():
            return s
    return None


def _resolve_endpoint(city_key, value, coords, prefer_first=True):
    """Try to interpret 'value' as a road name; else coords; else pick nearest node."""
    seg = _find_segment_by_name(city_key, value)
    if seg:
        return seg["from_node"] if prefer_first else seg["to_node"], (seg["from"] if prefer_first else seg["to"]), seg["name"]
    # Fallback: pick a random-ish node
    keys = sorted(coords.keys())
    if not keys:
        return None, None, None
    idx = (hash(str(value)) & 0xFFFFFFFF) % len(keys)
    node = keys[idx]
    return node, coords[node], value or "Custom"


def _summarize_route(edges, tag):
    total_km = sum(e["length_km"] for e in edges)
    # Weighted average speed by length
    if total_km > 0:
        avg_speed = sum(e["speed_kmph"] * e["length_km"] for e in edges) / total_km
        avg_cong = sum(e["congestion"] * e["length_km"] for e in edges) / total_km
    else:
        avg_speed = 30
        avg_cong = 50
    time_min = (total_km / max(5, avg_speed)) * 60
    # Eco score (0-100): higher for lower congestion + moderate distance
    eco = max(0, 100 - avg_cong * 0.7 - max(0, total_km - 8) * 2)
    coords = []
    for e in edges:
        pts = e.get("coords") or [e["from"], e["to"]]
        for pt in pts:
            pt_list = list(pt)
            if not coords or coords[-1] != pt_list:
                coords.append(pt_list)
    return {
        "tag": tag,
        "distance_km": round(total_km, 2),
        "time_min": round(time_min, 1),
        "avg_speed_kmph": round(avg_speed, 1),
        "avg_congestion": round(avg_cong, 1),
        "eco_score": round(eco, 1),
        "segment_ids": [e["id"] for e in edges],
        "segment_names": list({e["name"] for e in edges})[:8],
        "coords": coords,
    }


async def optimize_routes(city_key: str, start: str, destination: str) -> Dict:
    graph, coords = _build_graph(city_key)
    start_node, start_coord, start_label = _resolve_endpoint(city_key, start, coords, prefer_first=True)
    end_node, end_coord, end_label = _resolve_endpoint(city_key, destination, coords, prefer_first=False)

    if start_node is None or end_node is None or start_node == end_node:
        keys = list(coords.keys())
        end_node = keys[(hash(destination or "x") & 0xFFFFFFFF) % len(keys)]
        end_coord = coords[end_node]

    # 1) PREFER OSRM — real driving directions
    osrm_result = None
    try:
        osrm_result = await osrm_route(
            start=(start_coord[0], start_coord[1]),
            end=(end_coord[0], end_coord[1]),
            alternatives=3,
        )
    except Exception:
        osrm_result = None

    if osrm_result and osrm_result.get("routes"):
        tags = ["Fastest", "Alternate A", "Alternate B", "Alternate C"]
        routes: List[Dict] = []
        for i, rt in enumerate(osrm_result["routes"][:3]):
            cong_data = _compute_osrm_congestion(city_key, rt["coords"])
            avg_cong = cong_data["avg_congestion"]
            avg_speed = cong_data["avg_speed_kmph"]
            # Adjust duration by current congestion — traffic slows OSRM's free-flow ETA
            traffic_factor = 1.0 + max(0.0, (avg_cong - 40) / 100.0)
            adj_duration = rt["duration_min"] * traffic_factor
            eco = max(0, 100 - avg_cong * 0.7 - max(0, rt["distance_km"] - 8) * 2)
            routes.append({
                "tag": tags[i] if i < len(tags) else f"Alt {i}",
                "distance_km": rt["distance_km"],
                "time_min": round(adj_duration, 1),
                "free_flow_min": rt["duration_min"],
                "avg_speed_kmph": avg_speed,
                "avg_congestion": avg_cong,
                "eco_score": round(eco, 1),
                "segment_ids": [],  # OSRM path — no internal segment ids
                "segment_names": rt.get("street_names", [])[:8],
                "coords": rt["coords"],
                "steps": rt.get("steps", []),
                "source": "osrm",
            })
        recommended_idx = min(range(len(routes)), key=lambda i: routes[i]["time_min"])
        return {
            "city": city_key,
            "start": {"label": start_label, "coord": list(start_coord)},
            "destination": {"label": end_label, "coord": list(end_coord)},
            "routes": routes,
            "recommended_index": recommended_idx,
            "source": "osrm",
        }

    # 2) FALLBACK — Dijkstra on cached graph
    def w_time(e):
        return (e["length_km"] / max(5, e["speed_kmph"])) * 60

    fastest = _dijkstra(graph, coords, start_node, end_node, w_time)
    def w_dist(e):
        return e["length_km"]
    shortest = _dijkstra(graph, coords, start_node, end_node, w_dist)
    def w_eco(e):
        return e["length_km"] * (1.0 + (e["congestion"] / 60.0))
    eco = _dijkstra(graph, coords, start_node, end_node, w_eco)

    routes = []
    def _sig(edges):
        return tuple(e["id"] for e in edges)
    seen_sigs = set()
    if fastest:
        routes.append(_summarize_route(fastest, "Fastest"))
        seen_sigs.add(_sig(fastest))
    if shortest and _sig(shortest) not in seen_sigs:
        routes.append(_summarize_route(shortest, "Shortest"))
        seen_sigs.add(_sig(shortest))
    if eco and _sig(eco) not in seen_sigs:
        routes.append(_summarize_route(eco, "Eco"))
        seen_sigs.add(_sig(eco))

    # Ensure 3 alternatives
    attempts = 0
    cumulative_avoid: set = set()
    while len(routes) < 3 and routes and attempts < 20:
        attempts += 1
        base = routes[-1]["segment_ids"]
        if base:
            mid = len(base) // 2
            cumulative_avoid.add(base[mid])
            if mid + 1 < len(base):
                cumulative_avoid.add(base[mid + 1])
            if mid > 0:
                cumulative_avoid.add(base[mid - 1])
        alt = _dijkstra(graph, coords, start_node, end_node, w_time, avoid_edges=cumulative_avoid)
        if alt and _sig(alt) not in seen_sigs:
            tag = ["Alternate A", "Alternate B", "Alternate C"][len(routes) - 1] if len(routes) - 1 < 3 else f"Alt {len(routes)}"
            routes.append(_summarize_route(alt, tag))
            seen_sigs.add(_sig(alt))

    for r in routes:
        r["source"] = "dijkstra"

    recommended_idx = 0
    if routes:
        recommended_idx = min(range(len(routes)), key=lambda i: routes[i]["time_min"])

    return {
        "city": city_key,
        "start": {"label": start_label, "coord": list(start_coord)},
        "destination": {"label": end_label, "coord": list(end_coord)},
        "routes": routes,
        "recommended_index": recommended_idx,
        "source": "dijkstra",
    }

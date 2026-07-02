"""Alerts engine: generates realistic active alerts per city.
Maintains in-memory active alerts and expires them over time.
"""
import random
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from city_data import get_segments, get_city


ALERT_TYPES = [
    ("accident", "Vehicle Collision", ["critical", "high", "medium"]),
    ("roadwork", "Ongoing Roadwork", ["medium", "low"]),
    ("weather", "Weather Advisory", ["high", "medium", "low"]),
    ("congestion", "Heavy Congestion", ["high", "medium"]),
    ("event", "Local Event Traffic", ["medium", "low"]),
    ("closure", "Road Closure", ["critical", "high"]),
]

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _recommended_action(alert_type: str, severity: str) -> str:
    m = {
        "accident": "Emergency response dispatched. Detour recommended via alternate route.",
        "roadwork": "Expect 10-15 min delay. Prefer parallel arteries.",
        "weather": "Reduce speed by 15-20 kmph. Turn on headlights.",
        "congestion": "Delay travel by 20-30 min or use alternate route.",
        "event": "Avoid area between 6-10 PM. Use ring roads.",
        "closure": "Segment closed. Reroute via nearest bypass.",
    }
    prefix = "URGENT: " if severity == "critical" else ""
    return prefix + m.get(alert_type, "Monitor for updates.")


class AlertsStore:
    def __init__(self):
        self._by_city: Dict[str, List[Dict]] = {}
        self._last_gen: Dict[str, float] = {}

    def _generate_one(self, city_key: str, force_type: Optional[str] = None) -> Dict:
        segs = get_segments(city_key)
        seg = random.choice(segs)
        atype, title, sevs = random.choice(ALERT_TYPES) if not force_type else next(
            (t for t in ALERT_TYPES if t[0] == force_type), random.choice(ALERT_TYPES)
        )
        severity = random.choice(sevs)
        now = datetime.now(ZoneInfo(get_city(city_key)["tz"]))
        duration_min = {"critical": 30, "high": 45, "medium": 60, "low": 90}[severity]
        return {
            "id": str(uuid.uuid4()),
            "city": city_key,
            "type": atype,
            "title": title,
            "severity": severity,
            "location": seg["name"],
            "segment_id": seg["id"],
            "coord": seg["from"],
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=duration_min)).isoformat(),
            "recommended_action": _recommended_action(atype, severity),
            "description": f"{title} on {seg['name']}. Traffic disruption detected.",
        }

    def ensure(self, city_key: str, min_count: int = 6, max_count: int = 12):
        """Ensure there are alerts, generate/expire as needed."""
        now_ts = time.time()
        # Initialize if needed
        if city_key not in self._by_city:
            self._by_city[city_key] = []
            self._last_gen[city_key] = 0
            for _ in range(random.randint(min_count, max_count)):
                self._by_city[city_key].append(self._generate_one(city_key))

        # Expire
        tz = ZoneInfo(get_city(city_key)["tz"])
        now_dt = datetime.now(tz)
        alive = []
        for a in self._by_city[city_key]:
            exp = datetime.fromisoformat(a["expires_at"])
            if exp > now_dt:
                alive.append(a)
        self._by_city[city_key] = alive

        # Add new occasionally (every ~35 seconds)
        if now_ts - self._last_gen.get(city_key, 0) > 35 and len(self._by_city[city_key]) < max_count:
            self._by_city[city_key].insert(0, self._generate_one(city_key))
            self._last_gen[city_key] = now_ts

        # Ensure minimum
        while len(self._by_city[city_key]) < min_count:
            self._by_city[city_key].insert(0, self._generate_one(city_key))

    def list(self, city_key: str) -> List[Dict]:
        self.ensure(city_key)
        alerts = list(self._by_city.get(city_key, []))
        alerts.sort(key=lambda a: (-SEVERITY_ORDER.get(a["severity"], 0), a["created_at"]), reverse=False)
        # sort by severity DESC then created_at DESC
        alerts.sort(key=lambda a: (SEVERITY_ORDER.get(a["severity"], 0), a["created_at"]), reverse=True)
        return alerts

    def add_incident(self, city_key: str, segment_id: Optional[str] = None) -> Dict:
        """Manually add an incident (simulate)."""
        segs = get_segments(city_key)
        seg = None
        if segment_id:
            seg = next((s for s in segs if s["id"] == segment_id), None)
        seg = seg or random.choice(segs)
        now = datetime.now(ZoneInfo(get_city(city_key)["tz"]))
        alert = {
            "id": str(uuid.uuid4()),
            "city": city_key,
            "type": "accident",
            "title": "Simulated Incident",
            "severity": "critical",
            "location": seg["name"],
            "segment_id": seg["id"],
            "from_node": seg["from_node"],
            "to_node": seg["to_node"],
            "coord": seg["from"],
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=25)).isoformat(),
            "recommended_action": _recommended_action("accident", "critical"),
            "description": f"Simulated incident on {seg['name']}. Adjacent segments impacted.",
            "simulated": True,
        }
        self._by_city.setdefault(city_key, []).insert(0, alert)
        return alert

    def get_incidents_for_engine(self, city_key: str) -> List[Dict]:
        """Return active alerts as incidents for the traffic engine."""
        self.ensure(city_key)
        incidents = []
        segs = {s["id"]: s for s in get_segments(city_key)}
        for a in self._by_city.get(city_key, []):
            if a["type"] in {"accident", "closure", "roadwork"} and a["severity"] in {"critical", "high"}:
                seg = segs.get(a["segment_id"])
                if seg:
                    incidents.append({
                        "segment_id": a["segment_id"],
                        "from_node": seg["from_node"],
                        "to_node": seg["to_node"],
                    })
        return incidents


STORE = AlertsStore()

"""Traffic engine: generates realistic congestion values driven by time-of-day,
day-of-week, weather, holidays, and events. Also maintains active incidents.
"""
import math
import random
import time
from datetime import datetime
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from city_data import CITIES, get_segments, get_city


WEATHER_STATES = ["clear", "cloudy", "rain", "heavy_rain", "fog"]


def _season_bias(city_key: str, month: int) -> float:
    # India monsoon (Jun-Sep): more rain -> more congestion baseline
    if city_key in {"pune", "nagpur", "mumbai", "delhi"} and 6 <= month <= 9:
        return 0.08
    # Winter fog in Delhi
    if city_key == "delhi" and month in {12, 1}:
        return 0.06
    return 0.0


def current_weather(city_key: str, now: Optional[datetime] = None) -> Dict:
    """Deterministic-ish weather derived from time of day and city."""
    now = now or datetime.now(ZoneInfo(get_city(city_key)["tz"]))
    hour_seed = int(now.strftime("%Y%m%d%H"))
    rng = random.Random(hash((city_key, hour_seed // 3)) & 0xFFFFFFFF)  # weather changes every ~3 hours
    # Weight rain higher in monsoon months for Indian cities
    weights = [0.42, 0.28, 0.14, 0.06, 0.10]
    month = now.month
    if city_key in {"pune", "nagpur", "mumbai", "delhi"} and 6 <= month <= 9:
        weights = [0.20, 0.28, 0.32, 0.15, 0.05]
    state = rng.choices(WEATHER_STATES, weights=weights, k=1)[0]
    temp_c = {
        "pune": 27, "nagpur": 30, "mumbai": 30, "delhi": 25,
        "london": 14, "nyc": 18, "tokyo": 20, "singapore": 30,
    }.get(city_key, 22)
    temp_c += rng.uniform(-4, 4)
    return {"state": state, "temp_c": round(temp_c, 1), "as_of": now.isoformat()}


def is_holiday(city_key: str, dt: datetime) -> bool:
    # Simple synthetic holidays: 1st of each month or specific festivals
    festivals = {
        "pune": [(1, 26), (8, 15), (10, 24), (11, 1), (12, 25)],
        "nagpur": [(1, 26), (8, 15), (10, 24), (11, 1)],
        "mumbai": [(1, 26), (8, 15), (10, 24), (11, 1), (12, 25)],
        "delhi": [(1, 26), (8, 15), (10, 24), (11, 1)],
        "london": [(1, 1), (12, 25), (12, 26)],
        "nyc": [(1, 1), (7, 4), (11, 28), (12, 25)],
        "tokyo": [(1, 1), (5, 3), (5, 5), (12, 31)],
        "singapore": [(1, 1), (8, 9), (12, 25)],
    }
    for (m, d) in festivals.get(city_key, []):
        if dt.month == m and dt.day == d:
            return True
    return False


def _rush_hour_multiplier(hour: float, is_weekend: bool) -> float:
    """Bell curves centered at 9 and 18. Reduced on weekends."""
    peak_morning = math.exp(-((hour - 9.0) ** 2) / (2 * 1.2 ** 2))
    peak_evening = math.exp(-((hour - 18.0) ** 2) / (2 * 1.4 ** 2))
    midday = math.exp(-((hour - 13.0) ** 2) / (2 * 2.5 ** 2)) * 0.4
    weekend_factor = 0.55 if is_weekend else 1.0
    return max(peak_morning, peak_evening) * weekend_factor + midday * 0.5


def _weather_multiplier(weather_state: str) -> float:
    return {
        "clear": 1.0,
        "cloudy": 1.04,
        "rain": 1.22,
        "heavy_rain": 1.38,
        "fog": 1.18,
    }.get(weather_state, 1.0)


def _segment_base(city_key: str, segment: Dict) -> float:
    """Baseline traffic sensitivity per segment (some roads are always busier)."""
    rng = random.Random(hash(segment["id"]) & 0xFFFFFFFF)
    return rng.uniform(0.35, 0.65)


def congestion_for_segment(
    city_key: str,
    segment: Dict,
    dt: Optional[datetime] = None,
    weather: Optional[str] = None,
    holiday: Optional[bool] = None,
    event_boost: float = 0.0,
    incident_boost: float = 0.0,
) -> Dict:
    """Compute a segment's current congestion (0-100), speed (kmph), status."""
    tz = ZoneInfo(get_city(city_key)["tz"])
    dt = dt or datetime.now(tz)
    hour = dt.hour + dt.minute / 60.0
    is_weekend = dt.weekday() >= 5
    weather = weather or current_weather(city_key, dt)["state"]
    holiday = is_holiday(city_key, dt) if holiday is None else holiday

    base = _segment_base(city_key, segment)
    rush = _rush_hour_multiplier(hour, is_weekend)
    weather_m = _weather_multiplier(weather)
    season_b = _season_bias(city_key, dt.month)
    holiday_reduction = 0.65 if holiday else 1.0  # holidays reduce commute

    # Segment-specific noise (stable per minute)
    noise_seed = hash((segment["id"], dt.strftime("%Y%m%d%H%M"))) & 0xFFFFFFFF
    noise = (random.Random(noise_seed).random() - 0.5) * 0.15

    raw = (base * 28) + (rush * 45 * holiday_reduction * weather_m) + (season_b * 60) + (event_boost * 22) + (incident_boost * 38) + noise * 16
    congestion = max(0.0, min(100.0, raw))

    speed_limit = segment.get("speed_limit", 50)
    # Speed drops as congestion rises (non-linear)
    speed = speed_limit * max(0.1, 1.0 - (congestion / 100.0) ** 1.4)

    status = "clear"
    if congestion >= 66:
        status = "congested"
    elif congestion >= 33:
        status = "moderate"

    return {
        "congestion": round(congestion, 1),
        "speed_kmph": round(speed, 1),
        "status": status,
    }


def snapshot_city(
    city_key: str,
    dt: Optional[datetime] = None,
    incidents: Optional[List[Dict]] = None,
) -> Dict:
    """Full snapshot of traffic for a city."""
    tz = ZoneInfo(get_city(city_key)["tz"])
    dt = dt or datetime.now(tz)
    weather = current_weather(city_key, dt)
    holiday = is_holiday(city_key, dt)
    incidents = incidents or []

    segs = get_segments(city_key)
    seg_out = []
    total_cong = 0.0
    total_speed = 0.0
    congested_count = 0
    for seg in segs:
        # Compute incident boost for this segment
        incident_boost = 0.0
        for inc in incidents:
            if inc["segment_id"] == seg["id"]:
                incident_boost = 1.0
            elif seg["from_node"] in (inc.get("from_node"), inc.get("to_node")) or seg["to_node"] in (inc.get("from_node"), inc.get("to_node")):
                incident_boost = max(incident_boost, 0.45)
        c = congestion_for_segment(city_key, seg, dt=dt, weather=weather["state"], holiday=holiday, incident_boost=incident_boost)
        seg_out.append({
            **seg,
            **c,
        })
        total_cong += c["congestion"]
        total_speed += c["speed_kmph"]
        if c["status"] == "congested":
            congested_count += 1

    n = max(1, len(segs))
    return {
        "city": city_key,
        "as_of": dt.isoformat(),
        "weather": weather,
        "holiday": holiday,
        "segments": seg_out,
        "kpis": {
            "congestion_index": round(total_cong / n, 1),
            "avg_speed_kmph": round(total_speed / n, 1),
            "segments_congested": congested_count,
            "segments_total": n,
        },
    }

"""LSTM-mimicking prediction model.
Generates a plausible congestion curve for the requested time range,
reacting to weather / holiday / event factors, with a confidence score.
"""
import logging
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from city_data import get_city, get_segments
from traffic_engine import _rush_hour_multiplier, _weather_multiplier, is_holiday, current_weather


def _find_segment(city_key: str, location: str) -> Optional[Dict]:
    if not location:
        return None
    segs = get_segments(city_key)
    location_l = location.lower().strip()
    for s in segs:
        if s["name"].lower() == location_l:
            return s
    for s in segs:
        if location_l in s["name"].lower():
            return s
    return None


def predict_congestion_formula(
    city_key: str,
    start: str,
    destination: str,
    when_iso: Optional[str],
    horizon_minutes: int = 60,
    weather_impact: bool = True,
    holiday_effect: bool = True,
    event_nearby: bool = False,
) -> Dict:
    tz = ZoneInfo(get_city(city_key)["tz"])
    when = datetime.fromisoformat(when_iso).astimezone(tz) if when_iso else datetime.now(tz)

    weather = current_weather(city_key, when)
    weather_state = weather["state"] if weather_impact else "clear"
    weather_m = _weather_multiplier(weather_state) if weather_impact else 1.0
    holiday = is_holiday(city_key, when) if holiday_effect else False
    holiday_reduction = 0.65 if holiday else 1.0
    event_boost = 0.18 if event_nearby else 0.0

    start_seg = _find_segment(city_key, start)
    dest_seg = _find_segment(city_key, destination)

    # Determine step size
    step_minutes = 5 if horizon_minutes <= 60 else 10
    steps = horizon_minutes // step_minutes
    points: List[Dict] = []

    seg_base_multiplier = 1.0
    if start_seg or dest_seg:
        # Slight bias if roads are known to be busy
        base_start = random.Random(hash(start_seg["id"]) & 0xFFFFFFFF).uniform(0.4, 0.7) if start_seg else 0.5
        base_dest = random.Random(hash(dest_seg["id"]) & 0xFFFFFFFF).uniform(0.4, 0.7) if dest_seg else 0.5
        seg_base_multiplier = (base_start + base_dest) / 2 * 1.4
    else:
        seg_base_multiplier = 0.55

    # Confidence: higher for near horizon and clearer weather
    confidence = 0.92 - (0.001 * horizon_minutes) - (0.05 if weather_state in {"rain", "heavy_rain", "fog"} else 0.0)
    confidence = max(0.55, min(0.95, confidence))

    total = 0.0
    best_val = 101.0
    best_time_iso = when.isoformat()
    max_val = 0.0

    for i in range(steps + 1):
        t = when + timedelta(minutes=i * step_minutes)
        hour = t.hour + t.minute / 60.0
        rush = _rush_hour_multiplier(hour, t.weekday() >= 5)
        noise_seed = hash((city_key, start, destination, t.strftime("%Y%m%d%H%M"))) & 0xFFFFFFFF
        noise = (random.Random(noise_seed).random() - 0.5) * 0.14

        raw = (seg_base_multiplier * 30) + (rush * 55 * holiday_reduction * weather_m) + (event_boost * 25) + noise * 22
        congestion = max(0.0, min(100.0, raw))
        # Predicted mean speed for a typical 50 kmph road
        speed = 50 * max(0.1, 1.0 - (congestion / 100.0) ** 1.4)
        conf_low = max(0.0, congestion - (1.0 - confidence) * 30)
        conf_high = min(100.0, congestion + (1.0 - confidence) * 30)
        points.append({
            "t": t.isoformat(),
            "minute_offset": i * step_minutes,
            "congestion": round(congestion, 1),
            "speed_kmph": round(speed, 1),
            "conf_low": round(conf_low, 1),
            "conf_high": round(conf_high, 1),
        })
        total += congestion
        if congestion < best_val:
            best_val = congestion
            best_time_iso = t.isoformat()
        if congestion > max_val:
            max_val = congestion

    avg_cong = total / max(1, len(points))
    avg_speed = 50 * max(0.1, 1.0 - (avg_cong / 100.0) ** 1.4)

    # Summary
    if avg_cong >= 70:
        summary = "Severe congestion expected — consider delaying your trip."
    elif avg_cong >= 45:
        summary = "Moderate congestion expected during this window."
    else:
        summary = "Roads look clear — good time to travel."

    return {
        "city": city_key,
        "start": start,
        "destination": destination,
        "when": when.isoformat(),
        "horizon_minutes": horizon_minutes,
        "factors": {
            "weather_impact": weather_impact,
            "holiday_effect": holiday_effect,
            "event_nearby": event_nearby,
            "weather_state": weather_state,
            "is_holiday": holiday,
        },
        "points": points,
        "avg_congestion": round(avg_cong, 1),
        "predicted_speed_kmph": round(avg_speed, 1),
        "peak_congestion": round(max_val, 1),
        "best_travel_time": best_time_iso,
        "confidence": round(confidence, 2),
        "summary": summary,
    }


_LSTM_CITIES = {"nagpur"}  # cities with a trained model; others fall back to the formula


def predict_congestion(
    city_key: str,
    start: str,
    destination: str,
    when_iso: Optional[str] = None,
    horizon_minutes: int = 60,
    weather_impact: bool = True,
    holiday_effect: bool = True,
    event_nearby: bool = False,
) -> Dict:
    """Dispatches to the trained LSTM for cities that have one, and to the
    deterministic formula (predict_congestion_formula) for the rest. Keeps
    the same signature/response shape either way -- server.py and the
    frontend don't need to know which one ran."""
    if city_key in _LSTM_CITIES:
        try:
            from lstm_predictor import predict_congestion as lstm_predict
            return lstm_predict(
                city_key=city_key, start=start, destination=destination,
                when_iso=when_iso, horizon_minutes=horizon_minutes,
                weather_impact=weather_impact, holiday_effect=holiday_effect,
                event_nearby=event_nearby,
            )
        except Exception:
            logging.exception("LSTM prediction failed, falling back to formula")
    result = predict_congestion_formula(
        city_key=city_key, start=start, destination=destination,
        when_iso=when_iso, horizon_minutes=horizon_minutes,
        weather_impact=weather_impact, holiday_effect=holiday_effect,
        event_nearby=event_nearby,
    )
    result["model"] = "formula_v1"
    return result


def analytics_historical(city_key: str) -> Dict:
    """Return historical analytics: hour-of-day, day-of-week heatmap, top roads,
    weather scatter, holiday impact."""
    # Hour-of-day pattern (0-23)
    hour_pattern = []
    for h in range(24):
        rush = _rush_hour_multiplier(h, False)
        val = 25 + rush * 55 + random.Random(hash((city_key, "h", h)) & 0xFFFFFFFF).uniform(-5, 5)
        hour_pattern.append({"hour": h, "congestion": round(max(0, min(100, val)), 1)})

    # 7x24 heatmap
    heatmap = []
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for d in range(7):
        for h in range(24):
            is_wknd = d >= 5
            rush = _rush_hour_multiplier(h, is_wknd)
            val = 22 + rush * 55 + random.Random(hash((city_key, d, h)) & 0xFFFFFFFF).uniform(-6, 6)
            heatmap.append({"day": days[d], "day_idx": d, "hour": h, "congestion": round(max(0, min(100, val)), 1)})

    # Weather scatter (weather intensity vs congestion)
    scatter = []
    for w, weight in [("clear", 1.0), ("cloudy", 1.04), ("rain", 1.22), ("heavy_rain", 1.38), ("fog", 1.18)]:
        for i in range(12):
            base = 35 + random.Random(hash((city_key, w, i)) & 0xFFFFFFFF).uniform(-8, 20)
            scatter.append({"weather": w, "intensity": round(weight, 2), "congestion": round(min(100, base * weight), 1)})

    # Holiday impact
    holiday_impact = [
        {"type": "Working Day", "congestion": 62.0},
        {"type": "Weekend", "congestion": 41.0},
        {"type": "Public Holiday", "congestion": 32.0},
        {"type": "Festival", "congestion": 54.0},
    ]

    # Top 5 most congested roads (from segments)
    segs = get_segments(city_key)
    scored = []
    for s in segs:
        base = random.Random(hash(s["id"]) & 0xFFFFFFFF).uniform(30, 82)
        scored.append({"id": s["id"], "name": s["name"], "avg_congestion": round(base, 1)})
    scored.sort(key=lambda x: x["avg_congestion"], reverse=True)
    # Deduplicate names
    seen = set()
    top = []
    for s in scored:
        if s["name"] in seen:
            continue
        seen.add(s["name"])
        top.append(s)
        if len(top) == 5:
            break

    return {
        "city": city_key,
        "hour_pattern": hour_pattern,
        "heatmap": heatmap,
        "weather_scatter": scatter,
        "holiday_impact": holiday_impact,
        "top_roads": top,
    }

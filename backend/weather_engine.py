"""Weather engine: deterministic forecasts for each city with realistic patterns.

Provides current conditions + 24h hourly forecast. Weather changes gradually
over ~3 hour windows for realism.
"""
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from city_data import get_city
from traffic_engine import current_weather, WEATHER_STATES


WEATHER_LABEL = {
    "clear": "Clear",
    "cloudy": "Cloudy",
    "rain": "Rain",
    "heavy_rain": "Heavy Rain",
    "fog": "Fog",
}

WEATHER_ICON = {
    "clear": "sun",
    "cloudy": "cloud",
    "rain": "cloud-rain",
    "heavy_rain": "cloud-lightning",
    "fog": "cloud-fog",
}

WEATHER_TRAFFIC_IMPACT = {
    "clear": {"multiplier": 1.00, "label": "No impact", "tone": "success"},
    "cloudy": {"multiplier": 1.04, "label": "Minor", "tone": "primary"},
    "rain": {"multiplier": 1.22, "label": "Moderate", "tone": "warning"},
    "heavy_rain": {"multiplier": 1.38, "label": "Severe", "tone": "danger"},
    "fog": {"multiplier": 1.18, "label": "Moderate", "tone": "warning"},
}


def _humidity(state: str, temp_c: float) -> int:
    if state == "heavy_rain":
        return random.randint(88, 96)
    if state == "rain":
        return random.randint(78, 90)
    if state == "fog":
        return random.randint(85, 98)
    if state == "cloudy":
        return random.randint(60, 78)
    # clear
    return max(30, min(70, int(75 - (temp_c - 20) * 1.2 + random.uniform(-5, 5))))


def _wind_kmph(state: str) -> float:
    base = {
        "clear": 8, "cloudy": 11, "rain": 18, "heavy_rain": 28, "fog": 4,
    }.get(state, 10)
    return round(base + random.uniform(-3, 5), 1)


def _visibility_km(state: str) -> float:
    v = {
        "clear": 12.0, "cloudy": 9.0, "rain": 5.0, "heavy_rain": 2.5, "fog": 0.6,
    }.get(state, 10.0)
    return round(v + random.uniform(-0.5, 0.5), 1)


def _uv_index(state: str, hour: int) -> int:
    if hour < 7 or hour > 18:
        return 0
    base = {
        "clear": 8, "cloudy": 4, "rain": 2, "heavy_rain": 1, "fog": 2,
    }.get(state, 4)
    # Peak at solar noon
    modifier = 1.0 - abs(hour - 13) / 8.0
    return max(0, min(11, int(base * modifier)))


def _pressure(state: str) -> int:
    base = {
        "clear": 1017, "cloudy": 1013, "rain": 1005, "heavy_rain": 998, "fog": 1011,
    }.get(state, 1013)
    return base + random.randint(-3, 3)


def _feels_like(temp_c: float, humidity: int, wind: float) -> float:
    # Simple heat index / wind chill approximation
    if temp_c >= 27:
        # Slight heat index
        return round(temp_c + (humidity - 50) * 0.05, 1)
    if temp_c <= 10:
        return round(temp_c - wind * 0.15, 1)
    return round(temp_c + random.uniform(-1, 1), 1)


def current_weather_detailed(city_key: str, when: Optional[datetime] = None) -> Dict:
    tz = ZoneInfo(get_city(city_key)["tz"])
    now = when or datetime.now(tz)
    base = current_weather(city_key, now)
    state = base["state"]
    temp_c = base["temp_c"]
    rng = random.Random(hash((city_key, now.strftime("%Y%m%d%H"))) & 0xFFFFFFFF)
    random.seed(rng.random())  # seed the global for helpers

    hum = _humidity(state, temp_c)
    wind = _wind_kmph(state)
    vis = _visibility_km(state)
    uv = _uv_index(state, now.hour)
    pressure = _pressure(state)
    feels = _feels_like(temp_c, hum, wind)

    impact = WEATHER_TRAFFIC_IMPACT.get(state, WEATHER_TRAFFIC_IMPACT["clear"])

    # Sunrise / sunset approximation
    sunrise_h = 6 if tz.key not in ("Europe/London",) else 7
    sunset_h = 18 if tz.key not in ("Europe/London",) else 20
    sunrise_dt = now.replace(hour=sunrise_h, minute=15, second=0, microsecond=0)
    sunset_dt = now.replace(hour=sunset_h, minute=42, second=0, microsecond=0)

    return {
        "city": city_key,
        "as_of": now.isoformat(),
        "state": state,
        "label": WEATHER_LABEL.get(state, state.title()),
        "icon": WEATHER_ICON.get(state, "sun"),
        "temp_c": round(temp_c, 1),
        "feels_like_c": feels,
        "humidity": hum,
        "wind_kmph": wind,
        "visibility_km": vis,
        "uv_index": uv,
        "pressure_hpa": pressure,
        "sunrise": sunrise_dt.isoformat(),
        "sunset": sunset_dt.isoformat(),
        "sunrise_local": sunrise_dt.strftime("%I:%M %p").lstrip("0"),
        "sunset_local": sunset_dt.strftime("%I:%M %p").lstrip("0"),
        "traffic_impact": impact,
    }


def forecast_24h(city_key: str) -> Dict:
    """Return 24 hourly forecast entries starting from current hour."""
    tz = ZoneInfo(get_city(city_key)["tz"])
    now = datetime.now(tz).replace(minute=0, second=0, microsecond=0)
    hours: List[Dict] = []
    for i in range(24):
        t = now + timedelta(hours=i)
        base = current_weather(city_key, t)
        state = base["state"]
        temp = base["temp_c"]
        rng = random.Random(hash((city_key, t.strftime("%Y%m%d%H"))) & 0xFFFFFFFF)
        # Slight diurnal temperature variation
        hour_offset = math.cos((t.hour - 15) / 24 * 2 * math.pi) * 3
        temp = round(temp + hour_offset + rng.uniform(-1, 1), 1)
        hours.append({
            "t": t.isoformat(),
            "hour": t.hour,
            "state": state,
            "label": WEATHER_LABEL.get(state, state.title()),
            "icon": WEATHER_ICON.get(state, "sun"),
            "temp_c": temp,
            "pop": (
                80 if state == "heavy_rain"
                else 55 if state == "rain"
                else 20 if state == "cloudy"
                else 5 if state == "clear"
                else 30
            ),
            "traffic_multiplier": WEATHER_TRAFFIC_IMPACT.get(state, {}).get("multiplier", 1.0),
        })
    return {"city": city_key, "hours": hours}


def weekly_forecast(city_key: str) -> List[Dict]:
    """7-day summary forecast."""
    tz = ZoneInfo(get_city(city_key)["tz"])
    today = datetime.now(tz).replace(hour=12, minute=0, second=0, microsecond=0)
    days = []
    for i in range(7):
        t = today + timedelta(days=i)
        base = current_weather(city_key, t)
        state = base["state"]
        rng = random.Random(hash((city_key, t.strftime("%Y%m%d"))) & 0xFFFFFFFF)
        high = round(base["temp_c"] + rng.uniform(2, 5), 1)
        low = round(base["temp_c"] - rng.uniform(3, 7), 1)
        days.append({
            "date": t.strftime("%Y-%m-%d"),
            "day_label": t.strftime("%a"),
            "state": state,
            "label": WEATHER_LABEL.get(state, state.title()),
            "icon": WEATHER_ICON.get(state, "sun"),
            "high_c": high,
            "low_c": low,
            "traffic_multiplier": WEATHER_TRAFFIC_IMPACT.get(state, {}).get("multiplier", 1.0),
        })
    return days

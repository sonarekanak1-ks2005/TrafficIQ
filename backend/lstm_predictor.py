"""
Production inference for the trained congestion LSTM.

Zero PyTorch dependency at runtime -- loads plain numpy weight matrices
(lstm_weights_numpy.npz) and config (lstm_config.json), and runs the LSTM
forward pass with hand-written numpy matrix ops. Safe to deploy on
resource-constrained hosts (Render free tier, etc).

Drop-in for backend/prediction_model.py's predict_congestion(): same
function signature, same response shape, so server.py and the frontend
don't need to change.

HONEST LIMITATION: the training data (generate_dataset.py) did not include
an "event_nearby" feature, so the LSTM never learned that signal. event_nearby
is applied as a small, clearly-labeled heuristic adjustment on top of the
model's output, not something the network learned. To make this fully
learned, add an event flag to generate_dataset.py + train_lstm.py and retrain.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np

_DIR = Path(__file__).parent
_weights = np.load(_DIR / "lstm_weights_numpy.npz")
_config = json.loads((_DIR / "lstm_config.json").read_text())

LOOKBACK = _config["lookback"]
HORIZON = _config["horizon"]
WEATHER_STATES = _config["weather_states"]
STEP_MINUTES = 15
VAL_MAE_PTS = 1.08  # from training_history.json, last epoch


def _sigmoid(x):
    return 1 / (1 + np.exp(-x))


def _lstm_forward(x_seq: np.ndarray) -> np.ndarray:
    """x_seq: (LOOKBACK, input_dim) -> (HORIZON,) prediction in [0,1]."""
    hidden_dim = _weights["W_hh"].shape[1]
    h = np.zeros(hidden_dim, dtype=np.float32)
    c = np.zeros(hidden_dim, dtype=np.float32)
    for t in range(x_seq.shape[0]):
        gates = _weights["W_ih"] @ x_seq[t] + _weights["b_ih"] + _weights["W_hh"] @ h + _weights["b_hh"]
        i, f, g, o = np.split(gates, 4)
        i, f, o = _sigmoid(i), _sigmoid(f), _sigmoid(o)
        g = np.tanh(g)
        c = f * c + i * g
        h = o * np.tanh(c)
    z1 = np.maximum(0, _weights["head_W1"] @ h + _weights["head_b1"])
    z2 = _weights["head_W2"] @ z1 + _weights["head_b2"]
    return _sigmoid(z2)


def _feature_vec(dt: datetime, congestion_norm: float, weather_state: str,
                  holiday: bool, segment_base: float) -> np.ndarray:
    hour = dt.hour + dt.minute / 60.0
    dow = dt.weekday()
    hour_sin, hour_cos = np.sin(2 * np.pi * hour / 24), np.cos(2 * np.pi * hour / 24)
    dow_sin, dow_cos = np.sin(2 * np.pi * dow / 7), np.cos(2 * np.pi * dow / 7)
    is_weekend = float(dow >= 5)
    is_holiday = float(holiday)
    weather_oh = [float(weather_state == w) for w in WEATHER_STATES]
    return np.array([congestion_norm, hour_sin, hour_cos, dow_sin, dow_cos,
                      is_weekend, is_holiday, segment_base, *weather_oh], dtype=np.float32)


def _route_segment_base(city_key: str, start: str, destination: str) -> float:
    """Deterministic pseudo-sensitivity for an arbitrary start/destination pair,
    reusing the same hashing convention as traffic_engine._segment_base so the
    LSTM's segment_base feature is consistent with what it saw in training."""
    import random
    seed = hash((city_key, "route", start, destination)) & 0xFFFFFFFF
    return random.Random(seed).uniform(0.35, 0.65)


def _build_lookback(city_key: str, start: str, destination: str, when: datetime,
                     weather_impact: bool, holiday_effect: bool):
    """Builds LOOKBACK historical feature rows ending just before `when`,
    using the project's own traffic_engine simulator as ground truth context
    (matches how training data was generated)."""
    from traffic_engine import congestion_for_segment, current_weather, is_holiday

    seg_base = _route_segment_base(city_key, start, destination)
    fake_seg = {"id": f"route::{city_key}::{start}::{destination}", "speed_limit": 50}

    rows = []
    for i in range(LOOKBACK, 0, -1):
        t = when - timedelta(minutes=i * STEP_MINUTES)
        w = current_weather(city_key, t)["state"] if weather_impact else "clear"
        h = is_holiday(city_key, t) if holiday_effect else False
        c = congestion_for_segment(city_key, fake_seg, dt=t, weather=w, holiday=h)
        rows.append((t, c["congestion"] / 100.0, w, h))
    feats = np.stack([_feature_vec(t, cn, w, h, seg_base) for (t, cn, w, h) in rows])
    return feats, seg_base


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
    from city_data import get_city
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(get_city(city_key)["tz"])
    when = datetime.fromisoformat(when_iso).astimezone(tz) if when_iso else datetime.now(tz)

    feats, seg_base = _build_lookback(city_key, start, destination, when, weather_impact, holiday_effect)

    n_target_steps = max(1, horizon_minutes // STEP_MINUTES)
    predicted_norm: List[float] = []
    cur_feats = feats.copy()
    cur_time = when

    from traffic_engine import current_weather, is_holiday as _is_holiday
    rollouts = 0
    while len(predicted_norm) < n_target_steps:
        out = _lstm_forward(cur_feats)  # (HORIZON,) normalized 0-1
        predicted_norm.extend(out.tolist())
        # advance the window: append predicted steps as if observed, recompute
        # calendar features for those future timestamps (autoregressive rollout)
        new_rows = []
        for k, val in enumerate(out, start=1):
            t = cur_time + timedelta(minutes=k * STEP_MINUTES)
            w = current_weather(city_key, t)["state"] if weather_impact else "clear"
            h = _is_holiday(city_key, t) if holiday_effect else False
            new_rows.append(_feature_vec(t, float(val), w, h, seg_base))
        cur_feats = np.concatenate([cur_feats, np.stack(new_rows)])[-LOOKBACK:]
        cur_time = cur_time + timedelta(minutes=len(out) * STEP_MINUTES)
        rollouts += 1
        if rollouts > 20:  # safety cap
            break

    predicted_norm = predicted_norm[:n_target_steps]
    event_boost_pts = 8.0 if event_nearby else 0.0  # heuristic add-on, see module docstring

    points = []
    total = 0.0
    best_val = 101.0
    best_time_iso = when.isoformat()
    max_val = 0.0
    for i, norm_val in enumerate(predicted_norm):
        t = when + timedelta(minutes=(i + 1) * STEP_MINUTES)
        congestion = float(np.clip(norm_val * 100 + event_boost_pts, 0, 100))
        speed = 50 * max(0.1, 1.0 - (congestion / 100.0) ** 1.4)
        # uncertainty grows with how far into the autoregressive rollout we are
        step_uncertainty = VAL_MAE_PTS * (1 + i / max(1, n_target_steps) * 3)
        conf_low = max(0.0, congestion - step_uncertainty * 2)
        conf_high = min(100.0, congestion + step_uncertainty * 2)
        points.append({
            "t": t.isoformat(),
            "minute_offset": (i + 1) * STEP_MINUTES,
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
    # confidence: grounded in real validation error, decays over the horizon
    confidence = max(0.5, min(0.95, 0.95 - (VAL_MAE_PTS / 100) * 4 - (horizon_minutes / 1000)))

    if avg_cong >= 70:
        summary = "Severe congestion expected — consider delaying your trip."
    elif avg_cong >= 45:
        summary = "Moderate congestion expected during this window."
    else:
        summary = "Roads look clear — good time to travel."

    weather_now = current_weather(city_key, when)["state"] if weather_impact else "clear"
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
            "weather_state": weather_now,
            "is_holiday": _is_holiday(city_key, when) if holiday_effect else False,
        },
        "points": points,
        "avg_congestion": round(avg_cong, 1),
        "predicted_speed_kmph": round(avg_speed, 1),
        "peak_congestion": round(max_val, 1),
        "best_travel_time": best_time_iso,
        "confidence": round(confidence, 2),
        "summary": summary,
        "model": "lstm_v1",  # so the frontend/README can be honest about provenance
    }

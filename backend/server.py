from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import asyncio
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Dict, Set
from datetime import datetime

from city_data import CITIES, list_cities, get_city, get_segments
from traffic_engine import snapshot_city, current_weather
from prediction_model import predict_congestion, analytics_historical
from route_optimizer import optimize_routes
from alerts_engine import STORE as ALERTS
from weather_engine import current_weather_detailed, forecast_24h, weekly_forecast
from geocoding import geocode_search


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

app = FastAPI(title="TrafficIQ API", version="1.0.0")
api_router = APIRouter(prefix="/api")


class SessionState:
    def __init__(self):
        self.routes_optimized = 0

    def bump_routes(self):
        self.routes_optimized += 1


SESSION = SessionState()


class PredictionRequest(BaseModel):
    city: str
    start: str = ""
    destination: str = ""
    when: Optional[str] = None
    horizon_minutes: int = 60
    weather_impact: bool = True
    holiday_effect: bool = True
    event_nearby: bool = False


class RouteRequest(BaseModel):
    city: str
    start: str
    destination: str


class IncidentRequest(BaseModel):
    city: str
    segment_id: Optional[str] = None


@api_router.get("/")
async def root():
    return {"message": "TrafficIQ API online", "cities": len(CITIES)}


@api_router.get("/cities")
async def cities():
    return {"cities": list_cities()}


@api_router.get("/traffic/current")
async def traffic_current(city: str = Query("pune")):
    if city not in CITIES:
        raise HTTPException(status_code=404, detail="Unknown city")
    incidents = ALERTS.get_incidents_for_engine(city)
    snap = snapshot_city(city, incidents=incidents)
    snap["routes_optimized"] = SESSION.routes_optimized
    return snap


@api_router.get("/geo/nearest")
async def geo_nearest(lat: float, lng: float, city: Optional[str] = None):
    """Find the closest road segment to given coordinates and the closest city.
    If city is provided, only search within that city's segments.
    """
    from math import radians, sin, cos, asin, sqrt

    def hav(a, b):
        lat1, lng1 = a
        lat2, lng2 = b
        dlat = radians(lat2 - lat1)
        dlng = radians(lng2 - lng1)
        aa = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
        return 2 * 6371 * asin(sqrt(aa))

    # Detect city if not provided (pick closest by center distance)
    picked_city = city
    if picked_city not in CITIES:
        best = None
        best_d = float("inf")
        for k, c in CITIES.items():
            d = hav((lat, lng), tuple(c["center"]))
            if d < best_d:
                best_d = d
                best = k
        picked_city = best

    segs = get_segments(picked_city)
    best_seg = None
    best_d = float("inf")
    for s in segs:
        # Check distance to both endpoints and to any polyline vertex if present
        pts = s.get("coords") or [s["from"], s["to"]]
        for pt in pts:
            d = hav((lat, lng), tuple(pt))
            if d < best_d:
                best_d = d
                best_seg = s
    return {
        "city": picked_city,
        "distance_km": round(best_d, 3),
        "segment": {
            "id": best_seg["id"],
            "name": best_seg["name"],
            "from": best_seg["from"],
            "to": best_seg["to"],
        } if best_seg else None,
    }


@api_router.post("/traffic/predict")
async def traffic_predict(req: PredictionRequest):
    if req.city not in CITIES:
        raise HTTPException(status_code=404, detail="Unknown city")
    return predict_congestion(
        city_key=req.city,
        start=req.start,
        destination=req.destination,
        when_iso=req.when,
        horizon_minutes=req.horizon_minutes,
        weather_impact=req.weather_impact,
        holiday_effect=req.holiday_effect,
        event_nearby=req.event_nearby,
    )


@api_router.post("/routes/optimize")
async def routes_optimize(req: RouteRequest):
    if req.city not in CITIES:
        raise HTTPException(status_code=404, detail="Unknown city")
    result = optimize_routes(req.city, req.start, req.destination)
    SESSION.bump_routes()
    result["session_routes_optimized"] = SESSION.routes_optimized
    return result


@api_router.get("/analytics/historical")
async def analytics(city: str = Query("pune")):
    if city not in CITIES:
        raise HTTPException(status_code=404, detail="Unknown city")
    return analytics_historical(city)


@api_router.get("/alerts")
async def alerts(city: str = Query("pune")):
    if city not in CITIES:
        raise HTTPException(status_code=404, detail="Unknown city")
    return {"city": city, "alerts": ALERTS.list(city)}


@api_router.get("/weather/current")
async def weather_current(city: str = Query("pune")):
    if city not in CITIES:
        raise HTTPException(status_code=404, detail="Unknown city")
    return current_weather_detailed(city)


@api_router.get("/weather/forecast")
async def weather_forecast_endpoint(city: str = Query("pune")):
    if city not in CITIES:
        raise HTTPException(status_code=404, detail="Unknown city")
    hourly = forecast_24h(city)
    weekly = weekly_forecast(city)
    return {"city": city, "hourly": hourly["hours"], "weekly": weekly}


@api_router.get("/geo/search")
async def geo_search(q: str, city: Optional[str] = None, limit: int = 6):
    """Search for a place / address via OSM Nominatim, biased to city if provided."""
    city_center = None
    if city and city in CITIES:
        city_center = CITIES[city]["center"]
    results = geocode_search(q=q, limit=limit, city_center=city_center)
    return {"q": q, "city": city, "results": results}


@api_router.post("/incident/simulate")
async def simulate_incident(req: IncidentRequest):
    if req.city not in CITIES:
        raise HTTPException(status_code=404, detail="Unknown city")
    alert = ALERTS.add_incident(req.city, req.segment_id)
    incidents = ALERTS.get_incidents_for_engine(req.city)
    snap = snapshot_city(req.city, incidents=incidents)
    snap["routes_optimized"] = SESSION.routes_optimized
    await MANAGER.broadcast(req.city, {"type": "snapshot", "payload": snap})
    await MANAGER.broadcast(req.city, {"type": "alert_added", "payload": alert})
    await MANAGER.broadcast(req.city, {"type": "alerts", "payload": ALERTS.list(req.city)})
    return {"alert": alert, "snapshot": snap}


class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, city: str):
        await ws.accept()
        self.rooms.setdefault(city, set()).add(ws)

    def disconnect(self, ws: WebSocket, city: str):
        if city in self.rooms and ws in self.rooms[city]:
            self.rooms[city].remove(ws)
            if not self.rooms[city]:
                del self.rooms[city]

    async def broadcast(self, city: str, message: dict):
        if city not in self.rooms:
            return
        dead = []
        for ws in list(self.rooms[city]):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, city)


MANAGER = ConnectionManager()


@app.websocket("/api/ws/traffic")
async def ws_traffic(websocket: WebSocket, city: str = "pune"):
    if city not in CITIES:
        await websocket.close(code=4004)
        return
    await MANAGER.connect(websocket, city)
    try:
        incidents = ALERTS.get_incidents_for_engine(city)
        snap = snapshot_city(city, incidents=incidents)
        snap["routes_optimized"] = SESSION.routes_optimized
        await websocket.send_json({"type": "snapshot", "payload": snap})
        await websocket.send_json({"type": "alerts", "payload": ALERTS.list(city)})
        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=45)
                if msg == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                try:
                    await websocket.send_json({"type": "heartbeat", "t": datetime.utcnow().isoformat()})
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logging.exception("ws error: %s", e)
    finally:
        MANAGER.disconnect(websocket, city)


async def broadcaster_loop():
    logging.info("broadcaster started")
    while True:
        try:
            for city_key in list(MANAGER.rooms.keys()):
                incidents = ALERTS.get_incidents_for_engine(city_key)
                snap = snapshot_city(city_key, incidents=incidents)
                snap["routes_optimized"] = SESSION.routes_optimized
                await MANAGER.broadcast(city_key, {"type": "snapshot", "payload": snap})
                await MANAGER.broadcast(city_key, {"type": "alerts", "payload": ALERTS.list(city_key)})
        except Exception as e:
            logging.exception("broadcaster error: %s", e)
        await asyncio.sleep(30)


@app.on_event("startup")
async def _startup():
    asyncio.create_task(broadcaster_loop())
    # Pre-warm segment caches for all cities sequentially in background
    async def prewarm():
        for city_key in list(CITIES.keys()):
            try:
                await asyncio.to_thread(get_segments, city_key)
                logging.info("Prewarmed segments for %s", city_key)
                # Larger delay between cities to avoid Overpass rate limits
                await asyncio.sleep(3.0)
            except Exception as e:
                logging.warning("Prewarm failed for %s: %s", city_key, e)
    asyncio.create_task(prewarm())


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# --- Single-service deployment: serve the built React app directly. ---
# Only activates if a production build exists (frontend/build). In local
# dev, run the CRA dev server separately (yarn start) instead -- this block
# simply does nothing if the build directory isn't present.
FRONTEND_BUILD_DIR = ROOT_DIR.parent / "frontend" / "build"

if FRONTEND_BUILD_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=FRONTEND_BUILD_DIR / "static"),
        name="static",
    )

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """SPA fallback: serve real build files (favicon, manifest, etc.)
        directly if they exist, otherwise serve index.html so client-side
        routing works. /api/* and /api/ws/* never reach here -- they're
        matched by api_router / the websocket route registered above."""
        candidate = FRONTEND_BUILD_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_BUILD_DIR / "index.html")
    logger.info("Serving frontend build from %s", FRONTEND_BUILD_DIR)
else:
    logger.info("No frontend build found at %s -- API-only mode", FRONTEND_BUILD_DIR)

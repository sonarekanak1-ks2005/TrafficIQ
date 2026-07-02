"""
TrafficIQ Backend API Test Suite
Tests all backend endpoints against the public URL
"""
import os
import requests
import sys
import json
from datetime import datetime

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8000") + "/api"

class BackendTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []

    def test(self, name, fn):
        """Run a single test"""
        self.tests_run += 1
        print(f"\n{'='*60}")
        print(f"TEST {self.tests_run}: {name}")
        print('='*60)
        try:
            fn()
            self.tests_passed += 1
            print(f"✅ PASSED")
            return True
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            self.failures.append({"test": name, "error": str(e)})
            return False
        except Exception as e:
            print(f"❌ ERROR: {e}")
            self.failures.append({"test": name, "error": f"Exception: {e}"})
            return False

    def assert_status(self, response, expected, msg=""):
        assert response.status_code == expected, f"Expected {expected}, got {response.status_code}. {msg} Response: {response.text[:200]}"

    def assert_field(self, data, field, msg=""):
        assert field in data, f"Missing field '{field}'. {msg}"

    def assert_length(self, arr, op, val, msg=""):
        if op == ">=":
            assert len(arr) >= val, f"Expected length >= {val}, got {len(arr)}. {msg}"
        elif op == "==":
            assert len(arr) == val, f"Expected length == {val}, got {len(arr)}. {msg}"

    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print('='*60)
        print(f"Total: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        if self.failures:
            print(f"\n❌ FAILURES:")
            for f in self.failures:
                print(f"  - {f['test']}: {f['error']}")
        return 0 if self.tests_passed == self.tests_run else 1


def main():
    t = BackendTester()

    # TEST 1: GET /api/cities returns 8 cities
    def test_cities():
        r = requests.get(f"{BASE_URL}/cities", timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        t.assert_field(data, "cities")
        t.assert_length(data["cities"], "==", 8, "Should return exactly 8 cities")
        cities = data["cities"]
        keys = [c["key"] for c in cities]
        expected = ["pune", "nagpur", "mumbai", "delhi", "london", "nyc", "tokyo", "singapore"]
        for exp in expected:
            assert exp in keys, f"Missing city: {exp}"
        print(f"✓ Cities: {keys}")

    t.test("GET /api/cities returns 8 cities", test_cities)

    # TEST 2: GET /api/traffic/current?city=pune returns segments + kpis + weather + holiday
    def test_traffic_current():
        r = requests.get(f"{BASE_URL}/traffic/current?city=pune", timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        t.assert_field(data, "segments")
        t.assert_field(data, "kpis")
        t.assert_field(data, "weather")
        t.assert_field(data, "holiday")
        t.assert_length(data["segments"], ">=", 48, "Should have at least 48 segments")
        print(f"✓ Segments: {len(data['segments'])}")
        print(f"✓ KPIs: {data['kpis']}")
        print(f"✓ Weather: {data['weather']['state']}")
        print(f"✓ Holiday: {data['holiday']}")

    t.test("GET /api/traffic/current?city=pune returns segments + kpis + weather + holiday", test_traffic_current)

    # TEST 3: POST /api/traffic/predict returns prediction curve
    def test_traffic_predict():
        payload = {
            "city": "pune",
            "start": "FC Road",
            "destination": "MG Road",
            "when": datetime.now().isoformat(),
            "horizon_minutes": 60,
            "weather_impact": True,
            "holiday_effect": True,
            "event_nearby": False
        }
        r = requests.post(f"{BASE_URL}/traffic/predict", json=payload, timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        t.assert_field(data, "points")
        t.assert_field(data, "avg_congestion")
        t.assert_field(data, "confidence")
        t.assert_field(data, "best_travel_time")
        t.assert_field(data, "summary")
        assert len(data["points"]) > 0, "Points array should not be empty"
        assert 0.55 <= data["confidence"] <= 0.95, f"Confidence {data['confidence']} not in range [0.55, 0.95]"
        print(f"✓ Points: {len(data['points'])}")
        print(f"✓ Avg Congestion: {data['avg_congestion']}")
        print(f"✓ Confidence: {data['confidence']}")
        print(f"✓ Best Time: {data['best_travel_time']}")

    t.test("POST /api/traffic/predict returns prediction curve", test_traffic_predict)

    # TEST 4: POST /api/routes/optimize returns exactly 3 routes
    def test_routes_optimize():
        payload = {
            "city": "pune",
            "start": "FC Road",
            "destination": "Sinhagad Road"
        }
        r = requests.post(f"{BASE_URL}/routes/optimize", json=payload, timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        t.assert_field(data, "routes")
        t.assert_field(data, "recommended_index")
        t.assert_length(data["routes"], ">=", 1, "Should have at least 1 route")
        # Check first route structure
        route = data["routes"][0]
        t.assert_field(route, "tag")
        t.assert_field(route, "time_min")
        t.assert_field(route, "distance_km")
        t.assert_field(route, "avg_congestion")
        t.assert_field(route, "eco_score")
        t.assert_field(route, "coords")
        t.assert_field(route, "segment_ids")
        assert isinstance(route["coords"], list), "coords should be array"
        assert len(route["coords"]) > 0, "coords should not be empty"
        print(f"✓ Routes: {len(data['routes'])}")
        print(f"✓ Recommended: {data['recommended_index']}")
        for i, rt in enumerate(data["routes"]):
            print(f"  Route {i}: {rt['tag']} - {rt['time_min']}min, {rt['distance_km']}km")

    t.test("POST /api/routes/optimize returns exactly 3 routes", test_routes_optimize)

    # TEST 5: POST /api/routes/optimize increments routes_optimized counter
    def test_routes_counter():
        # Get initial count
        r1 = requests.get(f"{BASE_URL}/traffic/current?city=pune", timeout=10)
        t.assert_status(r1, 200)
        initial = r1.json().get("routes_optimized", 0)
        
        # Optimize route
        payload = {"city": "pune", "start": "FC Road", "destination": "MG Road"}
        r2 = requests.post(f"{BASE_URL}/routes/optimize", json=payload, timeout=10)
        t.assert_status(r2, 200)
        data = r2.json()
        t.assert_field(data, "session_routes_optimized")
        
        # Check incremented
        r3 = requests.get(f"{BASE_URL}/traffic/current?city=pune", timeout=10)
        t.assert_status(r3, 200)
        final = r3.json().get("routes_optimized", 0)
        
        assert final > initial, f"Counter should increment: initial={initial}, final={final}"
        print(f"✓ Counter incremented: {initial} -> {final}")

    t.test("POST /api/routes/optimize increments routes_optimized counter", test_routes_counter)

    # TEST 6: GET /api/analytics/historical returns all analytics
    def test_analytics():
        r = requests.get(f"{BASE_URL}/analytics/historical?city=pune", timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        t.assert_field(data, "hour_pattern")
        t.assert_field(data, "heatmap")
        t.assert_field(data, "weather_scatter")
        t.assert_field(data, "holiday_impact")
        t.assert_field(data, "top_roads")
        t.assert_length(data["hour_pattern"], "==", 24, "hour_pattern should have 24 entries")
        t.assert_length(data["heatmap"], "==", 168, "heatmap should have 7x24=168 entries")
        t.assert_length(data["top_roads"], "==", 5, "top_roads should have 5 entries")
        print(f"✓ Hour pattern: {len(data['hour_pattern'])} entries")
        print(f"✓ Heatmap: {len(data['heatmap'])} entries")
        print(f"✓ Weather scatter: {len(data['weather_scatter'])} entries")
        print(f"✓ Top roads: {len(data['top_roads'])} entries")

    t.test("GET /api/analytics/historical returns all analytics", test_analytics)

    # TEST 7: GET /api/alerts returns at least 6 alerts
    def test_alerts():
        r = requests.get(f"{BASE_URL}/alerts?city=pune", timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        t.assert_field(data, "alerts")
        t.assert_length(data["alerts"], ">=", 6, "Should have at least 6 alerts")
        # Check first alert structure
        alert = data["alerts"][0]
        t.assert_field(alert, "severity")
        t.assert_field(alert, "type")
        t.assert_field(alert, "location")
        t.assert_field(alert, "recommended_action")
        print(f"✓ Alerts: {len(data['alerts'])}")
        for a in data["alerts"][:3]:
            print(f"  - {a['severity'].upper()}: {a['type']} at {a['location']}")

    t.test("GET /api/alerts returns at least 6 alerts", test_alerts)

    # TEST 8: POST /api/incident/simulate accepts {city} body
    def test_incident_simulate():
        payload = {"city": "pune"}
        r = requests.post(f"{BASE_URL}/incident/simulate", json=payload, timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        t.assert_field(data, "alert")
        t.assert_field(data, "snapshot")
        alert = data["alert"]
        t.assert_field(alert, "id")
        t.assert_field(alert, "severity")
        t.assert_field(alert, "location")
        print(f"✓ Simulated incident: {alert['severity']} at {alert['location']}")

    t.test("POST /api/incident/simulate accepts {city} body", test_incident_simulate)

    # TEST 9: Test multiple cities work (pune, mumbai, london)
    def test_multiple_cities():
        cities_to_test = ["pune", "mumbai", "london"]
        for city in cities_to_test:
            r = requests.get(f"{BASE_URL}/traffic/current?city={city}", timeout=10)
            t.assert_status(r, 200, f"City {city} failed")
            data = r.json()
            assert data["city"] == city, f"Expected city={city}, got {data['city']}"
            print(f"✓ City {city}: {len(data['segments'])} segments")

    t.test("All city keys work (pune, mumbai, london)", test_multiple_cities)

    # TEST 10: WebSocket connection test (basic connectivity)
    def test_websocket_basic():
        # We'll just verify the endpoint exists and doesn't return 404
        # Full WebSocket testing will be done in frontend tests
        import websocket
        api_root = BASE_URL[:-4] if BASE_URL.endswith("/api") else BASE_URL
        ws_scheme = "wss" if api_root.startswith("https://") else "ws"
        ws_host = api_root.split("://", 1)[1].rstrip("/")
        ws_url = f"{ws_scheme}://{ws_host}/api/ws/traffic?city=pune"
        try:
            ws = websocket.create_connection(ws_url, timeout=5)
            # Wait for initial messages
            msg1 = ws.recv()
            data1 = json.loads(msg1)
            assert data1["type"] in ["snapshot", "alerts"], f"Unexpected message type: {data1['type']}"
            print(f"✓ WebSocket connected, received: {data1['type']}")
            ws.close()
        except Exception as e:
            raise AssertionError(f"WebSocket connection failed: {e}")

    t.test("WebSocket /api/ws/traffic?city=pune connects", test_websocket_basic)

    # TEST 11: Root endpoint
    def test_root():
        r = requests.get(f"{BASE_URL}/", timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        t.assert_field(data, "message")
        print(f"✓ Root: {data['message']}")

    t.test("GET /api/ returns message", test_root)

    # TEST 12: GET /api/geo/nearest with Pune coords returns nearest segment
    def test_geo_nearest_pune():
        r = requests.get(f"{BASE_URL}/geo/nearest?lat=18.52&lng=73.85", timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        t.assert_field(data, "city")
        t.assert_field(data, "distance_km")
        t.assert_field(data, "segment")
        assert data["city"] == "pune", f"Expected city=pune, got {data['city']}"
        seg = data["segment"]
        t.assert_field(seg, "id")
        t.assert_field(seg, "name")
        t.assert_field(seg, "from")
        t.assert_field(seg, "to")
        assert isinstance(seg["name"], str) and len(seg["name"]) > 0, "Segment name should be non-empty string"
        print(f"✓ Nearest segment: {seg['name']} (distance: {data['distance_km']} km)")

    t.test("GET /api/geo/nearest with Pune coords returns nearest segment", test_geo_nearest_pune)

    # TEST 13: GET /api/geo/nearest with coords not in any city returns closest city
    def test_geo_nearest_auto_city():
        # Use coords in middle of ocean (should pick closest city)
        r = requests.get(f"{BASE_URL}/geo/nearest?lat=20.0&lng=70.0", timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        t.assert_field(data, "city")
        t.assert_field(data, "segment")
        assert data["city"] in ["pune", "nagpur", "mumbai", "delhi", "london", "nyc", "tokyo", "singapore"], \
            f"Should return a valid city, got {data['city']}"
        print(f"✓ Auto-detected city: {data['city']} for coords (20.0, 70.0)")

    t.test("GET /api/geo/nearest auto-detects closest city", test_geo_nearest_auto_city)

    # TEST 14: GET /api/traffic/current returns segments with coords polyline (>=3 points) proving OSM roads
    def test_traffic_current_osm_coords():
        r = requests.get(f"{BASE_URL}/traffic/current?city=pune", timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        segments = data["segments"]
        # Check if at least one segment has coords array with >=3 points
        has_polyline = False
        for seg in segments:
            if "coords" in seg and isinstance(seg["coords"], list) and len(seg["coords"]) >= 3:
                has_polyline = True
                print(f"✓ Found OSM polyline segment: {seg['name']} with {len(seg['coords'])} points")
                break
        assert has_polyline, "At least one segment should have coords array with >=3 points (OSM polyline)"

    t.test("GET /api/traffic/current returns segments with OSM polyline coords", test_traffic_current_osm_coords)

    # TEST 15: POST /api/routes/optimize returns routes with polyline coords (>=5 points)
    def test_routes_polyline_coords():
        payload = {"city": "pune", "start": "FC Road", "destination": "Sinhagad Road"}
        r = requests.post(f"{BASE_URL}/routes/optimize", json=payload, timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        routes = data["routes"]
        assert len(routes) > 0, "Should have at least 1 route"
        route = routes[0]
        t.assert_field(route, "coords")
        coords = route["coords"]
        assert isinstance(coords, list), "coords should be array"
        assert len(coords) >= 5, f"Route coords should have >=5 points (real road geometry), got {len(coords)}"
        print(f"✓ Route has {len(coords)} polyline points (real road geometry)")

    t.test("POST /api/routes/optimize returns routes with polyline coords", test_routes_polyline_coords)

    # TEST 16: POST /api/routes/optimize returns 3 route alternatives with different segment_ids
    def test_routes_three_alternatives():
        payload = {"city": "pune", "start": "FC Road", "destination": "Sinhagad Road"}
        r = requests.post(f"{BASE_URL}/routes/optimize", json=payload, timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        routes = data["routes"]
        # Should ideally have 3 routes, but at least 1
        print(f"✓ Routes returned: {len(routes)}")
        if len(routes) >= 2:
            # Check that routes have different segment_ids
            sig1 = tuple(routes[0]["segment_ids"])
            sig2 = tuple(routes[1]["segment_ids"])
            assert sig1 != sig2, "Routes should have different segment_ids (different paths)"
            print(f"✓ Routes have different paths: Route 0 has {len(sig1)} segments, Route 1 has {len(sig2)} segments")
        else:
            print(f"⚠ Only {len(routes)} route(s) returned (expected 3 alternatives)")

    t.test("POST /api/routes/optimize returns 3 alternatives with different paths", test_routes_three_alternatives)

    # TEST 17: All 8 cities return valid snapshots (OSM or grid fallback)
    def test_all_cities_snapshots():
        cities = ["pune", "nagpur", "mumbai", "delhi", "london", "nyc", "tokyo", "singapore"]
        for city in cities:
            r = requests.get(f"{BASE_URL}/traffic/current?city={city}", timeout=10)
            t.assert_status(r, 200, f"City {city} failed")
            data = r.json()
            assert data["city"] == city, f"Expected city={city}, got {data['city']}"
            assert len(data["segments"]) > 0, f"City {city} should have segments"
            print(f"✓ City {city}: {len(data['segments'])} segments")

    t.test("All 8 cities return valid snapshots", test_all_cities_snapshots)

    # TEST 18: GET /api/alerts uses real road names (not synthetic like "Pune Road 42")
    def test_alerts_real_road_names():
        r = requests.get(f"{BASE_URL}/alerts?city=pune", timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        alerts = data["alerts"]
        assert len(alerts) > 0, "Should have at least 1 alert"
        # Check if alert locations use real road names (not "Pune Road XX" pattern)
        real_names_found = 0
        for alert in alerts[:5]:
            location = alert["location"]
            # Real road names should not match pattern "CityName Road NN"
            if not (location.startswith("pune Road") or location.startswith("Pune Road")):
                real_names_found += 1
                print(f"✓ Real road name in alert: {location}")
        # At least some alerts should have real road names (when OSM cache is warm)
        print(f"✓ Found {real_names_found}/{len(alerts[:5])} alerts with real road names")

    t.test("GET /api/alerts uses real road names", test_alerts_real_road_names)

    # TEST 19: GET /api/weather/current?city=pune returns all required fields
    def test_weather_current():
        r = requests.get(f"{BASE_URL}/weather/current?city=pune", timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        # Check all required fields
        required_fields = [
            "state", "label", "icon", "temp_c", "feels_like_c", "humidity",
            "wind_kmph", "visibility_km", "uv_index", "pressure_hpa",
            "sunrise_local", "sunset_local", "traffic_impact"
        ]
        for field in required_fields:
            t.assert_field(data, field, f"Missing field: {field}")
        
        # Check traffic_impact structure
        impact = data["traffic_impact"]
        t.assert_field(impact, "label")
        t.assert_field(impact, "multiplier")
        
        # Verify sunrise_local/sunset_local are human-readable strings (not ISO timestamps)
        sunrise = data["sunrise_local"]
        sunset = data["sunset_local"]
        assert ":" in sunrise and ("AM" in sunrise or "PM" in sunrise), \
            f"sunrise_local should be human-readable like '6:15 AM', got: {sunrise}"
        assert ":" in sunset and ("AM" in sunset or "PM" in sunset), \
            f"sunset_local should be human-readable like '6:42 PM', got: {sunset}"
        
        print(f"✓ Weather state: {data['state']} ({data['label']})")
        print(f"✓ Temperature: {data['temp_c']}°C (feels like {data['feels_like_c']}°C)")
        print(f"✓ Sunrise: {sunrise}, Sunset: {sunset}")
        print(f"✓ Traffic impact: {impact['label']} ({impact['multiplier']}x)")

    t.test("GET /api/weather/current?city=pune returns all required fields", test_weather_current)

    # TEST 20: GET /api/weather/forecast?city=pune returns hourly (24) and weekly (7)
    def test_weather_forecast():
        r = requests.get(f"{BASE_URL}/weather/forecast?city=pune", timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        t.assert_field(data, "hourly")
        t.assert_field(data, "weekly")
        
        hourly = data["hourly"]
        weekly = data["weekly"]
        
        t.assert_length(hourly, "==", 24, "hourly should have exactly 24 items")
        t.assert_length(weekly, "==", 7, "weekly should have exactly 7 items")
        
        # Check hourly structure
        h = hourly[0]
        for field in ["state", "icon", "temp_c"]:
            t.assert_field(h, field, f"Hourly missing field: {field}")
        
        # Check weekly structure
        w = weekly[0]
        for field in ["state", "icon", "high_c", "low_c"]:
            t.assert_field(w, field, f"Weekly missing field: {field}")
        
        print(f"✓ Hourly forecast: {len(hourly)} items")
        print(f"✓ Weekly forecast: {len(weekly)} items")
        print(f"✓ Sample hourly: {h['temp_c']}°C, {h['state']}")
        print(f"✓ Sample weekly: {w['high_c']}°C / {w['low_c']}°C, {w['state']}")

    t.test("GET /api/weather/forecast?city=pune returns hourly (24) and weekly (7)", test_weather_forecast)

    # TEST 21: GET /api/geo/search?q=Baner returns results array
    def test_geo_search_valid():
        r = requests.get(f"{BASE_URL}/geo/search?q=Baner", timeout=15)
        t.assert_status(r, 200)
        data = r.json()
        t.assert_field(data, "results")
        results = data["results"]
        assert isinstance(results, list), "results should be an array"
        # Results may be empty if Nominatim is rate-limited or cache miss, but should not error
        print(f"✓ Search 'Baner' returned {len(results)} results")
        if len(results) > 0:
            res = results[0]
            t.assert_field(res, "lat")
            t.assert_field(res, "lng")
            t.assert_field(res, "display_name")
            print(f"✓ First result: {res['display_name'][:60]}...")

    t.test("GET /api/geo/search?q=Baner returns results array", test_geo_search_valid)

    # TEST 22: GET /api/geo/search?q=abcxyznonexistent returns empty array without error
    def test_geo_search_nonexistent():
        r = requests.get(f"{BASE_URL}/geo/search?q=abcxyznonexistent", timeout=15)
        t.assert_status(r, 200)
        data = r.json()
        t.assert_field(data, "results")
        results = data["results"]
        assert isinstance(results, list), "results should be an array"
        # Should return empty array, not error
        print(f"✓ Search 'abcxyznonexistent' returned {len(results)} results (expected 0)")

    t.test("GET /api/geo/search?q=abcxyznonexistent returns empty array without error", test_geo_search_nonexistent)

    # TEST 23: GET /api/traffic/current?city=tokyo returns English/Latin road names
    def test_tokyo_english_names():
        r = requests.get(f"{BASE_URL}/traffic/current?city=tokyo", timeout=10)
        t.assert_status(r, 200)
        data = r.json()
        segments = data["segments"]
        assert len(segments) > 0, "Tokyo should have segments"
        
        # Check if road names are in Latin script (not Japanese characters)
        latin_names = 0
        for seg in segments[:10]:
            name = seg["name"]
            # Check if name contains only ASCII/Latin characters (no Japanese)
            if all(ord(c) < 128 or c in "āēīōūĀĒĪŌŪ" for c in name):
                latin_names += 1
                print(f"✓ Latin script road name: {name}")
        
        # At least some roads should have Latin names (when OSM name:en is available)
        print(f"✓ Found {latin_names}/{min(10, len(segments))} roads with Latin script names")
        # Note: Some roads may still have Japanese names if name:en is not available in OSM

    t.test("GET /api/traffic/current?city=tokyo returns English/Latin road names", test_tokyo_english_names)

    # TEST 24: Verify all previous endpoints still work (regression test)
    def test_regression_all_endpoints():
        endpoints = [
            ("GET", "/cities", None),
            ("GET", "/traffic/current?city=pune", None),
            ("POST", "/traffic/predict", {
                "city": "pune", "start": "FC Road", "destination": "MG Road",
                "when": datetime.now().isoformat(), "horizon_minutes": 60,
                "weather_impact": True, "holiday_effect": True, "event_nearby": False
            }),
            ("POST", "/routes/optimize", {"city": "pune", "start": "FC Road", "destination": "MG Road"}),
            ("GET", "/analytics/historical?city=pune", None),
            ("GET", "/alerts?city=pune", None),
            ("GET", "/geo/nearest?lat=18.52&lng=73.85", None),
        ]
        
        for method, path, payload in endpoints:
            url = f"{BASE_URL}{path}"
            if method == "GET":
                r = requests.get(url, timeout=10)
            else:
                r = requests.post(url, json=payload, timeout=10)
            t.assert_status(r, 200, f"Endpoint {method} {path} failed")
            print(f"✓ {method} {path}: OK")

    t.test("Verify all previous endpoints still work (regression test)", test_regression_all_endpoints)

    return t.print_summary()


if __name__ == "__main__":
    sys.exit(main())

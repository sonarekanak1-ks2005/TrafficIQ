# TrafficIQ — Development Plan

## 1) Objectives
- Deliver a full-stack **Smart Traffic Congestion Prediction & Route Optimization** app with a premium dark UI (accent **#00D4FF**).
- Support **global city presets** via selector; render **live traffic segments** on Leaflet map.
- Provide **algorithmic LSTM-mimicking predictions** (rush hours, weekend, weather/holiday/event factors) with confidence.
- Enable **route optimization** with 3 alternatives and map highlighting.
- Provide **analytics + alerts** with **WebSocket** real-time updates (broadcast every 30s).
- Keep predictions/alerts **in-memory** (Mongo only if needed for structural/session scaffolding).

---

## 2) Implementation Steps

### Phase 1 — Core POC (WebSockets + simulator + map segments)
**Goal:** prove the most failure-prone flow: **server sim → WS broadcast → client render update**.

**Build (minimal):**
- Backend FastAPI:
  - `GET /api/cities`
  - `GET /api/traffic/current?city=` (initial payload)
  - `WS /api/ws/traffic?city=` pushes segments + alerts every 30s
  - `traffic_engine` generating segment speeds/congestion with time-of-day + DOW + weather flags
- Frontend React:
  - Single page: City selector + Leaflet map
  - WS client subscribes; segments recolor (green/yellow/red) and pulse on change

**Web search (best practice checklist):**
- FastAPI WebSocket patterns (connection manager, heartbeats, reconnection)
- React WS reconnection/backoff and cleanup on city switch

**POC user stories:**
1. As a user, I can pick a city and see its base road segments on a map.
2. As a user, I see segment colors change in real-time via WebSocket without refreshing.
3. As a user, I can switch cities and the WS stream re-subscribes correctly.
4. As a user, I can tell when the connection drops and reconnects automatically.
5. As a user, I can visually confirm rush-hour spikes by changing local time inputs (debug control).

**Exit criteria:**
- WS updates reliably every 30s; no memory leak on reconnect/city switch.
- Map renders 50–200 segments/city smoothly; colors match congestion thresholds.

---

### Phase 2 — V1 App Development (end-to-end MVP)
**Goal:** implement the full app around the proven core with all main pages wired to backend.

**Backend (FastAPI):**
- Endpoints:
  - `POST /api/traffic/predict` (time range + factors → curve + confidence + summary)
  - `POST /api/routes/optimize` (start/end → 3 routes + metrics)
  - `GET /api/analytics/historical?city=` (synthetic historical aggregates)
  - `GET /api/alerts?city=` (current in-memory active alerts)
  - `POST /api/incident/simulate` (inject incident → localized congestion impact)
- Engines/modules:
  - `prediction_model`: LSTM-mimic curve generator (rush windows, weekend modifier, weather/holiday/event multipliers, noise, confidence)
  - `route_optimizer`: graph + Dijkstra; generate 3 alternatives (time vs distance vs “eco”)
  - `alerts_engine`: incident types + severity + TTL in memory
  - `city_data`: presets for global cities with coordinates + named segments
- WebSocket:
  - broadcast: `{city, segments[], alerts[], serverTime}`
  - per-city rooms; connection manager

**Frontend (React/Tailwind/Framer Motion):**
- Layout: Sidebar + Topbar (logo, city selector, dark/light toggle)
- Pages:
  - Dashboard: live map + 4 stat cards + congestion gauge
  - Prediction: form + factor toggles + Recharts line chart
  - Routes: start/end + 3 options + map highlight
  - Analytics: hour bars + 7×24 heatmap + scatter + top roads
  - Alerts: real-time feed + filters + slide-in animations
- Shared:
  - `useTrafficSocket` hook; global context for city + live state
  - Loading/skeleton + empty states; graceful WS reconnect

**V1 user stories:**
1. As a user, I can see a premium dashboard with live map, gauge, and animated stats for my selected city.
2. As a user, I can predict congestion for a chosen time range and see an animated forecast curve with confidence.
3. As a user, I can toggle weather/holiday/event factors and instantly see prediction outputs change.
4. As a user, I can request optimal routes and compare 3 options by time/distance/congestion/eco score.
5. As a user, I can view analytics (hourly patterns + heatmap + top congested roads) for the selected city.
6. As a user, I can see live alerts and filter them by type and severity.

**End-of-phase:**
- Run one full E2E pass with testing agent across all pages and API/WS flows; fix regressions.

---

### Phase 3 — Feature Expansion + Hardening
**Target upgrades:**
- PDF export report (jsPDF) for current city snapshot (stats + chart + top roads + alerts)
- Incident simulation UX: “Simulate Incident” button + impact visualization on nearby segments
- Performance polish: segment clustering/viewport rendering limits if needed
- Light mode refinement + a11y pass (contrast, focus states)

**Phase 3 user stories:**
1. As a user, I can export a PDF report of current traffic conditions and predictions.
2. As a user, I can simulate an incident and watch congestion propagate on the map.
3. As a user, I can keep using the app smoothly even with frequent WS updates.
4. As a user, I can switch to light mode and still read all charts and map legends clearly.
5. As a user, I can recover from network drops without losing my city selection or breaking the UI.

**End-of-phase:**
- E2E test again; verify PDF generation, incident cascade, and WS resilience.

---

## 3) Next Actions
1. Implement **Phase 1 POC** backend (cities, current traffic, WS manager, simulator loop).
2. Implement **Phase 1 POC** frontend (Leaflet map + city selector + WS hook + segment coloring).
3. Verify POC exit criteria; fix reconnect/city-switch issues.
4. Proceed to Phase 2: scaffold full pages + wire endpoints.

---

## 4) Success Criteria
- WebSocket live updates every 30s with stable reconnect behavior and no duplicate listeners.
- Predictions reflect: rush hours, weekends, weather/holiday/event modifiers, and provide confidence.
- Route optimization returns 3 plausible alternatives with consistent metrics and map highlighting.
- Analytics + alerts load quickly and match selected city.
- UI matches premium dark theme with **#00D4FF** accent, smooth animations, and clear empty/loading states.

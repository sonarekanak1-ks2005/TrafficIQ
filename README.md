# TrafficIQ - Smart Traffic Congestion Prediction & Route Optimization

TrafficIQ is a full-stack traffic operations app for simulated global cities
(Pune, Nagpur, Mumbai, Delhi, London, NYC, Tokyo, Singapore). It combines live
congestion simulation over OSM road networks, OSRM routing with a Dijkstra
fallback, Nagpur LSTM forecasting, analytics, weather impact, and real-time
alerts over WebSockets.

The project is ready for independent deployment on Render, Vercel, or a
single full-stack hosting target. It does not depend on hosted editor overlays,
injected badges, or platform-specific preview URLs.

## Stack

- **Backend:** FastAPI, WebSockets, OSM/Overpass + OSRM integration, NumPy
  (LSTM inference - no PyTorch needed at runtime)
- **Frontend:** React (CRACO) + Tailwind + Framer Motion + Recharts + Leaflet
- **ML:** PyTorch-trained LSTM deployed through a lightweight NumPy inference
  path

## Local Development

**Backend**

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
yarn install
copy .env.example .env
yarn start
```

Set `REACT_APP_BACKEND_URL=http://localhost:8000` in `frontend/.env` for local
two-process development. When the frontend is served by FastAPI in a
single-service deployment, the app automatically uses the current origin.

## Deployment

See `DEPLOYMENT.md` for single-service Render deployment and split
Render/Vercel deployment.

## Model Status

- **Nagpur:** trained LSTM (`backend/lstm_predictor.py`)
- **All other cities:** deterministic simulator (`backend/prediction_model.py`)
  labeled as `"model": "formula_v1"` in API responses

# Deploying TrafficIQ

TrafficIQ can be deployed as one full-stack service or as separate frontend
and backend services. The single-service setup is the simplest path because
the React build, API, and WebSocket share one origin.

## Option A - Single Render Service

FastAPI is configured in `backend/server.py` to serve the built React app when
`frontend/build/` exists. One Python process handles the frontend, API, and
WebSocket.

1. Push the repo to GitHub.
2. In Render, create a **New Web Service** and connect the repo.
3. Leave **Root Directory** blank so Render can access both `frontend/` and
   `backend/`.
4. Set **Runtime** to Python 3.
5. Use this build command:

   ```bash
   cd frontend && yarn install && yarn build && cd ../backend && pip install -r requirements.txt
   ```

6. Use this start command:

   ```bash
   cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT
   ```

7. No frontend environment variable is required in this mode.
8. Open the Render URL when the deploy finishes.

Sanity checks:

- The root URL loads the React dashboard.
- `/api/` returns `{"message": "TrafficIQ API online", "cities": 8}`.
- DevTools Network shows a `101 Switching Protocols` request for
  `/api/ws/traffic`.

## Option B - Render Backend + Vercel Frontend

Use this if you want the frontend and backend to redeploy independently.

### Backend on Render

1. Create a Render Web Service from the repo.
2. Set **Root Directory** to `backend`.
3. Set **Build Command** to `pip install -r requirements.txt`.
4. Let Render use `backend/Procfile` for the start command.
5. Set `CORS_ORIGINS=*` for the first deploy, then lock it down to the Vercel
   URL after the frontend is live.
6. Confirm `https://your-backend.onrender.com/api/` returns the online message.

### Frontend on Vercel

1. Import the same repo into Vercel.
2. Set **Root Directory** to `frontend`.
3. Set **Install Command** to `yarn install`.
4. Use the default build command, `craco build`.
5. Set `REACT_APP_BACKEND_URL` to the Render backend URL with no trailing
   slash.
6. Deploy, then update Render `CORS_ORIGINS` to the exact Vercel URL.

## Push to GitHub

```bash
git init
git add .
git commit -m "Prepare TrafficIQ for independent deployment"
git remote add origin https://github.com/YOUR_USERNAME/TrafficIQ.git
git branch -M main
git push -u origin main
```

## Verify End to End

- Open the app URL and pick **Nagpur**.
- Confirm the map loads and the live status changes to `LIVE`.
- In DevTools, confirm `/api/ws/traffic` connects with status `101`.
- In the Prediction tab, Nagpur responses include `"model": "lstm_v1"`.
- Other city predictions include `"model": "formula_v1"`.

## Cold Starts

Render's free tier can sleep after inactivity. The first request after idle can
take 30-60 seconds. In single-service mode, that can also delay the first page
load because one process serves both the UI and API.

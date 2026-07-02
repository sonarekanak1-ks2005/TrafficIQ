import { createContext, useContext, useEffect, useMemo, useRef, useState, useCallback } from 'react';
import axios from 'axios';

// If REACT_APP_BACKEND_URL is unset, the app uses the same origin that served it.
// That keeps local builds and single-service deployments working without extra config.
const normalizeOrigin = (value) => {
    const fallback = window.location.origin;
    const raw = (value || fallback).trim().replace(/\/+$/, '');

    try {
        return new URL(raw).origin;
    } catch (_err) {
        return fallback;
    }
};

const BACKEND_URL = normalizeOrigin(process.env.REACT_APP_BACKEND_URL);
export const API = `${BACKEND_URL}/api`;

const TrafficContext = createContext(null);

const DEFAULT_CITY = 'pune';
const STORAGE_KEY_CITY = 'tiq.city';
const STORAGE_KEY_THEME = 'tiq.theme';

export const TrafficProvider = ({ children }) => {
    const [cities, setCities] = useState([]);
    const [city, setCityState] = useState(() => localStorage.getItem(STORAGE_KEY_CITY) || DEFAULT_CITY);
    const [snapshot, setSnapshot] = useState(null);
    const [alerts, setAlerts] = useState([]);
    const [wsStatus, setWsStatus] = useState('connecting');
    const [theme, setThemeState] = useState(() => localStorage.getItem(STORAGE_KEY_THEME) || 'dark');
    const [routesOptimized, setRoutesOptimized] = useState(0);

    const wsRef = useRef(null);
    const wsReconnectTimeout = useRef(null);
    const currentCityRef = useRef(city);

    const setCity = useCallback((next) => {
        setCityState(next);
        localStorage.setItem(STORAGE_KEY_CITY, next);
    }, []);

    const setTheme = useCallback((t) => {
        setThemeState(t);
        localStorage.setItem(STORAGE_KEY_THEME, t);
        if (t === 'light') {
            document.documentElement.classList.remove('dark');
            document.documentElement.classList.add('light');
        } else {
            document.documentElement.classList.remove('light');
            document.documentElement.classList.add('dark');
        }
    }, []);

    // Fetch cities on mount
    useEffect(() => {
        (async () => {
            try {
                const r = await axios.get(`${API}/cities`);
                setCities(r.data.cities || []);
            } catch (e) {
                console.error('Failed to load cities', e);
            }
        })();
    }, []);

    // Initial fetch on city change
    useEffect(() => {
        currentCityRef.current = city;
        let cancelled = false;
        (async () => {
            try {
                const [snapR, alertsR] = await Promise.all([
                    axios.get(`${API}/traffic/current?city=${city}`),
                    axios.get(`${API}/alerts?city=${city}`),
                ]);
                if (cancelled) return;
                setSnapshot(snapR.data);
                setAlerts(alertsR.data.alerts || []);
                setRoutesOptimized(snapR.data.routes_optimized || 0);
            } catch (e) {
                console.error('Failed initial fetch', e);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [city]);

    // WebSocket connection - reconnects on city change
    useEffect(() => {
        const backendOrigin = new URL(BACKEND_URL);
        const wsProtocol = backendOrigin.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${backendOrigin.host}/api/ws/traffic?city=${encodeURIComponent(city)}`;
        setWsStatus('connecting');

        // Close prior socket cleanly
        if (wsRef.current) {
            try {
                wsRef.current.close();
            } catch (_err) {
                // ignore close errors
            }
            wsRef.current = null;
        }
        if (wsReconnectTimeout.current) {
            clearTimeout(wsReconnectTimeout.current);
            wsReconnectTimeout.current = null;
        }

        let attempt = 0;
        let closedByEffect = false;

        const connect = () => {
            if (closedByEffect) return;

            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                if (wsRef.current !== ws) return;
                setWsStatus('live');
                attempt = 0;
                ws.send('ping');
            };
            ws.onmessage = (ev) => {
                if (wsRef.current !== ws || ev.data === 'pong') return;

                try {
                    const msg = JSON.parse(ev.data);
                    if (msg.type === 'snapshot') {
                        setSnapshot(msg.payload);
                        setRoutesOptimized(msg.payload.routes_optimized || 0);
                    } else if (msg.type === 'alerts') {
                        setAlerts(msg.payload || []);
                    } else if (msg.type === 'alert_added') {
                        setAlerts((prev) => [msg.payload, ...prev.filter((a) => a.id !== msg.payload.id)]);
                    }
                } catch (_err) {
                    // ignore parse errors
                }
            };
            ws.onclose = () => {
                if (closedByEffect || wsRef.current !== ws) return;
                wsRef.current = null;
                setWsStatus('reconnecting');
                attempt += 1;
                const delay = Math.min(15000, 800 * Math.pow(1.6, attempt));
                wsReconnectTimeout.current = setTimeout(connect, delay);
            };
            ws.onerror = () => {
                try {
                    ws.close();
                } catch (_err) {
                    // ignore
                }
            };
        };

        connect();

        return () => {
            closedByEffect = true;
            if (wsReconnectTimeout.current) clearTimeout(wsReconnectTimeout.current);
            if (wsRef.current) {
                try {
                    wsRef.current.close();
                } catch (_err) {
                    // ignore
                }
                wsRef.current = null;
            }
        };
    }, [city]);

    const currentCity = useMemo(
        () => cities.find((c) => c.key === city) || { key: city, name: city, center: [18.5, 73.85], zoom: 12 },
        [cities, city]
    );

    const value = useMemo(
        () => ({
            API,
            cities,
            city,
            setCity,
            currentCity,
            snapshot,
            alerts,
            wsStatus,
            theme,
            setTheme,
            routesOptimized,
        }),
        [cities, city, setCity, currentCity, snapshot, alerts, wsStatus, theme, setTheme, routesOptimized]
    );

    return <TrafficContext.Provider value={value}>{children}</TrafficContext.Provider>;
};

export const useTraffic = () => {
    const ctx = useContext(TrafficContext);
    if (!ctx) throw new Error('useTraffic must be used within TrafficProvider');
    return ctx;
};

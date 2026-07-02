import { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { LineChart as LineChartIcon, Sparkles, Loader2, LocateFixed } from 'lucide-react';
import { toast } from 'sonner';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, ComposedChart, ReferenceLine } from 'recharts';
import { useTraffic, API } from '@/contexts/TrafficContext';
import { PRED } from '@/constants/testIds';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useCurrentLocation } from '@/hooks/useCurrentLocation';
import { AddressSearch } from '@/components/AddressSearch';

const horizonOptions = [
    { value: 30, label: 'Next 30 min' },
    { value: 60, label: 'Next 60 min' },
    { value: 120, label: 'Next 2 hours' },
];

export default function Prediction() {
    const { city, setCity, snapshot } = useTraffic();
    const [start, setStart] = useState('');
    const [destination, setDestination] = useState('');
    const [when, setWhen] = useState(() => new Date().toISOString().slice(0, 16));
    const [horizon, setHorizon] = useState(60);
    const [weather, setWeather] = useState(true);
    const [holiday, setHoliday] = useState(true);
    const [eventNearby, setEventNearby] = useState(false);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const { detect: detectLocation, loading: geoLoading } = useCurrentLocation();

    const handleUseLocation = async (which) => {
        const res = await detectLocation({ city });
        if (!res || !res.segment) return;
        if (res.city && res.city !== city) {
            justSetByAction.current = true;
            setCity(res.city);
            toast.info(`Switched city to ${res.city.toUpperCase()} based on your location`);
        }
        const name = res.segment.name;
        if (which === 'start') {
            setStart(name);
            toast.success(`Start set: ${name} (${res.distance_km.toFixed(2)} km away)`);
        } else {
            setDestination(name);
            toast.success(`Destination set: ${name}`);
        }
    };

    const handleAddressPick = async (which, result) => {
        try {
            const r = await axios.get(`${API}/geo/nearest`, {
                params: { lat: result.lat, lng: result.lng, city },
            });
            const nearestSeg = r.data.segment;
            if (r.data.city && r.data.city !== city) {
                justSetByAction.current = true;
                setCity(r.data.city);
                toast.info(`Switched to ${r.data.city.toUpperCase()} based on address`);
            }
            const name = nearestSeg?.name || result.display_name.split(',')[0];
            if (which === 'start') {
                setStart(name);
                toast.success(`Start set: ${name}`);
            } else {
                setDestination(name);
                toast.success(`Destination set: ${name}`);
            }
        } catch (_e) {
            toast.error('Failed to resolve address');
        }
    };

    const roadOptions = useMemo(() => {
        const seen = new Set();
        return (snapshot?.segments || [])
            .filter((s) => {
                if (seen.has(s.name)) return false;
                seen.add(s.name);
                return true;
            })
            .slice(0, 30)
            .map((s) => s.name);
    }, [snapshot]);

    // Auto-fill defaults from available roads (only ONCE per city switch)
    const initialFilled = useRef(false);
    const justSetByAction = useRef(false);
    useEffect(() => {
        if (justSetByAction.current) {
            justSetByAction.current = false;
            initialFilled.current = true;
            return;
        }
        initialFilled.current = false;
        setStart('');
        setDestination('');
        setResult(null);
    }, [city]);

    useEffect(() => {
        if (initialFilled.current) return;
        if (roadOptions.length > 0) {
            if (!start && roadOptions[0]) setStart(roadOptions[0]);
            if (!destination && roadOptions[3]) setDestination(roadOptions[3]);
            initialFilled.current = true;
        }
    }, [roadOptions, start, destination]);

    const runPredict = async () => {
        try {
            setLoading(true);
            const r = await axios.post(`${API}/traffic/predict`, {
                city,
                start,
                destination,
                when: new Date(when).toISOString(),
                horizon_minutes: horizon,
                weather_impact: weather,
                holiday_effect: holiday,
                event_nearby: eventNearby,
            });
            setResult(r.data);
            toast.success('Prediction ready', { description: r.data.summary });
        } catch (e) {
            toast.error('Prediction failed');
        } finally {
            setLoading(false);
        }
    };

    const chartData = useMemo(
        () =>
            (result?.points || []).map((p) => ({
                t: p.minute_offset,
                congestion: p.congestion,
                low: p.conf_low,
                high: p.conf_high,
                bandHigh: p.conf_high,
                bandRange: p.conf_high - p.conf_low,
            })),
        [result]
    );

    const bestT = useMemo(() => {
        if (!result?.best_travel_time) return null;
        const d = new Date(result.best_travel_time);
        return d.toLocaleString();
    }, [result]);

    return (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            <motion.div
                className="lg:col-span-5 tiq-card p-5 flex flex-col gap-4"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
            >
                <div className="flex items-center gap-2">
                    <LineChartIcon className="h-4 w-4 text-[color:var(--tiq-primary)]" />
                    <div className="section-title mb-0">Forecast Inputs</div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                    <div className="col-span-2">
                        <div className="flex items-center justify-between">
                            <Label className="kpi-label">Start Location</Label>
                            <button
                                type="button"
                                onClick={() => handleUseLocation('start')}
                                disabled={geoLoading}
                                data-testid="prediction-use-location-start"
                                className="text-[11px] mono flex items-center gap-1 text-[color:var(--tiq-primary)] hover:underline disabled:opacity-60"
                            >
                                {geoLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <LocateFixed className="h-3 w-3" />}
                                Use my location
                            </button>
                        </div>
                        <AddressSearch
                            value={start}
                            onChange={setStart}
                            onPick={(r) => handleAddressPick('start', r)}
                            onPickRoad={setStart}
                            roadOptions={roadOptions}
                            city={city}
                            testId={PRED.startInput}
                            placeholder="Type a road, address or place…"
                            className="mt-1"
                        />
                    </div>
                    <div className="col-span-2">
                        <div className="flex items-center justify-between">
                            <Label className="kpi-label">Destination</Label>
                            <button
                                type="button"
                                onClick={() => handleUseLocation('destination')}
                                disabled={geoLoading}
                                data-testid="prediction-use-location-dest"
                                className="text-[11px] mono flex items-center gap-1 text-[color:var(--tiq-primary)] hover:underline disabled:opacity-60"
                            >
                                {geoLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <LocateFixed className="h-3 w-3" />}
                                Use my location
                            </button>
                        </div>
                        <AddressSearch
                            value={destination}
                            onChange={setDestination}
                            onPick={(r) => handleAddressPick('destination', r)}
                            onPickRoad={setDestination}
                            roadOptions={roadOptions}
                            city={city}
                            testId={PRED.destInput}
                            placeholder="Type a road, address or place…"
                            className="mt-1"
                        />
                    </div>
                    <datalist id="roads-list">
                        {roadOptions.map((r) => (
                            <option key={r} value={r} />
                        ))}
                    </datalist>
                    <div className="col-span-2 md:col-span-1">
                        <Label className="kpi-label">Date &amp; Time</Label>
                        <Input
                            type="datetime-local"
                            data-testid={PRED.dateInput}
                            value={when}
                            onChange={(e) => setWhen(e.target.value)}
                            className="mt-1 bg-transparent border-[color:var(--tiq-border-strong)] mono"
                        />
                    </div>
                    <div className="col-span-2 md:col-span-1">
                        <Label className="kpi-label">Time Range</Label>
                        <Select value={String(horizon)} onValueChange={(v) => setHorizon(Number(v))}>
                            <SelectTrigger data-testid={PRED.horizonSelect} className="mt-1 bg-transparent border-[color:var(--tiq-border-strong)]">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-[color:var(--tiq-card)] border-[color:var(--tiq-border)] text-[color:var(--tiq-foreground)]">
                                {horizonOptions.map((o) => (
                                    <SelectItem key={o.value} value={String(o.value)}>
                                        {o.label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                <div className="tiq-divider" />

                <div className="section-title">Factors</div>
                <div className="grid grid-cols-1 gap-3">
                    {[
                        { label: 'Weather Impact', value: weather, set: setWeather, testId: PRED.weatherToggle, hint: 'Include rain/fog effects' },
                        { label: 'Holiday Effect', value: holiday, set: setHoliday, testId: PRED.holidayToggle, hint: 'Reduce weekday commute if holiday' },
                        { label: 'Event Nearby', value: eventNearby, set: setEventNearby, testId: PRED.eventToggle, hint: 'Simulate stadium / festival' },
                    ].map((f) => (
                        <div key={f.label} className="flex items-center justify-between gap-3 py-1">
                            <div>
                                <div className="text-sm font-medium">{f.label}</div>
                                <div className="text-xs text-[color:var(--tiq-muted)]">{f.hint}</div>
                            </div>
                            <Switch checked={f.value} onCheckedChange={f.set} data-testid={f.testId} />
                        </div>
                    ))}
                </div>

                <button
                    className="tiq-btn-primary flex items-center justify-center gap-2 mono"
                    onClick={runPredict}
                    disabled={loading}
                    data-testid={PRED.predictBtn}
                >
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                    Predict Congestion
                </button>
            </motion.div>

            <motion.div
                className="lg:col-span-7 tiq-card p-5 min-h-[520px] flex flex-col"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.05 }}
                data-testid={PRED.resultCard}
            >
                <div className="flex items-center justify-between flex-wrap gap-2">
                    <div>
                        <div className="section-title mb-0">Forecast Result</div>
                        {result && (
                            <div className="text-xs text-[color:var(--tiq-muted)] mono mt-1">
                                {result.start || 'Any'} → {result.destination || 'Any'} · {result.horizon_minutes}m horizon
                            </div>
                        )}
                    </div>
                    {result && (
                        <div className="flex items-center gap-2">
                            <span className="tiq-chip mono" style={{ borderColor: 'rgba(0,212,255,0.35)', color: 'var(--tiq-primary)' }}>
                                Confidence {(result.confidence * 100).toFixed(0)}%
                            </span>
                        </div>
                    )}
                </div>

                {!result && (
                    <div className="flex-1 grid place-items-center text-[color:var(--tiq-muted)]">
                        <div className="text-center">
                            <Sparkles className="h-8 w-8 mx-auto mb-2 opacity-60" />
                            <div>Configure inputs and run a prediction.</div>
                        </div>
                    </div>
                )}

                {result && (
                    <>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                            <div className="tiq-card-2 p-3">
                                <div className="kpi-label">Avg Congestion</div>
                                <div className="kpi-value">{result.avg_congestion.toFixed(1)}</div>
                                <div className="text-xs mono text-[color:var(--tiq-muted)]">out of 100</div>
                            </div>
                            <div className="tiq-card-2 p-3">
                                <div className="kpi-label">Predicted Speed</div>
                                <div className="kpi-value">{result.predicted_speed_kmph}</div>
                                <div className="text-xs mono text-[color:var(--tiq-muted)]">kmph</div>
                            </div>
                            <div className="tiq-card-2 p-3">
                                <div className="kpi-label">Peak Congestion</div>
                                <div className="kpi-value">{result.peak_congestion}</div>
                                <div className="text-xs mono text-[color:var(--tiq-muted)]">max in window</div>
                            </div>
                            <div className="tiq-card-2 p-3">
                                <div className="kpi-label">Best Travel Time</div>
                                <div className="text-sm font-medium mono mt-1">{bestT}</div>
                                <div className="text-xs text-[color:var(--tiq-muted)] mt-1">lowest congestion</div>
                            </div>
                        </div>

                        <div className="mt-4 tiq-card-2 p-3">
                            <div className="text-sm">{result.summary}</div>
                        </div>

                        <div className="mt-4 flex-1 min-h-[280px]" data-testid={PRED.chart}>
                            <ResponsiveContainer width="100%" height={300}>
                                <ComposedChart data={chartData} margin={{ top: 10, right: 12, left: 0, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="congGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="#00D4FF" stopOpacity={0.28} />
                                            <stop offset="100%" stopColor="#00D4FF" stopOpacity={0.02} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid stroke="rgba(255,255,255,0.06)" />
                                    <XAxis
                                        dataKey="t"
                                        stroke="rgba(237,239,242,0.55)"
                                        tickFormatter={(v) => `+${v}m`}
                                        tick={{ fontFamily: 'JetBrains Mono', fontSize: 11 }}
                                    />
                                    <YAxis stroke="rgba(237,239,242,0.55)" domain={[0, 100]} tick={{ fontFamily: 'JetBrains Mono', fontSize: 11 }} />
                                    <Tooltip />
                                    <Area dataKey="bandHigh" stroke="none" fill="rgba(0,212,255,0.06)" isAnimationActive={false} />
                                    <Line
                                        type="monotone"
                                        dataKey="congestion"
                                        stroke="#00D4FF"
                                        strokeWidth={2.4}
                                        dot={false}
                                        isAnimationActive={true}
                                        animationDuration={800}
                                        fill="url(#congGrad)"
                                    />
                                    <ReferenceLine y={66} stroke="#FF4D4D" strokeDasharray="3 4" label={{ value: 'Congested', fill: '#FF4D4D', fontSize: 10 }} />
                                    <ReferenceLine y={33} stroke="#F7C948" strokeDasharray="3 4" label={{ value: 'Moderate', fill: '#F7C948', fontSize: 10 }} />
                                </ComposedChart>
                            </ResponsiveContainer>
                        </div>
                    </>
                )}
            </motion.div>
        </div>
    );
}

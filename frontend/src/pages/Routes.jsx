import { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Loader2, RouteIcon, Sparkles, Navigation, Leaf, Zap, Clock, LocateFixed, MousePointerClick } from 'lucide-react';
import { toast } from 'sonner';
import { useTraffic, API } from '@/contexts/TrafficContext';
import { ROUTE } from '@/constants/testIds';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { TrafficMap } from '@/components/TrafficMap';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useCurrentLocation } from '@/hooks/useCurrentLocation';
import { AddressSearch } from '@/components/AddressSearch';

const TAG_ICON = {
    Fastest: Zap,
    Shortest: Navigation,
    Eco: Leaf,
};

export default function Routes() {
    const { snapshot, currentCity, city, setCity, theme } = useTraffic();
    const [start, setStart] = useState('');
    const [destination, setDestination] = useState('');
    const [routes, setRoutes] = useState([]);
    const [selectedIdx, setSelectedIdx] = useState(0);
    const [startCoord, setStartCoord] = useState(null);
    const [endCoord, setEndCoord] = useState(null);
    const [loading, setLoading] = useState(false);
    const [pickMode, setPickMode] = useState(null); // 'start' | 'destination' | null
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

    const handleMapClick = async (lat, lng) => {
        if (!pickMode) return;
        try {
            const r = await axios.get(`${API}/geo/nearest`, { params: { lat, lng, city } });
            const seg = r.data.segment;
            if (!seg) {
                toast.error('No nearby road found');
                return;
            }
            if (pickMode === 'start') {
                setStart(seg.name);
                toast.success(`Start set: ${seg.name}`);
            } else {
                setDestination(seg.name);
                toast.success(`Destination set: ${seg.name}`);
            }
        } catch (_e) {
            toast.error('Failed to identify road');
        } finally {
            setPickMode(null);
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

    const initialFilled = useRef(false);
    const justSetByAction = useRef(false); // true when setCity was triggered by geo/address action
    // On manual city change (via selector), reset the fields. On geo/address-driven
    // city change (which also sets start/destination in the same batch), preserve them.
    useEffect(() => {
        if (justSetByAction.current) {
            justSetByAction.current = false;
            initialFilled.current = true; // don't auto-fill, values are already set
            return;
        }
        initialFilled.current = false;
        setStart('');
        setDestination('');
        setRoutes([]);
        setStartCoord(null);
        setEndCoord(null);
    }, [city]);

    useEffect(() => {
        if (initialFilled.current) return;
        if (roadOptions.length > 0) {
            if (!start && roadOptions[0]) setStart(roadOptions[0]);
            if (!destination && roadOptions[5]) setDestination(roadOptions[5]);
            initialFilled.current = true;
        }
    }, [roadOptions, start, destination]);

    const findRoutes = async () => {
        if (!start || !destination) {
            toast.error('Enter start and destination');
            return;
        }
        try {
            setLoading(true);
            const r = await axios.post(`${API}/routes/optimize`, { city, start, destination });
            setRoutes(r.data.routes || []);
            setSelectedIdx(r.data.recommended_index || 0);
            setStartCoord(r.data.start?.coord || null);
            setEndCoord(r.data.destination?.coord || null);
            toast.success(`Found ${r.data.routes.length} route options`);
        } catch (e) {
            toast.error('Route search failed');
        } finally {
            setLoading(false);
        }
    };

    const selected = routes[selectedIdx];

    return (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            <motion.div
                className="lg:col-span-5 flex flex-col gap-4"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
            >
                <div className="tiq-card p-5 flex flex-col gap-3">
                    <div className="section-title">Trip Details</div>
                    <div>
                        <div className="flex items-center justify-between">
                            <Label className="kpi-label">Start</Label>
                            <div className="flex items-center gap-2">
                                <button
                                    type="button"
                                    onClick={() => setPickMode(pickMode === 'start' ? null : 'start')}
                                    data-testid="route-pick-start"
                                    className={`text-[11px] mono flex items-center gap-1 hover:underline ${pickMode === 'start' ? 'text-[#F7C948]' : 'text-[color:var(--tiq-muted)]'}`}
                                >
                                    <MousePointerClick className="h-3 w-3" />
                                    {pickMode === 'start' ? 'Click map…' : 'Pick on map'}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => handleUseLocation('start')}
                                    disabled={geoLoading}
                                    data-testid="route-use-location-start"
                                    className="text-[11px] mono flex items-center gap-1 text-[color:var(--tiq-primary)] hover:underline disabled:opacity-60"
                                >
                                    {geoLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <LocateFixed className="h-3 w-3" />}
                                    Use my location
                                </button>
                            </div>
                        </div>
                        <AddressSearch
                            value={start}
                            onChange={setStart}
                            onPick={(r) => handleAddressPick('start', r)}
                            onPickRoad={setStart}
                            roadOptions={roadOptions}
                            city={city}
                            testId={ROUTE.startInput}
                            placeholder="Type a road, address or place…"
                            className="mt-1"
                        />
                    </div>
                    <div>
                        <div className="flex items-center justify-between">
                            <Label className="kpi-label">Destination</Label>
                            <div className="flex items-center gap-2">
                                <button
                                    type="button"
                                    onClick={() => setPickMode(pickMode === 'destination' ? null : 'destination')}
                                    data-testid="route-pick-dest"
                                    className={`text-[11px] mono flex items-center gap-1 hover:underline ${pickMode === 'destination' ? 'text-[#F7C948]' : 'text-[color:var(--tiq-muted)]'}`}
                                >
                                    <MousePointerClick className="h-3 w-3" />
                                    {pickMode === 'destination' ? 'Click map…' : 'Pick on map'}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => handleUseLocation('destination')}
                                    disabled={geoLoading}
                                    data-testid="route-use-location-dest"
                                    className="text-[11px] mono flex items-center gap-1 text-[color:var(--tiq-primary)] hover:underline disabled:opacity-60"
                                >
                                    {geoLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <LocateFixed className="h-3 w-3" />}
                                    Use my location
                                </button>
                            </div>
                        </div>
                        <AddressSearch
                            value={destination}
                            onChange={setDestination}
                            onPick={(r) => handleAddressPick('destination', r)}
                            onPickRoad={setDestination}
                            roadOptions={roadOptions}
                            city={city}
                            testId={ROUTE.destInput}
                            placeholder="Type a road, address or place…"
                            className="mt-1"
                        />
                    </div>
                    <datalist id="routes-roads">
                        {roadOptions.map((r) => (
                            <option key={r} value={r} />
                        ))}
                    </datalist>
                    <button
                        className="tiq-btn-primary flex items-center justify-center gap-2 mono"
                        onClick={findRoutes}
                        disabled={loading}
                        data-testid={ROUTE.findBtn}
                    >
                        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                        Find Optimal Route
                    </button>
                    {pickMode && (
                        <div className="text-[11px] text-[#F7C948] mono">
                            Click anywhere on the map to set the {pickMode}.
                        </div>
                    )}
                </div>

                <div className="tiq-card p-5">
                    <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="section-title mb-0">Route Options</div>
                        {routes.length > 0 && routes[0].source === 'osrm' && (
                            <span className="tiq-chip mono text-[10px]" style={{ borderColor: 'rgba(46,229,157,0.35)', color: '#2EE59D' }}>
                                REAL ROUTING · OSRM
                            </span>
                        )}
                    </div>
                    {routes.length === 0 && (
                        <div className="text-sm text-[color:var(--tiq-muted)] mt-3">Run a search to see options.</div>
                    )}
                    <div className="flex flex-col gap-2 mt-3">
                        {routes.map((r, idx) => {
                            const Icon = TAG_ICON[r.tag] || RouteIcon;
                            return (
                                <button
                                    key={idx}
                                    onClick={() => setSelectedIdx(idx)}
                                    data-testid={`${ROUTE.selectRoute}-${idx}`}
                                    className={`route-row ${idx === selectedIdx ? 'selected' : ''}`}
                                >
                                    <div className="flex items-center gap-3 text-left">
                                        <div className="h-9 w-9 rounded-lg grid place-items-center" style={{ background: 'rgba(0,212,255,0.10)' }}>
                                            <Icon className="h-4 w-4 text-[color:var(--tiq-primary)]" />
                                        </div>
                                        <div>
                                            <div className="text-sm font-semibold">{r.tag}</div>
                                            <div className="text-xs text-[color:var(--tiq-muted)] mono">
                                                {r.time_min.toFixed(1)} min · {r.distance_km.toFixed(2)} km
                                                {r.free_flow_min && r.free_flow_min < r.time_min && (
                                                    <span className="ml-1 opacity-70">
                                                        (+{(r.time_min - r.free_flow_min).toFixed(1)} traffic)
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-xs kpi-label">Congestion</div>
                                        <div className="mono text-sm" style={{ color: r.avg_congestion >= 66 ? '#FF4D4D' : r.avg_congestion >= 33 ? '#F7C948' : '#2EE59D' }}>
                                            {r.avg_congestion.toFixed(1)}%
                                        </div>
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                </div>
            </motion.div>

            <motion.div className="lg:col-span-7 flex flex-col gap-4" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: 0.05 }}>
                <TrafficMap
                    center={currentCity.center}
                    zoom={currentCity.zoom}
                    segments={snapshot?.segments || []}
                    theme={theme}
                    height={420}
                    highlightRouteCoords={selected?.coords || null}
                    startCoord={startCoord}
                    endCoord={endCoord}
                    onMapClick={pickMode ? handleMapClick : null}
                />
                <div className="tiq-card p-5">
                    <div className="section-title">Comparison</div>
                    <div className="overflow-x-auto">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Option</TableHead>
                                    <TableHead className="mono">Time</TableHead>
                                    <TableHead className="mono">Distance</TableHead>
                                    <TableHead className="mono">Avg Speed</TableHead>
                                    <TableHead className="mono">Congestion</TableHead>
                                    <TableHead className="mono">Eco Score</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {routes.map((r, idx) => (
                                    <TableRow key={idx} className={idx === selectedIdx ? 'bg-[rgba(0,212,255,0.05)]' : ''} data-testid={`${ROUTE.routeRow}-${idx}`}>
                                        <TableCell className="font-semibold">
                                            <div className="flex items-center gap-2">
                                                <span className="h-2 w-2 rounded-full" style={{ background: idx === selectedIdx ? '#00D4FF' : 'rgba(255,255,255,0.25)' }} />
                                                {r.tag}
                                            </div>
                                        </TableCell>
                                        <TableCell className="mono"><Clock className="h-3 w-3 inline mr-1 opacity-60" />{r.time_min.toFixed(1)} min</TableCell>
                                        <TableCell className="mono">{r.distance_km.toFixed(2)} km</TableCell>
                                        <TableCell className="mono">{r.avg_speed_kmph.toFixed(1)} kmph</TableCell>
                                        <TableCell className="mono">{r.avg_congestion.toFixed(1)}%</TableCell>
                                        <TableCell className="mono">{r.eco_score.toFixed(0)}</TableCell>
                                    </TableRow>
                                ))}
                                {routes.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={6} className="text-center text-[color:var(--tiq-muted)]">
                                            No routes yet.
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </div>

                {selected && selected.steps && selected.steps.length > 0 && (
                    <div className="tiq-card p-5">
                        <div className="flex items-center justify-between">
                            <div className="section-title mb-0">Turn-by-Turn Directions</div>
                            <div className="text-xs text-[color:var(--tiq-muted)] mono">{selected.steps.length} steps · {selected.tag}</div>
                        </div>
                        <div className="mt-3 flex flex-col gap-1.5 max-h-[300px] overflow-y-auto pr-1">
                            {selected.steps.map((s, i) => (
                                <div key={i} className="flex items-start gap-3 py-1.5 px-2 rounded-lg hover:bg-white/[0.03]">
                                    <div className="h-6 w-6 rounded-full grid place-items-center bg-[rgba(0,212,255,0.14)] text-[color:var(--tiq-primary)] text-[10px] mono font-semibold flex-shrink-0">
                                        {i + 1}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="text-sm">{s.instruction}</div>
                                        {s.distance_m > 0 && (
                                            <div className="text-[11px] mono text-[color:var(--tiq-muted)] mt-0.5">
                                                {s.distance_m >= 1000 ? `${(s.distance_m / 1000).toFixed(2)} km` : `${Math.round(s.distance_m)} m`}
                                                {s.duration_s > 0 && ` · ${Math.round(s.duration_s)} s`}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </motion.div>
        </div>
    );
}

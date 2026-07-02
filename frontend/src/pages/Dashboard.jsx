import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Activity, Gauge, AlertTriangle, Route as RouteIcon, PlayCircle, FileDown, LocateFixed, Loader2 } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { useTraffic, API } from '@/contexts/TrafficContext';
import { StatCard } from '@/components/StatCard';
import { ArcGauge } from '@/components/ArcGauge';
import { TrafficMap } from '@/components/TrafficMap';
import { KPI, TOPBAR } from '@/constants/testIds';
import { Badge } from '@/components/ui/badge';
import { useCurrentLocation } from '@/hooks/useCurrentLocation';

const SEVERITY_STYLE = {
    critical: { badge: 'bg-[rgba(255,77,77,0.14)] text-[#FFB3B3] border-[rgba(255,77,77,0.28)]', dot: '#FF4D4D' },
    high: { badge: 'bg-[rgba(247,201,72,0.14)] text-[#FFE3A3] border-[rgba(247,201,72,0.28)]', dot: '#F7C948' },
    medium: { badge: 'bg-[rgba(0,212,255,0.12)] text-[#BDEFFF] border-[rgba(0,212,255,0.22)]', dot: '#00D4FF' },
    low: { badge: 'bg-[rgba(46,229,157,0.12)] text-[#B9F7DE] border-[rgba(46,229,157,0.22)]', dot: '#2EE59D' },
};

export default function Dashboard() {
    const { snapshot, alerts, currentCity, city, setCity, theme, routesOptimized } = useTraffic();
    const [busy, setBusy] = useState(false);
    const { detect: detectLocation, loading: geoLoading } = useCurrentLocation();

    const handleUseLocation = async () => {
        const res = await detectLocation();
        if (!res) return;
        if (res.city && res.city !== city) {
            setCity(res.city);
            toast.success(`Switched to nearest city: ${res.city.toUpperCase()}`);
        } else {
            toast.info(`You appear to be in ${res.city.toUpperCase()}`);
        }
    };

    const segments = snapshot?.segments || [];
    const kpis = snapshot?.kpis || { congestion_index: 0, avg_speed_kmph: 0, segments_congested: 0, segments_total: 0 };

    const activeAlerts = alerts || [];
    const incidents = useMemo(
        () => activeAlerts.filter((a) => ['accident', 'closure', 'roadwork'].includes(a.type)).length,
        [activeAlerts]
    );
    const criticalHigh = useMemo(
        () => activeAlerts.filter((a) => a.severity === 'critical' || a.severity === 'high').slice(0, 5),
        [activeAlerts]
    );

    const weather = snapshot?.weather || { state: 'clear', temp_c: 25 };

    const simulateIncident = async () => {
        try {
            setBusy(true);
            const r = await axios.post(`${API}/incident/simulate`, { city });
            toast.success(`Incident simulated on ${r.data.alert.location}`, {
                description: 'Nearby segments will show increased congestion.',
            });
        } catch (e) {
            toast.error('Failed to simulate incident');
        } finally {
            setBusy(false);
        }
    };

    const exportPdf = async () => {
        try {
            const [{ default: jsPDF }] = await Promise.all([import('jspdf')]);
            const doc = new jsPDF({ orientation: 'portrait', unit: 'pt', format: 'a4' });
            const now = new Date().toISOString();
            doc.setFillColor(10, 10, 10);
            doc.rect(0, 0, 595, 80, 'F');
            doc.setTextColor(0, 212, 255);
            doc.setFontSize(22);
            doc.text('TrafficIQ Report', 40, 45);
            doc.setTextColor(200, 200, 200);
            doc.setFontSize(11);
            doc.text(`${currentCity.name} · ${now}`, 40, 65);

            doc.setTextColor(20, 20, 20);
            let y = 110;
            doc.setFontSize(14);
            doc.text('Key Metrics', 40, y);
            y += 20;
            doc.setFontSize(11);
            doc.text(`Congestion Index: ${kpis.congestion_index}`, 40, y);
            y += 16;
            doc.text(`Avg Speed: ${kpis.avg_speed_kmph} kmph`, 40, y);
            y += 16;
            doc.text(`Incidents Today: ${incidents}`, 40, y);
            y += 16;
            doc.text(`Routes Optimized (session): ${routesOptimized}`, 40, y);
            y += 24;
            doc.text(`Weather: ${weather.state} · ${weather.temp_c}°C`, 40, y);
            y += 16;
            doc.text(`Segments Total: ${kpis.segments_total} · Congested: ${kpis.segments_congested}`, 40, y);
            y += 24;

            doc.setFontSize(14);
            doc.text('Top Alerts', 40, y);
            y += 16;
            doc.setFontSize(10);
            criticalHigh.forEach((a) => {
                doc.text(`[${a.severity.toUpperCase()}] ${a.title} — ${a.location}`, 40, y);
                y += 14;
            });

            doc.save(`trafficiq-${currentCity.key}-report.pdf`);
            toast.success('Report exported');
        } catch (e) {
            toast.error('PDF export failed');
        }
    };

    return (
        <div className="flex flex-col gap-6">
            {/* Top actions row */}
            <div className="flex items-center justify-between gap-3 flex-wrap">
                <div>
                    <div className="section-title">Live · {currentCity.name}</div>
                    <div className="text-2xl font-semibold">
                        Smart City Traffic Operations
                    </div>
                    <div className="text-sm text-[color:var(--tiq-muted)] mt-1">
                        Weather: <span className="mono">{weather.state}</span> · <span className="mono">{weather.temp_c}°C</span>
                        {snapshot?.holiday && <span className="ml-2 tiq-chip" style={{ borderColor: 'rgba(0,212,255,0.35)' }}>HOLIDAY</span>}
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        className="tiq-btn-secondary flex items-center gap-2 mono text-sm"
                        onClick={handleUseLocation}
                        disabled={geoLoading}
                        data-testid="dashboard-use-location"
                    >
                        {geoLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <LocateFixed className="h-4 w-4" />}
                        <span className="hidden sm:inline">Use my location</span>
                    </button>
                    <button className="tiq-btn-secondary flex items-center gap-2 mono text-sm" onClick={exportPdf} data-testid={TOPBAR.exportPdf}>
                        <FileDown className="h-4 w-4" />
                        <span>Export PDF</span>
                    </button>
                    <button className="tiq-btn-primary flex items-center gap-2 mono text-sm" onClick={simulateIncident} disabled={busy} data-testid={TOPBAR.simulateIncident}>
                        <PlayCircle className="h-4 w-4" />
                        <span>{busy ? 'Simulating…' : 'Simulate Incident'}</span>
                    </button>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    testId={KPI.congestionIndex}
                    label="Congestion Index"
                    value={kpis.congestion_index}
                    unit="/100"
                    icon={Gauge}
                    tone="danger"
                    index={0}
                    delta={`${kpis.segments_congested}/${kpis.segments_total} segments`}
                />
                <StatCard
                    testId={KPI.avgSpeed}
                    label="Avg Speed"
                    value={kpis.avg_speed_kmph}
                    unit="kmph"
                    icon={Activity}
                    tone="success"
                    index={1}
                    delta="City-wide average"
                />
                <StatCard
                    testId={KPI.incidents}
                    label="Incidents Today"
                    value={incidents}
                    format="int"
                    icon={AlertTriangle}
                    tone="warning"
                    index={2}
                    delta={`${activeAlerts.length} active alerts`}
                />
                <StatCard
                    testId={KPI.routes}
                    label="Routes Optimized"
                    value={routesOptimized}
                    format="int"
                    icon={RouteIcon}
                    tone="primary"
                    index={3}
                    delta="Session count"
                />
            </div>

            {/* Map + Gauge */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
                <motion.div
                    className="lg:col-span-8"
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.35, delay: 0.16 }}
                >
                    <TrafficMap
                        center={currentCity.center}
                        zoom={currentCity.zoom}
                        segments={segments}
                        theme={theme}
                        height={520}
                    />
                </motion.div>

                <motion.div
                    className="lg:col-span-4 tiq-card p-5 flex flex-col"
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.35, delay: 0.18 }}
                >
                    <div className="section-title">Real-time Congestion</div>
                    <ArcGauge value={kpis.congestion_index} label="City Congestion Index" />
                    <div className="tiq-divider my-4" />
                    <div className="section-title">Critical Alerts</div>
                    <div className="flex flex-col gap-2">
                        {criticalHigh.length === 0 && (
                            <div className="text-sm text-[color:var(--tiq-muted)]">No critical alerts.</div>
                        )}
                        {criticalHigh.map((a) => {
                            const s = SEVERITY_STYLE[a.severity] || SEVERITY_STYLE.medium;
                            return (
                                <div key={a.id} className="flex items-start gap-2 py-1">
                                    <span className="h-2 w-2 rounded-full mt-2" style={{ background: s.dot }} />
                                    <div className="flex-1 min-w-0">
                                        <div className="text-sm truncate">{a.title}</div>
                                        <div className="text-xs text-[color:var(--tiq-muted)] truncate mono">
                                            {a.location}
                                        </div>
                                    </div>
                                    <Badge variant="outline" className={`text-[10px] mono ${s.badge}`}>
                                        {a.severity}
                                    </Badge>
                                </div>
                            );
                        })}
                    </div>
                </motion.div>
            </div>
        </div>
    );
}

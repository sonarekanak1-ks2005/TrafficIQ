import { useMemo, useState } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, PlayCircle, Filter } from 'lucide-react';
import { toast } from 'sonner';
import { useTraffic, API } from '@/contexts/TrafficContext';
import { ALERTS as ALERTS_TID, TOPBAR } from '@/constants/testIds';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';

const SEVERITY_STYLE = {
    critical: { badge: 'bg-[rgba(255,77,77,0.14)] text-[#FFB3B3] border-[rgba(255,77,77,0.28)]', dot: '#FF4D4D' },
    high: { badge: 'bg-[rgba(247,201,72,0.14)] text-[#FFE3A3] border-[rgba(247,201,72,0.28)]', dot: '#F7C948' },
    medium: { badge: 'bg-[rgba(0,212,255,0.12)] text-[#BDEFFF] border-[rgba(0,212,255,0.22)]', dot: '#00D4FF' },
    low: { badge: 'bg-[rgba(46,229,157,0.12)] text-[#B9F7DE] border-[rgba(46,229,157,0.22)]', dot: '#2EE59D' },
};

const TYPES = ['all', 'accident', 'roadwork', 'weather', 'congestion', 'event', 'closure'];
const SEVERITIES = ['all', 'critical', 'high', 'medium', 'low'];

export default function Alerts() {
    const { alerts, city, currentCity } = useTraffic();
    const [typeFilter, setTypeFilter] = useState('all');
    const [sevFilter, setSevFilter] = useState('all');
    const [detail, setDetail] = useState(null);
    const [busy, setBusy] = useState(false);

    const filtered = useMemo(() => {
        return (alerts || []).filter((a) => {
            if (typeFilter !== 'all' && a.type !== typeFilter) return false;
            if (sevFilter !== 'all' && a.severity !== sevFilter) return false;
            return true;
        });
    }, [alerts, typeFilter, sevFilter]);

    const simulate = async () => {
        try {
            setBusy(true);
            const r = await axios.post(`${API}/incident/simulate`, { city });
            toast.success(`Incident simulated on ${r.data.alert.location}`);
        } catch (e) {
            toast.error('Failed to simulate incident');
        } finally {
            setBusy(false);
        }
    };

    const formatTime = (iso) => {
        if (!iso) return '';
        const d = new Date(iso);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            <motion.div
                className="lg:col-span-4 tiq-card p-5 flex flex-col gap-3"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
            >
                <div className="flex items-center gap-2">
                    <Bell className="h-4 w-4 text-[color:var(--tiq-primary)]" />
                    <div className="section-title mb-0">Alert Filters</div>
                </div>
                <div>
                    <div className="kpi-label">Type</div>
                    <Select value={typeFilter} onValueChange={setTypeFilter}>
                        <SelectTrigger className="mt-1 bg-transparent border-[color:var(--tiq-border-strong)]" data-testid={ALERTS_TID.filter + '-type'}>
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-[color:var(--tiq-card)] border-[color:var(--tiq-border)] text-[color:var(--tiq-foreground)]">
                            {TYPES.map((t) => (
                                <SelectItem key={t} value={t}>
                                    {t.charAt(0).toUpperCase() + t.slice(1)}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
                <div>
                    <div className="kpi-label">Severity</div>
                    <Select value={sevFilter} onValueChange={setSevFilter}>
                        <SelectTrigger className="mt-1 bg-transparent border-[color:var(--tiq-border-strong)]" data-testid={ALERTS_TID.filter + '-sev'}>
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-[color:var(--tiq-card)] border-[color:var(--tiq-border)] text-[color:var(--tiq-foreground)]">
                            {SEVERITIES.map((s) => (
                                <SelectItem key={s} value={s}>
                                    {s.charAt(0).toUpperCase() + s.slice(1)}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
                <div className="tiq-divider my-2" />
                <button
                    className="tiq-btn-primary flex items-center justify-center gap-2 mono text-sm"
                    onClick={simulate}
                    disabled={busy}
                    data-testid={TOPBAR.simulateIncident + '-alerts'}
                >
                    <PlayCircle className="h-4 w-4" />
                    {busy ? 'Simulating…' : 'Simulate Traffic Incident'}
                </button>
                <div className="text-xs text-[color:var(--tiq-muted)]">
                    Injects a critical incident on a random road for {currentCity.name}. Adjacent segments show cascading impact on the map.
                </div>
            </motion.div>

            <motion.div
                className="lg:col-span-8 tiq-card p-5"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.06 }}
                data-testid={ALERTS_TID.feed}
            >
                <div className="flex items-center justify-between">
                    <div>
                        <div className="section-title mb-0">Live Alerts Feed</div>
                        <div className="text-xs text-[color:var(--tiq-muted)] mt-1 mono">{filtered.length} active</div>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-[color:var(--tiq-muted)]">
                        <Filter className="h-3.5 w-3.5" />
                        <span className="mono">{typeFilter} · {sevFilter}</span>
                    </div>
                </div>

                <div className="mt-4 flex flex-col gap-2">
                    <AnimatePresence initial={false}>
                        {filtered.map((a) => {
                            const s = SEVERITY_STYLE[a.severity] || SEVERITY_STYLE.medium;
                            return (
                                <motion.div
                                    key={a.id}
                                    layout
                                    initial={{ opacity: 0, x: 40 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -20 }}
                                    transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
                                    className="alert-item"
                                    onClick={() => setDetail(a)}
                                    data-testid={ALERTS_TID.item}
                                >
                                    <span className="h-2 w-2 rounded-full mt-2 flex-shrink-0" style={{ background: s.dot }} />
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <div className="text-sm font-semibold">{a.title}</div>
                                            <Badge variant="outline" className={`text-[10px] mono uppercase ${s.badge}`}>
                                                {a.severity}
                                            </Badge>
                                            <Badge variant="outline" className="text-[10px] mono uppercase border-[color:var(--tiq-border-strong)]">
                                                {a.type}
                                            </Badge>
                                            {a.simulated && (
                                                <Badge variant="outline" className="text-[10px] mono border-[color:var(--tiq-primary)]" style={{ color: 'var(--tiq-primary)' }}>
                                                    SIMULATED
                                                </Badge>
                                            )}
                                        </div>
                                        <div className="text-xs text-[color:var(--tiq-muted)] mono mt-1">
                                            {a.location} · {formatTime(a.created_at)}
                                        </div>
                                        <div className="text-xs mt-1 opacity-80">{a.recommended_action}</div>
                                    </div>
                                </motion.div>
                            );
                        })}
                    </AnimatePresence>
                    {filtered.length === 0 && (
                        <div className="text-center py-10 text-[color:var(--tiq-muted)]">No alerts match filters.</div>
                    )}
                </div>
            </motion.div>

            <Sheet open={!!detail} onOpenChange={(o) => !o && setDetail(null)}>
                <SheetContent side="right" className="bg-[color:var(--tiq-card)] border-[color:var(--tiq-border)] text-[color:var(--tiq-foreground)] w-[400px] sm:w-[440px]">
                    {detail && (
                        <>
                            <SheetHeader>
                                <SheetTitle className="flex items-center gap-2">
                                    <span className="h-2 w-2 rounded-full" style={{ background: SEVERITY_STYLE[detail.severity]?.dot }} />
                                    {detail.title}
                                </SheetTitle>
                            </SheetHeader>
                            <div className="mt-4 flex flex-col gap-3">
                                <div>
                                    <div className="kpi-label">Location</div>
                                    <div className="mono text-sm">{detail.location}</div>
                                </div>
                                <div>
                                    <div className="kpi-label">Type / Severity</div>
                                    <div className="mono text-sm uppercase">{detail.type} · {detail.severity}</div>
                                </div>
                                <div>
                                    <div className="kpi-label">Created</div>
                                    <div className="mono text-sm">{new Date(detail.created_at).toLocaleString()}</div>
                                </div>
                                <div>
                                    <div className="kpi-label">Expires</div>
                                    <div className="mono text-sm">{new Date(detail.expires_at).toLocaleString()}</div>
                                </div>
                                <div className="tiq-divider" />
                                <div>
                                    <div className="kpi-label">Description</div>
                                    <div className="text-sm mt-1">{detail.description}</div>
                                </div>
                                <div>
                                    <div className="kpi-label">Recommended Action</div>
                                    <div className="text-sm mt-1">{detail.recommended_action}</div>
                                </div>
                            </div>
                        </>
                    )}
                </SheetContent>
            </Sheet>
        </div>
    );
}

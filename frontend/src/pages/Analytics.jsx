import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp } from 'lucide-react';
import {
    ResponsiveContainer,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ScatterChart,
    Scatter,
    ZAxis,
    Cell,
} from 'recharts';
import { useTraffic, API } from '@/contexts/TrafficContext';
import { ANALYTICS } from '@/constants/testIds';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const heatColor = (v) => {
    if (v >= 66) return `rgba(255, 77, 77, ${0.2 + (v - 66) / 100})`;
    if (v >= 33) return `rgba(247, 201, 72, ${0.2 + (v - 33) / 100})`;
    return `rgba(46, 229, 157, ${0.14 + v / 200})`;
};

const barColor = (v) => (v >= 66 ? '#FF4D4D' : v >= 33 ? '#F7C948' : '#2EE59D');

export default function Analytics() {
    const { city, currentCity } = useTraffic();
    const [data, setData] = useState(null);

    useEffect(() => {
        (async () => {
            try {
                const r = await axios.get(`${API}/analytics/historical?city=${city}`);
                setData(r.data);
            } catch (e) {
                console.error(e);
            }
        })();
    }, [city]);

    const heatmapCells = useMemo(() => {
        if (!data) return [];
        return data.heatmap;
    }, [data]);

    return (
        <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
                <div>
                    <div className="section-title">Analytics · {currentCity.name}</div>
                    <div className="text-2xl font-semibold flex items-center gap-2">
                        <BarChart3 className="h-6 w-6 text-[color:var(--tiq-primary)]" />
                        Traffic Insights
                    </div>
                    <div className="text-sm text-[color:var(--tiq-muted)] mt-1">Historical patterns, weather impact & top congested roads.</div>
                </div>
            </div>

            {!data && (
                <div className="tiq-card p-10 text-center text-[color:var(--tiq-muted)]">Loading analytics…</div>
            )}

            {data && (
                <>
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
                        <motion.div
                            className="lg:col-span-8 tiq-card p-5"
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3 }}
                        >
                            <div className="flex items-center justify-between">
                                <div className="section-title mb-0">Hour of Day · Avg Congestion</div>
                                <div className="text-xs text-[color:var(--tiq-muted)] mono">weekday baseline</div>
                            </div>
                            <div className="mt-3" data-testid={ANALYTICS.hourChart}>
                                <ResponsiveContainer width="100%" height={280}>
                                    <BarChart data={data.hour_pattern} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                        <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                                        <XAxis dataKey="hour" stroke="rgba(237,239,242,0.55)" tickFormatter={(h) => `${String(h).padStart(2, '0')}h`} tick={{ fontFamily: 'JetBrains Mono', fontSize: 10 }} />
                                        <YAxis stroke="rgba(237,239,242,0.55)" domain={[0, 100]} tick={{ fontFamily: 'JetBrains Mono', fontSize: 10 }} />
                                        <Tooltip />
                                        <Bar dataKey="congestion" radius={[6, 6, 0, 0]}>
                                            {data.hour_pattern.map((h) => (
                                                <Cell key={h.hour} fill={barColor(h.congestion)} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </motion.div>

                        <motion.div
                            className="lg:col-span-4 tiq-card p-5"
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3, delay: 0.06 }}
                            data-testid={ANALYTICS.topRoads}
                        >
                            <div className="section-title">Top 5 Congested Roads</div>
                            <div className="flex flex-col gap-2 mt-2">
                                {data.top_roads.map((r, i) => (
                                    <div key={r.id} className="flex items-center gap-3">
                                        <div className="w-6 mono text-[color:var(--tiq-muted)]">#{i + 1}</div>
                                        <div className="flex-1 min-w-0">
                                            <div className="text-sm truncate">{r.name}</div>
                                            <div className="w-full h-1.5 rounded-full bg-white/5 mt-1 overflow-hidden">
                                                <div
                                                    className="h-full rounded-full"
                                                    style={{ width: `${r.avg_congestion}%`, background: barColor(r.avg_congestion) }}
                                                />
                                            </div>
                                        </div>
                                        <div className="mono text-sm">{r.avg_congestion.toFixed(1)}%</div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    </div>

                    <motion.div
                        className="tiq-card p-5"
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3, delay: 0.1 }}
                        data-testid={ANALYTICS.heatmap}
                    >
                        <div className="flex items-center justify-between flex-wrap gap-2">
                            <div className="section-title mb-0">Weekly Heatmap · Day × Hour</div>
                            <div className="flex items-center gap-3 text-xs mono text-[color:var(--tiq-muted)]">
                                <span className="flex items-center gap-1"><span className="legend-dot" style={{ background: '#2EE59D' }} />Low</span>
                                <span className="flex items-center gap-1"><span className="legend-dot" style={{ background: '#F7C948' }} />Mid</span>
                                <span className="flex items-center gap-1"><span className="legend-dot" style={{ background: '#FF4D4D' }} />High</span>
                            </div>
                        </div>
                        <div className="mt-4 overflow-x-auto">
                            <div style={{ minWidth: 680 }}>
                                {/* Hour header */}
                                <div className="grid grid-cols-[60px_repeat(24,_minmax(24px,1fr))] gap-1 mb-1 pl-1">
                                    <div></div>
                                    {Array.from({ length: 24 }).map((_, h) => (
                                        <div key={h} className="text-[10px] text-[color:var(--tiq-muted)] mono text-center">
                                            {String(h).padStart(2, '0')}
                                        </div>
                                    ))}
                                </div>
                                {DAYS.map((day, dIdx) => (
                                    <div key={day} className="grid grid-cols-[60px_repeat(24,_minmax(24px,1fr))] gap-1 mb-1">
                                        <div className="text-xs mono text-[color:var(--tiq-muted)] flex items-center pl-1">{day}</div>
                                        {Array.from({ length: 24 }).map((_, h) => {
                                            const cell = heatmapCells.find((c) => c.day_idx === dIdx && c.hour === h) || { congestion: 0 };
                                            return (
                                                <div
                                                    key={h}
                                                    className="tiq-heatmap-cell h-6"
                                                    style={{ background: heatColor(cell.congestion) }}
                                                    title={`${day} ${String(h).padStart(2, '0')}:00 — ${cell.congestion.toFixed(1)}%`}
                                                />
                                            );
                                        })}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </motion.div>

                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
                        <motion.div
                            className="lg:col-span-7 tiq-card p-5"
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3, delay: 0.14 }}
                            data-testid={ANALYTICS.scatter}
                        >
                            <div className="section-title">Weather Intensity vs Congestion</div>
                            <ResponsiveContainer width="100%" height={280}>
                                <ScatterChart>
                                    <CartesianGrid stroke="rgba(255,255,255,0.06)" />
                                    <XAxis type="number" dataKey="intensity" name="Weather" stroke="rgba(237,239,242,0.55)" tick={{ fontFamily: 'JetBrains Mono', fontSize: 10 }} domain={[0.9, 1.5]} />
                                    <YAxis type="number" dataKey="congestion" name="Congestion" stroke="rgba(237,239,242,0.55)" tick={{ fontFamily: 'JetBrains Mono', fontSize: 10 }} domain={[0, 100]} />
                                    <ZAxis range={[60, 60]} />
                                    <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                                    <Scatter data={data.weather_scatter} fill="#00D4FF" opacity={0.85} />
                                </ScatterChart>
                            </ResponsiveContainer>
                        </motion.div>

                        <motion.div
                            className="lg:col-span-5 tiq-card p-5"
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3, delay: 0.16 }}
                            data-testid={ANALYTICS.holidayChart}
                        >
                            <div className="section-title flex items-center gap-2">
                                <TrendingUp className="h-3.5 w-3.5" /> Holiday Impact
                            </div>
                            <ResponsiveContainer width="100%" height={280}>
                                <BarChart data={data.holiday_impact} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                    <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                                    <XAxis dataKey="type" stroke="rgba(237,239,242,0.55)" tick={{ fontFamily: 'JetBrains Mono', fontSize: 10 }} />
                                    <YAxis stroke="rgba(237,239,242,0.55)" domain={[0, 100]} tick={{ fontFamily: 'JetBrains Mono', fontSize: 10 }} />
                                    <Tooltip />
                                    <Bar dataKey="congestion" radius={[6, 6, 0, 0]}>
                                        {data.holiday_impact.map((h) => (
                                            <Cell key={h.type} fill={barColor(h.congestion)} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </motion.div>
                    </div>
                </>
            )}
        </div>
    );
}

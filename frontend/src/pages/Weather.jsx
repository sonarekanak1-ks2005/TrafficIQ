import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import {
    Sun, Cloud, CloudRain, CloudLightning, CloudFog, Wind, Droplets, Eye,
    Sunrise, Sunset, Gauge, Thermometer, TrendingUp
} from 'lucide-react';
import {
    ResponsiveContainer, ComposedChart, Line, Area, Bar, XAxis, YAxis,
    CartesianGrid, Tooltip, Cell
} from 'recharts';
import { useTraffic, API } from '@/contexts/TrafficContext';

const ICONS = {
    'sun': Sun,
    'cloud': Cloud,
    'cloud-rain': CloudRain,
    'cloud-lightning': CloudLightning,
    'cloud-fog': CloudFog,
};

const TONE_COLORS = {
    success: '#2EE59D',
    primary: '#00D4FF',
    warning: '#F7C948',
    danger: '#FF4D4D',
};

const impactColor = (state) => {
    if (state === 'heavy_rain') return TONE_COLORS.danger;
    if (state === 'rain' || state === 'fog') return TONE_COLORS.warning;
    if (state === 'cloudy') return TONE_COLORS.primary;
    return TONE_COLORS.success;
};

const formatTime = (iso) => {
    try {
        const d = new Date(iso);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (_e) {
        return '';
    }
};

export default function Weather() {
    const { city, currentCity } = useTraffic();
    const [current, setCurrent] = useState(null);
    const [forecast, setForecast] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            setLoading(true);
            try {
                const [c, f] = await Promise.all([
                    axios.get(`${API}/weather/current?city=${city}`),
                    axios.get(`${API}/weather/forecast?city=${city}`),
                ]);
                if (cancelled) return;
                setCurrent(c.data);
                setForecast(f.data);
            } catch (_e) {
                // handled by empty state
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [city]);

    const HourlyIcon = ({ icon, className }) => {
        const Cmp = ICONS[icon] || Sun;
        return <Cmp className={className} />;
    };

    const chartData = useMemo(() => {
        if (!forecast) return [];
        return forecast.hourly.map((h, i) => ({
            i,
            hour: h.hour,
            temp: h.temp_c,
            pop: h.pop,
            state: h.state,
            impact: (h.traffic_multiplier - 1) * 100,
        }));
    }, [forecast]);

    const CurrentIcon = current ? ICONS[current.icon] || Sun : Sun;

    return (
        <div className="flex flex-col gap-4">
            {loading && (
                <div className="tiq-card p-10 text-center text-[color:var(--tiq-muted)]">Loading weather…</div>
            )}

            {current && !loading && (
                <>
                    <motion.div
                        className="tiq-card p-6"
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                        data-testid="weather-current"
                    >
                        <div className="flex items-start justify-between gap-4 flex-wrap">
                            <div className="flex items-center gap-5">
                                <div
                                    className="h-24 w-24 rounded-2xl grid place-items-center"
                                    style={{ background: `${impactColor(current.state)}22`, color: impactColor(current.state) }}
                                >
                                    <CurrentIcon className="h-14 w-14" />
                                </div>
                                <div>
                                    <div className="section-title">{currentCity.name} · Now</div>
                                    <div className="flex items-baseline gap-2 mt-1">
                                        <span className="kpi-value text-5xl leading-none">{current.temp_c.toFixed(1)}°</span>
                                        <span className="mono text-lg text-[color:var(--tiq-muted)]">C</span>
                                    </div>
                                    <div className="text-sm text-[color:var(--tiq-muted)] mt-1">
                                        Feels like <span className="mono">{current.feels_like_c.toFixed(1)}°C</span> · {current.label}
                                    </div>
                                </div>
                            </div>
                            <div className="tiq-card-2 p-4 min-w-[260px]">
                                <div className="kpi-label">Traffic Impact</div>
                                <div
                                    className="mt-2 text-2xl font-semibold"
                                    style={{ color: impactColor(current.state) }}
                                >
                                    {current.traffic_impact.label}
                                </div>
                                <div className="text-xs text-[color:var(--tiq-muted)] mono mt-1">
                                    Congestion multiplier: {(current.traffic_impact.multiplier).toFixed(2)}x
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mt-5">
                            {[
                                { icon: Droplets, label: 'Humidity', value: `${current.humidity}%` },
                                { icon: Wind, label: 'Wind', value: `${current.wind_kmph} kmph` },
                                { icon: Eye, label: 'Visibility', value: `${current.visibility_km} km` },
                                { icon: Sun, label: 'UV Index', value: `${current.uv_index}` },
                                { icon: Gauge, label: 'Pressure', value: `${current.pressure_hpa} hPa` },
                                { icon: Thermometer, label: 'Feels Like', value: `${current.feels_like_c.toFixed(1)}°` },
                            ].map((m) => {
                                const Icon = m.icon;
                                return (
                                    <div key={m.label} className="tiq-card-2 p-3">
                                        <div className="flex items-center gap-2 text-[color:var(--tiq-muted)]">
                                            <Icon className="h-3.5 w-3.5" />
                                            <span className="kpi-label mb-0">{m.label}</span>
                                        </div>
                                        <div className="mono text-xl font-semibold mt-1">{m.value}</div>
                                    </div>
                                );
                            })}
                        </div>

                        <div className="grid grid-cols-2 gap-3 mt-3">
                            <div className="tiq-card-2 p-3 flex items-center gap-3">
                                <div className="h-9 w-9 rounded-lg grid place-items-center bg-[rgba(247,201,72,0.14)] text-[#F7C948]">
                                    <Sunrise className="h-4 w-4" />
                                </div>
                                <div>
                                    <div className="kpi-label">Sunrise</div>
                                    <div className="mono text-lg">{current.sunrise_local || formatTime(current.sunrise)}</div>
                                </div>
                            </div>
                            <div className="tiq-card-2 p-3 flex items-center gap-3">
                                <div className="h-9 w-9 rounded-lg grid place-items-center bg-[rgba(255,77,77,0.14)] text-[#FF4D4D]">
                                    <Sunset className="h-4 w-4" />
                                </div>
                                <div>
                                    <div className="kpi-label">Sunset</div>
                                    <div className="mono text-lg">{current.sunset_local || formatTime(current.sunset)}</div>
                                </div>
                            </div>
                        </div>
                    </motion.div>

                    {/* Hourly forecast */}
                    <motion.div
                        className="tiq-card p-5"
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3, delay: 0.06 }}
                        data-testid="weather-hourly"
                    >
                        <div className="flex items-center justify-between flex-wrap gap-2">
                            <div className="section-title mb-0">Next 24 Hours</div>
                            <div className="text-xs text-[color:var(--tiq-muted)] mono">temperature · precipitation · traffic impact</div>
                        </div>
                        <div className="mt-4 overflow-x-auto">
                            <div className="flex gap-2 pb-1" style={{ minWidth: 900 }}>
                                {forecast.hourly.map((h) => {
                                    const c = impactColor(h.state);
                                    return (
                                        <div
                                            key={h.t}
                                            className="tiq-card-2 min-w-[70px] py-3 px-2 text-center flex-shrink-0"
                                        >
                                            <div className="text-[11px] mono text-[color:var(--tiq-muted)]">
                                                {String(h.hour).padStart(2, '0')}:00
                                            </div>
                                            <div className="my-2 grid place-items-center">
                                                <HourlyIcon icon={h.icon} className="h-5 w-5" />
                                            </div>
                                            <div className="mono text-lg font-semibold">{h.temp_c.toFixed(0)}°</div>
                                            <div
                                                className="text-[10px] mono mt-1"
                                                style={{ color: c }}
                                            >
                                                {h.pop}% · {h.label}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                        <div className="mt-6">
                            <ResponsiveContainer width="100%" height={220}>
                                <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="tempGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="#00D4FF" stopOpacity={0.35} />
                                            <stop offset="100%" stopColor="#00D4FF" stopOpacity={0.03} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                                    <XAxis
                                        dataKey="hour"
                                        stroke="rgba(237,239,242,0.55)"
                                        tickFormatter={(h) => `${String(h).padStart(2, '0')}h`}
                                        tick={{ fontFamily: 'JetBrains Mono', fontSize: 10 }}
                                    />
                                    <YAxis yAxisId="temp" stroke="rgba(237,239,242,0.55)" tick={{ fontFamily: 'JetBrains Mono', fontSize: 10 }} />
                                    <YAxis yAxisId="pop" orientation="right" stroke="rgba(237,239,242,0.55)" tick={{ fontFamily: 'JetBrains Mono', fontSize: 10 }} domain={[0, 100]} />
                                    <Tooltip />
                                    <Area yAxisId="temp" type="monotone" dataKey="temp" stroke="#00D4FF" fill="url(#tempGrad)" strokeWidth={2} />
                                    <Bar yAxisId="pop" dataKey="pop" radius={[3, 3, 0, 0]} opacity={0.7}>
                                        {chartData.map((d, i) => (
                                            <Cell key={i} fill={impactColor(d.state)} />
                                        ))}
                                    </Bar>
                                </ComposedChart>
                            </ResponsiveContainer>
                        </div>
                    </motion.div>

                    {/* Weekly */}
                    {forecast?.weekly && (
                        <motion.div
                            className="tiq-card p-5"
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3, delay: 0.1 }}
                            data-testid="weather-weekly"
                        >
                            <div className="section-title">7-Day Outlook</div>
                            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 mt-3">
                                {forecast.weekly.map((d) => {
                                    const c = impactColor(d.state);
                                    return (
                                        <div key={d.date} className="tiq-card-2 p-3 text-center">
                                            <div className="text-xs mono text-[color:var(--tiq-muted)] uppercase">{d.day_label}</div>
                                            <div className="my-2 grid place-items-center">
                                                <HourlyIcon icon={d.icon} className="h-6 w-6" />
                                            </div>
                                            <div className="mono text-sm font-semibold">{d.high_c.toFixed(0)}° / <span className="opacity-60">{d.low_c.toFixed(0)}°</span></div>
                                            <div className="text-[11px] mono mt-1" style={{ color: c }}>
                                                {d.label}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </motion.div>
                    )}

                    {/* Traffic impact banner */}
                    <motion.div
                        className="tiq-card p-5 flex items-center gap-4 flex-wrap"
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3, delay: 0.14 }}
                    >
                        <div
                            className="h-12 w-12 rounded-xl grid place-items-center"
                            style={{ background: `${impactColor(current.state)}22`, color: impactColor(current.state) }}
                        >
                            <TrendingUp className="h-6 w-6" />
                        </div>
                        <div className="flex-1 min-w-[200px]">
                            <div className="section-title mb-0">Traffic Advisory</div>
                            <div className="mt-1 text-sm">
                                {current.state === 'clear' && 'Ideal driving conditions. Expected traffic follows normal daily patterns.'}
                                {current.state === 'cloudy' && 'Overcast but dry. Minimal impact on commute times.'}
                                {current.state === 'rain' && 'Wet roads may slow traffic by 15-25%. Allow extra time for your commute.'}
                                {current.state === 'heavy_rain' && 'Severe congestion expected. Consider delaying travel or using alternate transport.'}
                                {current.state === 'fog' && 'Low visibility. Reduce speed by 20 kmph and use headlights. Higher accident risk.'}
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </div>
    );
}

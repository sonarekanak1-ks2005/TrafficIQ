import { useState, useMemo, useCallback } from 'react';
import { useTraffic } from '@/contexts/TrafficContext';
import { Sun, Moon, Menu, LocateFixed, Search, ChevronDown, MapPin, Check, Loader2 } from 'lucide-react';
import { TOPBAR } from '@/constants/testIds';
import { motion } from 'framer-motion';
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { NavLink, useLocation } from 'react-router-dom';
import { Activity, LineChart, Route as RouteIcon, BarChart3, Bell, CloudSun } from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { toast } from 'sonner';
import { useCurrentLocation } from '@/hooks/useCurrentLocation';

const pageTitles = {
    '/': { title: 'Dashboard', subtitle: 'Live traffic operations command center' },
    '/prediction': { title: 'Prediction Panel', subtitle: 'LSTM-based congestion forecasting' },
    '/routes': { title: 'Route Optimization', subtitle: 'Compare and select optimal paths' },
    '/weather': { title: 'Weather', subtitle: 'Conditions and traffic impact forecast' },
    '/analytics': { title: 'Analytics', subtitle: 'Historical patterns and insights' },
    '/alerts': { title: 'Alerts', subtitle: 'Real-time incident feed' },
};

const mobileLinks = [
    { to: '/', label: 'Dashboard', icon: Activity, end: true },
    { to: '/prediction', label: 'Prediction', icon: LineChart },
    { to: '/routes', label: 'Routes', icon: RouteIcon },
    { to: '/weather', label: 'Weather', icon: CloudSun },
    { to: '/analytics', label: 'Analytics', icon: BarChart3 },
    { to: '/alerts', label: 'Alerts', icon: Bell },
];

const CitySearchBox = () => {
    const { cities, city, setCity, currentCity } = useTraffic();
    const [open, setOpen] = useState(false);
    const [q, setQ] = useState('');
    const { detect: detectLocation, loading: geoLoading } = useCurrentLocation();

    const filtered = useMemo(() => {
        if (!q.trim()) return cities;
        const query = q.trim().toLowerCase();
        return cities.filter(
            (c) =>
                c.name.toLowerCase().includes(query) ||
                (c.country || '').toLowerCase().includes(query) ||
                c.key.toLowerCase().includes(query)
        );
    }, [cities, q]);

    const handleUseLocation = useCallback(async () => {
        const res = await detectLocation();
        if (!res) return;
        if (res.city && res.city !== city) {
            setCity(res.city);
            toast.success(`Switched to nearest city: ${res.city.toUpperCase()}`);
        } else {
            toast.info(`You're already in ${res.city.toUpperCase()}`);
        }
        setOpen(false);
    }, [detectLocation, city, setCity]);

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <button
                    className="city-search-trigger"
                    data-testid={TOPBAR.citySelector}
                    aria-label="Select city"
                >
                    <MapPin className="h-3.5 w-3.5 opacity-70" />
                    <span className="truncate">{currentCity?.name || 'Select city'}</span>
                    {currentCity?.country && (
                        <span className="mono text-[10px] text-[color:var(--tiq-muted)] hidden md:inline">{currentCity.country}</span>
                    )}
                    <ChevronDown className="h-3.5 w-3.5 opacity-70 ml-auto" />
                </button>
            </PopoverTrigger>
            <PopoverContent
                align="end"
                sideOffset={8}
                className="w-[300px] p-0 bg-[color:var(--tiq-card)] border-[color:var(--tiq-border)] text-[color:var(--tiq-foreground)]"
            >
                <div className="p-2 border-b border-[color:var(--tiq-border)]">
                    <div className="relative">
                        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[color:var(--tiq-muted)]" />
                        <input
                            data-testid="city-search-input"
                            autoFocus
                            value={q}
                            onChange={(e) => setQ(e.target.value)}
                            placeholder="Search cities…"
                            className="w-full pl-8 pr-2 py-2 bg-transparent outline-none text-sm border border-[color:var(--tiq-border)] rounded-md focus:border-[color:var(--tiq-primary)]"
                        />
                    </div>
                </div>
                <button
                    onClick={handleUseLocation}
                    disabled={geoLoading}
                    data-testid="city-search-use-location"
                    className="w-full flex items-center gap-2 px-3 py-2.5 text-sm hover:bg-white/[0.04] border-b border-[color:var(--tiq-border)] disabled:opacity-60"
                >
                    {geoLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin text-[color:var(--tiq-primary)]" />
                    ) : (
                        <LocateFixed className="h-4 w-4 text-[color:var(--tiq-primary)]" />
                    )}
                    <span className="font-medium">Use my current location</span>
                </button>
                <div className="max-h-[300px] overflow-y-auto py-1">
                    {filtered.length === 0 && (
                        <div className="px-3 py-4 text-sm text-center text-[color:var(--tiq-muted)]">
                            No cities match “{q}”
                        </div>
                    )}
                    {filtered.map((c) => {
                        const selected = c.key === city;
                        return (
                            <button
                                key={c.key}
                                data-testid={`city-option-${c.key}`}
                                onClick={() => {
                                    setCity(c.key);
                                    setOpen(false);
                                    setQ('');
                                }}
                                className={`w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-white/[0.04] ${selected ? 'bg-[rgba(0,212,255,0.08)]' : ''}`}
                            >
                                <MapPin className="h-3.5 w-3.5 opacity-60" />
                                <span className="flex-1 text-left truncate">{c.name}</span>
                                <span className="mono text-[10px] text-[color:var(--tiq-muted)]">{c.country}</span>
                                {selected && <Check className="h-3.5 w-3.5 text-[color:var(--tiq-primary)]" />}
                            </button>
                        );
                    })}
                </div>
            </PopoverContent>
        </Popover>
    );
};

export const TopBar = () => {
    const { wsStatus, theme, setTheme } = useTraffic();
    const location = useLocation();
    const meta = pageTitles[location.pathname] || { title: 'TrafficIQ', subtitle: '' };

    const wsLabel = wsStatus === 'live' ? 'LIVE' : wsStatus === 'connecting' ? 'CONNECTING' : 'RECONNECTING';

    return (
        <div className="topbar">
            <div className="topbar-left">
                {/* Mobile menu */}
                <div className="md:hidden">
                    <Sheet>
                        <SheetTrigger asChild>
                            <button className="tiq-btn-secondary" aria-label="Open menu">
                                <Menu className="h-4 w-4" />
                            </button>
                        </SheetTrigger>
                        <SheetContent side="left" className="bg-[color:var(--tiq-card)] border-[color:var(--tiq-border)] text-[color:var(--tiq-foreground)] w-[280px]">
                            <SheetHeader>
                                <SheetTitle className="flex items-center gap-2">
                                    <div className="brand-logo mono">T</div>
                                    <span>TrafficIQ</span>
                                </SheetTitle>
                            </SheetHeader>
                            <nav className="flex flex-col gap-1 mt-4">
                                {mobileLinks.map((l) => {
                                    const active = l.end ? location.pathname === l.to : location.pathname.startsWith(l.to);
                                    const Icon = l.icon;
                                    return (
                                        <NavLink key={l.to} to={l.to} end={l.end} className={`nav-item ${active ? 'active' : ''}`}>
                                            <Icon className="h-4 w-4" />
                                            <span>{l.label}</span>
                                        </NavLink>
                                    );
                                })}
                            </nav>
                        </SheetContent>
                    </Sheet>
                </div>

                <div>
                    <div className="page-title">
                        <motion.span initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
                            {meta.title}
                        </motion.span>
                    </div>
                    <div className="page-subtitle hidden md:block">{meta.subtitle}</div>
                </div>
            </div>

            <div className="topbar-right">
                <CitySearchBox />

                <div
                    className="tiq-chip hidden sm:inline-flex"
                    data-testid={TOPBAR.liveStatus}
                    title={`WebSocket: ${wsStatus}`}
                >
                    <span className={`status-dot ${wsStatus === 'live' ? '' : 'off'}`} />
                    <span className="mono">{wsLabel}</span>
                </div>

                <div className="tiq-chip" role="group" aria-label="Theme">
                    <Sun className="h-3.5 w-3.5 opacity-70" />
                    <Switch
                        checked={theme === 'dark'}
                        onCheckedChange={(v) => setTheme(v ? 'dark' : 'light')}
                        data-testid={TOPBAR.themeToggle}
                        aria-label="Toggle theme"
                    />
                    <Moon className="h-3.5 w-3.5 opacity-70" />
                </div>
            </div>
        </div>
    );
};

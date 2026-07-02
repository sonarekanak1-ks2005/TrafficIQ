import { NavLink, useLocation } from 'react-router-dom';
import { Activity, LineChart, Route as RouteIcon, BarChart3, Bell, CloudSun } from 'lucide-react';
import { NAV } from '@/constants/testIds';

const links = [
    { to: '/', label: 'Dashboard', icon: Activity, id: NAV.dashboard, end: true },
    { to: '/prediction', label: 'Prediction', icon: LineChart, id: NAV.prediction },
    { to: '/routes', label: 'Routes', icon: RouteIcon, id: NAV.routes },
    { to: '/weather', label: 'Weather', icon: CloudSun, id: 'nav-weather' },
    { to: '/analytics', label: 'Analytics', icon: BarChart3, id: NAV.analytics },
    { to: '/alerts', label: 'Alerts', icon: Bell, id: NAV.alerts },
];

export const Sidebar = () => {
    const location = useLocation();
    return (
        <aside className="sidebar">
            <div className="brand">
                <div className="brand-logo mono">T</div>
                <div>
                    <div className="brand-title">TrafficIQ</div>
                    <div className="brand-subtitle">Ops Center</div>
                </div>
            </div>

            <nav className="flex flex-col gap-1">
                {links.map((l) => {
                    const active = l.end ? location.pathname === l.to : location.pathname.startsWith(l.to);
                    const Icon = l.icon;
                    return (
                        <NavLink
                            key={l.to}
                            to={l.to}
                            end={l.end}
                            data-testid={l.id}
                            className={`nav-item ${active ? 'active' : ''}`}
                        >
                            <Icon className="h-4 w-4" />
                            <span>{l.label}</span>
                        </NavLink>
                    );
                })}
            </nav>
        </aside>
    );
};

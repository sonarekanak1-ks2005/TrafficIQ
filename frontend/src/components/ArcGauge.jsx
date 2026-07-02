import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

export const ArcGauge = ({ value = 0, max = 100, label = 'Congestion Index', size = 220 }) => {
    const [display, setDisplay] = useState(0);

    useEffect(() => {
        const target = Math.max(0, Math.min(max, value));
        const start = performance.now();
        const from = display;
        let raf;
        const step = (now) => {
            const t = Math.min(1, (now - start) / 700);
            const eased = 1 - Math.pow(1 - t, 3);
            setDisplay(from + (target - from) * eased);
            if (t < 1) raf = requestAnimationFrame(step);
        };
        raf = requestAnimationFrame(step);
        return () => raf && cancelAnimationFrame(raf);
        // display intentionally omitted to avoid re-triggering animation while it's running
    }, [value, max]);

    const pct = display / max;
    const startAngle = -220;
    const endAngle = 40;
    const totalArc = endAngle - startAngle;
    const currentAngle = startAngle + totalArc * pct;

    const cx = size / 2;
    const cy = size / 2 + 10;
    const r = size / 2 - 20;

    const polar = (angle) => {
        const rad = (angle * Math.PI) / 180;
        return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
    };

    const arcPath = (a1, a2) => {
        const p1 = polar(a1);
        const p2 = polar(a2);
        const largeArc = a2 - a1 > 180 ? 1 : 0;
        return `M ${p1.x} ${p1.y} A ${r} ${r} 0 ${largeArc} 1 ${p2.x} ${p2.y}`;
    };

    let color = '#2EE59D';
    if (display >= 66) color = '#FF4D4D';
    else if (display >= 33) color = '#F7C948';

    return (
        <div className="gauge-shell">
            <svg width={size} height={size * 0.72} viewBox={`0 0 ${size} ${size * 0.72}`}>
                {/* Track */}
                <path
                    d={arcPath(startAngle, endAngle)}
                    stroke="rgba(255,255,255,0.06)"
                    strokeWidth="14"
                    fill="none"
                    strokeLinecap="round"
                />
                {/* Progress */}
                <motion.path
                    d={arcPath(startAngle, currentAngle)}
                    stroke={color}
                    strokeWidth="14"
                    fill="none"
                    strokeLinecap="round"
                    initial={false}
                    animate={{ opacity: 1 }}
                    style={{ filter: `drop-shadow(0 0 12px ${color}80)` }}
                />
                {/* Ticks */}
                {Array.from({ length: 11 }).map((_, i) => {
                    const a = startAngle + (totalArc * i) / 10;
                    const p1 = polar(a);
                    const rad = (a * Math.PI) / 180;
                    const r2 = r - 22;
                    const p2 = { x: cx + r2 * Math.cos(rad), y: cy + r2 * Math.sin(rad) };
                    return (
                        <line
                            key={i}
                            x1={p1.x}
                            y1={p1.y}
                            x2={p2.x}
                            y2={p2.y}
                            stroke="rgba(255,255,255,0.12)"
                            strokeWidth={i % 5 === 0 ? 2 : 1}
                        />
                    );
                })}
            </svg>
            <div className="text-center -mt-8">
                <div className="kpi-value" style={{ color }}>
                    {display.toFixed(1)}
                </div>
                <div className="kpi-label mt-1">{label}</div>
            </div>
        </div>
    );
};

import { motion } from 'framer-motion';
import { useCountUp } from '@/hooks/useCountUp';

export const StatCard = ({ label, value, unit, delta, icon: Icon, format = 'number', tone = 'primary', testId, index = 0 }) => {
    const numeric = typeof value === 'number' ? value : parseFloat(value) || 0;
    const animated = useCountUp(numeric);
    const displayed = format === 'int' ? Math.round(animated) : animated.toFixed(1);

    const toneStyles = {
        primary: 'rgba(0, 212, 255, 0.14)',
        success: 'rgba(46, 229, 157, 0.14)',
        warning: 'rgba(247, 201, 72, 0.14)',
        danger: 'rgba(255, 77, 77, 0.14)',
    };

    return (
        <motion.div
            data-testid={testId}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.04 * index, ease: [0.22, 1, 0.36, 1] }}
            className="tiq-card p-4 relative overflow-hidden tiq-hover"
        >
            <div
                className="absolute inset-x-0 top-0 h-[1px]"
                style={{ background: `linear-gradient(90deg, transparent, ${toneStyles[tone]}, transparent)` }}
            />
            <div className="flex items-start justify-between gap-3">
                <div className="kpi-label">{label}</div>
                {Icon && (
                    <div
                        className="h-8 w-8 rounded-lg grid place-items-center"
                        style={{ background: toneStyles[tone], color: 'var(--tiq-primary)' }}
                    >
                        <Icon className="h-4 w-4" />
                    </div>
                )}
            </div>
            <div className="mt-3 flex items-baseline gap-2">
                <span className="kpi-value">{displayed}</span>
                {unit && <span className="mono text-sm text-[color:var(--tiq-muted)]">{unit}</span>}
            </div>
            {delta !== undefined && (
                <div className="mt-3 text-xs mono text-[color:var(--tiq-muted)]">{delta}</div>
            )}
        </motion.div>
    );
};

import { useEffect, useState, useRef } from 'react';

// Animate a numeric value from prev to next.
export const useCountUp = (target, duration = 900) => {
    const [value, setValue] = useState(target || 0);
    const rafRef = useRef();
    const prevRef = useRef(target || 0);

    useEffect(() => {
        if (target === undefined || target === null || Number.isNaN(target)) return;
        const start = performance.now();
        const from = prevRef.current;
        const to = target;
        const step = (now) => {
            const t = Math.min(1, (now - start) / duration);
            const eased = 1 - Math.pow(1 - t, 3);
            setValue(from + (to - from) * eased);
            if (t < 1) {
                rafRef.current = requestAnimationFrame(step);
            } else {
                prevRef.current = to;
            }
        };
        rafRef.current = requestAnimationFrame(step);
        return () => {
            if (rafRef.current) cancelAnimationFrame(rafRef.current);
        };
    }, [target, duration]);

    return value;
};

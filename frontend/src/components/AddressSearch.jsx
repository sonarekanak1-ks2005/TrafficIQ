import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Search, Loader2, MapPin, X, Route as RouteIcon } from 'lucide-react';
import { API } from '@/contexts/TrafficContext';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';

/**
 * Unified location input: free-text typing + local road suggestions + Nominatim address search.
 * Single input bar that shows a dropdown with two sections:
 *  1) Local city roads matching what you typed (fast, from current snapshot)
 *  2) Nominatim address results (worldwide, debounced)
 *
 * Props:
 *  - value: current text
 *  - onChange: (nextText) => void   (raw text updates while typing)
 *  - onPick: (result) => void       when a Nominatim/address item is picked -> {display_name, lat, lng, city}
 *  - onPickRoad: (roadName) => void when a local road is picked
 *  - roadOptions: string[]           local road names to suggest
 *  - city: current city key (biases Nominatim search)
 *  - placeholder, testId, className
 */
export const AddressSearch = ({
    value = '',
    onChange,
    onPick,
    onPickRoad,
    roadOptions = [],
    city,
    placeholder = 'Type a road, address, or place…',
    className = '',
    testId = 'address-search',
}) => {
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [nominatimResults, setNominatimResults] = useState([]);
    const debounceRef = useRef(null);
    const containerRef = useRef(null);

    // Local road filter (instant)
    const roadMatches = value.trim().length === 0
        ? roadOptions.slice(0, 5)
        : roadOptions
            .filter((r) => r.toLowerCase().includes(value.trim().toLowerCase()))
            .slice(0, 6);

    // Debounced Nominatim search
    useEffect(() => {
        if (debounceRef.current) clearTimeout(debounceRef.current);
        if (!value || value.trim().length < 3) {
            setNominatimResults([]);
            return;
        }
        debounceRef.current = setTimeout(async () => {
            setLoading(true);
            try {
                const r = await axios.get(`${API}/geo/search`, {
                    params: { q: value.trim(), city, limit: 5 },
                });
                setNominatimResults(r.data.results || []);
            } catch (_e) {
                setNominatimResults([]);
            } finally {
                setLoading(false);
            }
        }, 450);
        return () => {
            if (debounceRef.current) clearTimeout(debounceRef.current);
        };
    }, [value, city]);

    const handleInputChange = (e) => {
        onChange && onChange(e.target.value);
        if (!open) setOpen(true);
    };

    const handleRoadPick = (name) => {
        onChange && onChange(name);
        if (onPickRoad) onPickRoad(name);
        setOpen(false);
    };

    const handleAddressPick = (r) => {
        onChange && onChange(r.display_name.split(',')[0]);
        if (onPick) onPick(r);
        setOpen(false);
        setNominatimResults([]);
    };

    const showDropdown = open && (roadMatches.length > 0 || nominatimResults.length > 0 || loading);

    return (
        <Popover open={showDropdown} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <div className={`relative ${className}`} ref={containerRef}>
                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[color:var(--tiq-muted)] pointer-events-none" />
                    <input
                        data-testid={testId}
                        value={value}
                        onChange={handleInputChange}
                        onFocus={() => setOpen(true)}
                        placeholder={placeholder}
                        className="w-full pl-8 pr-8 py-2.5 bg-transparent outline-none text-sm border border-[color:var(--tiq-border-strong)] rounded-md focus:border-[color:var(--tiq-primary)]"
                    />
                    {loading && (
                        <Loader2 className="absolute right-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 animate-spin text-[color:var(--tiq-muted)]" />
                    )}
                    {!loading && value && (
                        <button
                            type="button"
                            onClick={(e) => {
                                e.stopPropagation();
                                onChange && onChange('');
                            }}
                            className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 grid place-items-center rounded hover:bg-white/10"
                            aria-label="Clear"
                            tabIndex={-1}
                        >
                            <X className="h-3 w-3 text-[color:var(--tiq-muted)]" />
                        </button>
                    )}
                </div>
            </PopoverTrigger>
            <PopoverContent
                align="start"
                sideOffset={4}
                className="w-[380px] p-0 bg-[color:var(--tiq-card)] border-[color:var(--tiq-border)] text-[color:var(--tiq-foreground)]"
                onOpenAutoFocus={(e) => e.preventDefault()}
            >
                <div className="max-h-[360px] overflow-y-auto py-1">
                    {roadMatches.length > 0 && (
                        <>
                            <div className="px-3 py-1.5 text-[10px] mono uppercase tracking-wider text-[color:var(--tiq-muted)]">
                                Local Roads
                            </div>
                            {roadMatches.map((r) => (
                                <button
                                    key={`road-${r}`}
                                    onClick={() => handleRoadPick(r)}
                                    data-testid={`${testId}-road-${r}`}
                                    className="w-full flex items-center gap-2 px-3 py-2 text-left text-sm hover:bg-white/[0.04]"
                                >
                                    <RouteIcon className="h-3.5 w-3.5 opacity-60 flex-shrink-0 text-[color:var(--tiq-primary)]" />
                                    <span className="flex-1 truncate">{r}</span>
                                </button>
                            ))}
                            {nominatimResults.length > 0 && (
                                <div className="border-t border-[color:var(--tiq-border)] mx-2 my-1" />
                            )}
                        </>
                    )}
                    {nominatimResults.length > 0 && (
                        <>
                            <div className="px-3 py-1.5 text-[10px] mono uppercase tracking-wider text-[color:var(--tiq-muted)]">
                                Addresses & Places
                            </div>
                            {nominatimResults.map((r, i) => (
                                <button
                                    key={`addr-${i}`}
                                    onClick={() => handleAddressPick(r)}
                                    data-testid={`${testId}-result-${i}`}
                                    className="w-full flex items-start gap-2 px-3 py-2 text-left text-sm hover:bg-white/[0.04]"
                                >
                                    <MapPin className="h-3.5 w-3.5 opacity-60 mt-0.5 flex-shrink-0" />
                                    <div className="flex-1 min-w-0">
                                        <div className="font-medium truncate">
                                            {r.display_name.split(',')[0]}
                                        </div>
                                        <div className="text-[11px] text-[color:var(--tiq-muted)] mono truncate">
                                            {r.display_name.split(',').slice(1, 4).join(',').trim() || r.type}
                                        </div>
                                    </div>
                                </button>
                            ))}
                        </>
                    )}
                    {!loading && roadMatches.length === 0 && nominatimResults.length === 0 && value.trim().length >= 3 && (
                        <div className="px-3 py-4 text-sm text-center text-[color:var(--tiq-muted)]">
                            No matches
                        </div>
                    )}
                    {!loading && value.trim().length < 3 && roadMatches.length === 0 && (
                        <div className="px-3 py-4 text-sm text-center text-[color:var(--tiq-muted)]">
                            Type at least 3 characters to search addresses
                        </div>
                    )}
                </div>
            </PopoverContent>
        </Popover>
    );
};

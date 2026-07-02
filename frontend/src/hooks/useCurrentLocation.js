import { useCallback, useState } from 'react';
import axios from 'axios';
import { API } from '@/contexts/TrafficContext';
import { toast } from 'sonner';

/**
 * Hook that uses browser geolocation and resolves the nearest road segment
 * via the backend `/api/geo/nearest` endpoint.
 */
export const useCurrentLocation = () => {
    const [loading, setLoading] = useState(false);
    const [lastCoord, setLastCoord] = useState(null);

    const detect = useCallback(async ({ city } = {}) => {
        if (!('geolocation' in navigator)) {
            toast.error('Geolocation is not supported by your browser');
            return null;
        }
        setLoading(true);
        try {
            const pos = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: true,
                    timeout: 12000,
                    maximumAge: 60000,
                });
            });
            const lat = pos.coords.latitude;
            const lng = pos.coords.longitude;
            setLastCoord([lat, lng]);

            const params = new URLSearchParams({ lat: String(lat), lng: String(lng) });
            if (city) params.set('city', city);
            const r = await axios.get(`${API}/geo/nearest?${params.toString()}`);
            return {
                lat,
                lng,
                city: r.data.city,
                distance_km: r.data.distance_km,
                segment: r.data.segment,
            };
        } catch (err) {
            if (err && err.code === 1) {
                toast.error('Location permission denied. Please enable it in your browser.');
            } else if (err && err.code === 2) {
                toast.error('Position unavailable. Try again outside or check your GPS.');
            } else if (err && err.code === 3) {
                toast.error('Timed out while getting your location');
            } else {
                toast.error('Could not detect your location');
            }
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    return { detect, loading, lastCoord };
};

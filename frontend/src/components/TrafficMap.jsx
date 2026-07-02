import { MapContainer, TileLayer, Polyline, CircleMarker, Tooltip, useMap, useMapEvents } from 'react-leaflet';
import { useEffect, useMemo, useRef } from 'react';
import L from 'leaflet';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const STATUS_COLOR = {
    clear: '#2EE59D',
    moderate: '#F7C948',
    congested: '#FF4D4D',
};

const RecenterOnCityChange = ({ center, zoom }) => {
    const map = useMap();
    useEffect(() => {
        if (center) map.setView(center, zoom, { animate: true });
    }, [center, zoom, map]);
    return null;
};

const MapClickCatcher = ({ onMapClick }) => {
    useMapEvents({
        click(e) {
            if (onMapClick) onMapClick(e.latlng.lat, e.latlng.lng);
        },
    });
    return null;
};

export const TrafficMap = ({
    center,
    zoom = 12,
    segments = [],
    highlightRouteCoords = null,
    startCoord = null,
    endCoord = null,
    onSegmentClick = null,
    onMapClick = null,
    height = 460,
    theme = 'dark',
}) => {
    const tileUrl = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
    const tileClass = theme === 'light' ? '' : 'tiq-tiles';

    // Track segment changes for pulse animation
    const prevStatusRef = useRef({});
    const changedIds = useMemo(() => {
        const s = new Set();
        for (const seg of segments) {
            const prev = prevStatusRef.current[seg.id];
            if (prev !== undefined && prev !== seg.status) s.add(seg.id);
        }
        const next = {};
        for (const seg of segments) next[seg.id] = seg.status;
        prevStatusRef.current = next;
        return s;
    }, [segments]);

    return (
        <div className="map-shell" style={{ height }} data-testid="traffic-map">
            <MapContainer
                center={center}
                zoom={zoom}
                style={{ height: '100%', width: '100%' }}
                scrollWheelZoom={true}
                preferCanvas={true}
                zoomControl={true}
                attributionControl={true}
            >
                <TileLayer
                    className={tileClass}
                    attribution='&copy; OpenStreetMap contributors'
                    url={tileUrl}
                />
                <RecenterOnCityChange center={center} zoom={zoom} />
                {onMapClick && <MapClickCatcher onMapClick={onMapClick} />}

                {segments.map((seg) => {
                    const color = STATUS_COLOR[seg.status] || '#00D4FF';
                    const pulsed = changedIds.has(seg.id);
                    const path = seg.coords && seg.coords.length > 1 ? seg.coords : [seg.from, seg.to];
                    return (
                        <Polyline
                            key={seg.id}
                            positions={path}
                            pathOptions={{
                                color,
                                weight: 3.2,
                                opacity: 0.85,
                                lineCap: 'round',
                                lineJoin: 'round',
                                className: pulsed ? 'tiq-pulse' : '',
                            }}
                            eventHandlers={onSegmentClick ? { click: () => onSegmentClick(seg) } : undefined}
                        >
                            <Tooltip direction="top" offset={[0, -6]} opacity={1} sticky>
                                <div className="mono text-xs">
                                    <div className="font-semibold text-[13px]" style={{ color }}>
                                        {seg.name}
                                    </div>
                                    <div className="opacity-80">
                                        {seg.status.toUpperCase()} · {seg.congestion?.toFixed(1)}% · {seg.speed_kmph?.toFixed(1)} kmph
                                    </div>
                                </div>
                            </Tooltip>
                        </Polyline>
                    );
                })}

                {/* Highlighted route */}
                {highlightRouteCoords && highlightRouteCoords.length > 1 && (
                    <>
                        <Polyline
                            positions={highlightRouteCoords}
                            pathOptions={{
                                color: '#00D4FF',
                                weight: 7,
                                opacity: 0.45,
                                lineCap: 'round',
                                lineJoin: 'round',
                            }}
                        />
                        <Polyline
                            positions={highlightRouteCoords}
                            pathOptions={{
                                color: '#ffffff',
                                weight: 2.8,
                                opacity: 0.98,
                                dashArray: '2 6',
                                lineCap: 'round',
                                lineJoin: 'round',
                            }}
                        />
                    </>
                )}

                {startCoord && (
                    <CircleMarker
                        center={startCoord}
                        radius={8}
                        pathOptions={{ color: '#00D4FF', fillColor: '#00D4FF', fillOpacity: 0.9, weight: 2 }}
                    >
                        <Tooltip permanent direction="top" offset={[0, -6]}>
                            <span className="mono text-[11px]">START</span>
                        </Tooltip>
                    </CircleMarker>
                )}
                {endCoord && (
                    <CircleMarker
                        center={endCoord}
                        radius={8}
                        pathOptions={{ color: '#2EE59D', fillColor: '#2EE59D', fillOpacity: 0.9, weight: 2 }}
                    >
                        <Tooltip permanent direction="top" offset={[0, -6]}>
                            <span className="mono text-[11px]">END</span>
                        </Tooltip>
                    </CircleMarker>
                )}
            </MapContainer>

            <div className="map-legend">
                <span className="legend-chip">
                    <span className="legend-dot" style={{ background: STATUS_COLOR.clear }} />
                    Clear
                </span>
                <span className="legend-chip">
                    <span className="legend-dot" style={{ background: STATUS_COLOR.moderate }} />
                    Moderate
                </span>
                <span className="legend-chip">
                    <span className="legend-dot" style={{ background: STATUS_COLOR.congested }} />
                    Congested
                </span>
            </div>
        </div>
    );
};

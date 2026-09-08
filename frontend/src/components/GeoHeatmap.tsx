import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet.heat';
import { MapPin } from 'lucide-react';
import { GeoHeatmapPoint } from './types';

interface GeoHeatmapProps {
  points: GeoHeatmapPoint[];
}

export const GeoHeatmap: React.FC<GeoHeatmapProps> = ({ points }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Initialize Leaflet map centered on Northern India
    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [26.5, 80.5],
        zoom: 5,
        zoomControl: true,
      });

      // OpenStreetMap's free tile service keeps the map functional without an API key.
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18,
      }).addTo(map);

      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;

    // Clear any previous layers (except tile layer)
    map.eachLayer(layer => {
      if (!(layer instanceof L.TileLayer)) {
        map.removeLayer(layer);
      }
    });

    if (points.length === 0) return;

    // 1. Prepare Leaflet.heat layer data: [lat, lng, intensity]
    const maxWeight = Math.max(...points.map(p => p.weight), 1.0);
    const heatData = points.map(p => [
      p.lat,
      p.lng,
      Math.min(1.0, (p.weight / maxWeight) * 1.5)
    ]);

    const heatLayerFactory = (L as typeof L & {
      heatLayer?: (data: number[][], options: Record<string, unknown>) => L.Layer;
    }).heatLayer;
    if (heatLayerFactory) {
      const heat = heatLayerFactory(heatData, {
        radius: 35,
        blur: 25,
        maxZoom: 12,
        gradient: {
          0.2: '#38bdf8',
          0.4: '#34d399',
          0.6: '#fbbf24',
          0.8: '#f97316',
          1.0: '#ef4444'
        }
      });
      heat.addTo(map);
    }

    // 2. Add custom pulsing hotspot markers with popups
    points.forEach(pt => {
      const radius = Math.max(6, Math.min(22, 6 + (pt.weight / maxWeight) * 16));

      const circle = L.circleMarker([pt.lat, pt.lng], {
        radius: radius,
        fillColor: pt.weight > 10 ? '#ef4444' : '#8b5cf6',
        color: '#ffffff',
        weight: 1.5,
        opacity: 0.9,
        fillOpacity: 0.75
      }).addTo(map);

      circle.bindPopup(`
        <div style="font-family: 'DM Sans', sans-serif; font-size: 12px; color: #0f172a; padding: 4px;">
          <b style="color: #0284c7; font-size: 13px;">${pt.location}</b><br/>
          <b>Coordinates:</b> ${pt.lat.toFixed(4)}, ${pt.lng.toFixed(4)}<br/>
          <b>Activity Weight:</b> <span style="color: #dc2626; font-weight: bold;">${pt.weight} event(s)</span>
        </div>
      `);
    });

    // Fit map bounds to points
    const bounds = L.latLngBounds(points.map(p => [p.lat, p.lng]));
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 10 });

  }, [points]);

  return (
    <div className="relative flex flex-col h-full bg-zinc-950 overflow-hidden">
      
      {/* Header / Legend */}
      <div className="flex items-center justify-between px-4 py-2 bg-zinc-900/90 border-b border-zinc-800 z-10 text-xs">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-rose-400" />
          <span className="font-bold text-zinc-100">
            Geographic Activity Hotspots (Tower Geolocation + FIR Raids)
          </span>
        </div>

        <div className="flex items-center gap-3 text-[11px] font-mono text-zinc-400">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
            <span>Moderate (NCR / UP)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
            <span className="text-rose-300 font-bold">Critical Hotspot (New Delhi Hub)</span>
          </div>
        </div>
      </div>

      {/* Leaflet Map Canvas */}
      <div ref={mapContainerRef} className="flex-1 w-full h-full min-h-[350px] z-0" />

    </div>
  );
};

"use client";
import { useEffect, useRef, useState, useCallback } from "react";

interface Props {
  onSelect: (lat: number, lon: number, address: string) => void;
  initialLat?: number;
  initialLon?: number;
}

declare global { interface Window { mapgl: any; } }

export default function DeliveryMap({ onSelect, initialLat, initialLon }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const markerRef = useRef<any>(null);
  const [loaded, setLoaded] = useState(false);
  const [address, setAddress] = useState("");
  const apiKey = process.env.NEXT_PUBLIC_2GIS_KEY;

  const handleMapClick = useCallback((lat: number, lon: number) => {
    if (markerRef.current) markerRef.current.destroy();
    if (!mapRef.current) return;
    markerRef.current = new window.mapgl.Marker(mapRef.current, {
      coordinates: [lon, lat],
      label: { text: "📍 Доставка", fontSize: 14, color: "#e03131" },
    });
    setAddress(lat.toFixed(6) + ", " + lon.toFixed(6));
    onSelect(lat, lon, lat.toFixed(6) + ", " + lon.toFixed(6));
  }, [onSelect]);

  useEffect(() => {
    if (loaded || !apiKey) return;
    if (window.mapgl) { setLoaded(true); return; }
    const s = document.createElement("script");
    s.src = "https://mapgl.2gis.com/api/js/v1";
    s.onload = () => setLoaded(true);
    s.onerror = () => console.warn("2GIS map load failed");
    document.head.appendChild(s);
  }, [loaded, apiKey]);

  useEffect(() => {
    if (!loaded || !containerRef.current || mapRef.current) return;
    const map = new window.mapgl.Map(containerRef.current, {
      center: [initialLon || 37.62, initialLat || 55.75],
      zoom: 10,
      key: apiKey,
    });
    mapRef.current = map;
    map.on("click", (e: any) => {
      handleMapClick(e.lngLat[1], e.lngLat[0]);
    });
    if (initialLat && initialLon) {
      handleMapClick(initialLat, initialLon);
    }
  }, [loaded, initialLat, initialLon, apiKey, handleMapClick]);

  if (!apiKey) {
    return (
      <div className="p-10 text-center text-label-3 border border-separator rounded-[var(--radius-md)] text-sm">
        Карта недоступна — не указан ключ 2GIS
      </div>
    );
  }

  return (
    <div className="h-full">
      <div ref={containerRef} className="w-full h-full min-h-[280px] rounded-[var(--radius-md)]" />
      {address && <p className="text-xs text-label-3 mt-1">📍 {address}</p>}
    </div>
  );
}

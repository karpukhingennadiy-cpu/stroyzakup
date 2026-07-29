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
    return <div style={{ padding: 40, textAlign: "center", color: "#94a3b8", border: "1px solid #e2e8f0", borderRadius: 8 }}>
      Карта недоступна — не указан ключ 2GIS
    </div>;
  }

  return (
    <div>
      <div ref={containerRef} style={{ width: "100%", height: 400, borderRadius: 8, border: "1px solid #e2e8f0" }} />
      {address && <p style={{ fontSize: 12, color: "#64748b", marginTop: 4 }}>📍 {address}</p>}
    </div>
  );
}

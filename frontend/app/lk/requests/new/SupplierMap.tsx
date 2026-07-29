"use client";
import { useEffect, useRef } from "react";

interface Supplier {
  supplier_id: number; name: string; city: string;
  total_score: number; distance_km: number | null;
  latitude: number | null;
  longitude: number | null;
  email?: string; phone?: string; site?: string;
}

interface Props {
  suppliers: Supplier[];
  centerLat: number;
  centerLon: number;
}

declare global { interface Window { mapgl: any; } }

export default function SupplierMap({ suppliers, centerLat, centerLon }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const apiKey = process.env.NEXT_PUBLIC_2GIS_KEY;
    if (!apiKey) {
      console.warn("2GIS API key not configured. Map disabled.");
      return;
    }

    function initMap() {
      if (!containerRef.current || !window.mapgl) return;

      const map = new window.mapgl.Map(containerRef.current, {
        center: [centerLon, centerLat],
        zoom: 10,
        key: apiKey,
      });
      mapRef.current = map;

      // Delivery point marker (red)
      new window.mapgl.Marker(map, {
        coordinates: [centerLon, centerLat],
        label: { text: "📍 Доставка", fontSize: 14, color: "#e03131" },
      });

      // Supplier markers at REAL coordinates
      const withCoords = suppliers.filter((s) => s.latitude && s.longitude);
      withCoords.slice(0, 30).forEach((s) => {
        new window.mapgl.Marker(map, {
          coordinates: [s.longitude!, s.latitude!],
          label: { text: s.name, fontSize: 11, color: "#1971c2" },
        });
      });
    }

    if (window.mapgl) {
      initMap();
    } else {
      const script = document.createElement("script");
      script.src = `https://mapgl.2gis.com/api/js/v1?key=${apiKey}`;
      script.onload = initMap;
      script.onerror = () => console.warn("2GIS map failed to load");
      document.head.appendChild(script);
    }
  }, [suppliers, centerLat, centerLon]);

  return (
    <div>
      <div ref={containerRef} style={{ width: "100%", height: 400, borderRadius: 8, border: "1px solid #e2e8f0" }} />
      <p style={{ fontSize: 12, color: "#94a3b8", marginTop: 4 }}>
        Поставщики с координатами: {suppliers.filter((s) => s.latitude && s.longitude).length} из {suppliers.length}
      </p>
    </div>
  );
}

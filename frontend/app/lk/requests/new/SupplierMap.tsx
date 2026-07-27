"use client";
import { useEffect, useRef } from "react";

interface Supplier {
  supplier_id: number; name: string; city: string;
  total_score: number; distance_km: number | null;
  latitude: number | null;
  longitude: number | null;
  email?: string; phone?: string; site?: string;
  category_score?: number; distance_score?: number;
  manufacturer_bonus?: number; supplier_type?: string; source?: string;
}

interface Props {
  suppliers: Supplier[];
  centerLat: number;
  centerLon: number;
}

declare global { interface Window { ymaps: any; } }

export default function SupplierMap({ suppliers, centerLat, centerLon }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    
    function initMap() {
      if (!containerRef.current) return;
      const ymaps = window.ymaps;
      if (!ymaps) return;
      
      const map = new ymaps.Map(containerRef.current, {
        center: [centerLat, centerLon],
        zoom: 10,
        controls: ["zoomControl"],
      });
      mapRef.current = map;

      // Delivery point marker
      map.geoObjects.add(new ymaps.Placemark([centerLat, centerLon], {
        hintContent: "\u0422\u043e\u0447\u043a\u0430 \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438",
      }, { preset: "islands#redCircleIcon" }));

      // Supplier markers at REAL coordinates
      const withCoords = suppliers.filter((s: any) => s.latitude && s.longitude);
      const withoutCoords = suppliers.filter((s: any) => !s.latitude || !s.longitude);

      withCoords.slice(0, 30).forEach((s: any) => {
        const slat = s.latitude;
        const slon = s.longitude;
        
        map.geoObjects.add(new ymaps.Placemark([slat, slon], {
          hintContent: s.name,
          balloonContent: "<strong>" + s.name + "</strong><br/>" + (s.city || "") + "<br/>\u0411\u0430\u043b\u043b\u044b: " + s.total_score.toFixed(0),
        }, {
          preset: "islands#blueDotIcon",
        }));
      });

      // Show suppliers without coordinates below map
      if (withoutCoords.length > 0 && typeof document !== "undefined") {
        const noteEl = document.getElementById("supplier-no-coords-note");
        if (noteEl) {
          noteEl.textContent = withoutCoords.length + " поставщиков без координат (показаны в таблице)";
          noteEl.style.display = "block";
        }
      }
    }

    if (window.ymaps) {
      window.ymaps.ready(initMap);
    } else {
      const script = document.createElement("script");
      script.src = "https://api-maps.yandex.ru/2.1/?lang=ru_RU&apikey=cb0b8e22-2e0b-4b02-b8e8-fd2a2f4d5e6f";
      script.onload = () => window.ymaps.ready(initMap);
      document.head.appendChild(script);
    }

    return () => {
      if (mapRef.current) { mapRef.current.destroy(); mapRef.current = null; }
    };
  }, [centerLat, centerLon, suppliers]);

  return <div ref={containerRef} className="w-full h-full" />;
}

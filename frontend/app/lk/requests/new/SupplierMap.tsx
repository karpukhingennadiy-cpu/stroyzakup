"use client";
import { useEffect, useRef } from "react";

interface Supplier {
  supplier_id: number; name: string; city: string;
  total_score: number; distance_km: number | null;
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

      // Supplier markers around delivery point
      suppliers.slice(0, 20).forEach((s, i) => {
        // Spread markers in a circle for visibility
        const angle = (i / Math.min(suppliers.length, 20)) * Math.PI * 2;
        const spread = 0.02; // ~2km spread
        const slat = centerLat + Math.cos(angle) * spread * (i + 1);
        const slon = centerLon + Math.sin(angle) * spread * (i + 1);
        
        map.geoObjects.add(new ymaps.Placemark([slat, slon], {
          hintContent: s.name,
          balloonContent: "<strong>" + s.name + "</strong><br/>" + (s.city || "") + "<br/>\u0411\u0430\u043b\u043b\u044b: " + s.total_score.toFixed(0),
        }, {
          preset: "islands#blueDotIcon",
        }));
      });
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

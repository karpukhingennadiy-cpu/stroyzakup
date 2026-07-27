"use client";
import { useEffect, useRef, useState, useCallback } from "react";

declare global {
  interface Window {
    ymaps: any;
  }
}

interface Props {
  onLocationSelect: (lat: number, lon: number, address: string) => void;
}

export default function DeliveryMap({ onLocationSelect }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const placemarkRef = useRef<any>(null);
  const [locating, setLocating] = useState(false);
  const [loaded, setLoaded] = useState(false);

  // Load Yandex Maps script
  useEffect(() => {
    if (window.ymaps) { setLoaded(true); return; }
    const script = document.createElement("script");
    script.src = "https://api-maps.yandex.ru/2.1/?lang=ru_RU&apikey=cb0b8e22-2e0b-4b02-b8e8-fd2a2f4d5e6f";
    script.onload = () => {
      window.ymaps.ready(() => setLoaded(true));
    };
    script.onerror = () => console.warn("Yandex Maps failed to load");
    document.head.appendChild(script);
  }, []);

  // Initialize map
  useEffect(() => {
    if (!loaded || !containerRef.current || mapRef.current) return;

    const ymaps = window.ymaps;
    const map = new ymaps.Map(containerRef.current, {
      center: [55.75, 37.62],
      zoom: 5,
      controls: ["zoomControl", "typeSelector"],
    });
    mapRef.current = map;

    // Click handler
    map.events.add("click", async (e: any) => {
      const coords = e.get("coords");
      const lat = coords[0];
      const lon = coords[1];

      // Update placemark
      if (placemarkRef.current) {
        placemarkRef.current.geometry.setCoordinates([lat, lon]);
      } else {
        placemarkRef.current = new ymaps.Placemark([lat, lon], {}, {
          preset: "islands#redDotIcon",
        });
        map.geoObjects.add(placemarkRef.current);
      }

      // Reverse geocode
      try {
        const result = await ymaps.geocode([lat, lon]);
        const geoObject = result.geoObjects.get(0);
        const addr = geoObject ? geoObject.getAddressLine() : lat.toFixed(5) + ", " + lon.toFixed(5);
        onLocationSelect(lat, lon, addr);
      } catch {
        onLocationSelect(lat, lon, lat.toFixed(5) + ", " + lon.toFixed(5));
      }
    });

    return () => { map.destroy(); mapRef.current = null; };
  }, [loaded]);

  // Locate user
  const handleLocate = useCallback(() => {
    if (!mapRef.current) return;
    setLocating(true);
    const ymaps = window.ymaps;
    ymaps.geolocation.get({
      provider: "browser",
      mapStateAutoApply: true,
    }).then((result: any) => {
      const coords = result.geoObjects.get(0).geometry.getCoordinates();
      const lat = coords[0];
      const lon = coords[1];
      mapRef.current.setCenter([lat, lon], 14);
      if (placemarkRef.current) {
        placemarkRef.current.geometry.setCoordinates([lat, lon]);
      } else {
        placemarkRef.current = new ymaps.Placemark([lat, lon], {}, { preset: "islands#redDotIcon" });
        mapRef.current.geoObjects.add(placemarkRef.current);
      }
      ymaps.geocode([lat, lon]).then((geoResult: any) => {
        const geoObject = geoResult.geoObjects.get(0);
        const addr = geoObject ? geoObject.getAddressLine() : lat.toFixed(5) + ", " + lon.toFixed(5);
        onLocationSelect(lat, lon, addr);
      });
      setLocating(false);
    }).catch(() => setLocating(false));
  }, [onLocationSelect]);

  if (!loaded) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-[#f5f7fa] text-[#64748b]">
        Загрузка карты...
      </div>
    );
  }

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full" />
      <button onClick={handleLocate} disabled={locating}
        className="absolute bottom-4 right-4 z-[1000] px-4 py-2 bg-white border border-[#e2e8f0] rounded-xl shadow-md text-sm font-medium hover:bg-[#f5f7fa] transition disabled:opacity-50">
        {locating ? "Определение..." : "Моё местоположение"}
      </button>
    </div>
  );
}

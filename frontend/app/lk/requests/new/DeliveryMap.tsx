"use client";
import { useEffect, useRef, useState, useCallback } from "react";

declare global { interface Window { ymaps: any; } }

interface Props { onLocationSelect: (lat: number, lon: number, address: string) => void; }

export default function DeliveryMap({ onLocationSelect }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const placemarkRef = useRef<any>(null);
  const [locating, setLocating] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [mapError, setMapError] = useState("");

  useEffect(() => {
    if (window.ymaps) { setLoaded(true); return; }
    const s = document.createElement("script");
    s.src = "https://api-maps.yandex.ru/2.1/?lang=ru_RU&apikey=cb0b8e22-2e0b-4b02-b8e8-fd2a2f4d5e6f";
    s.onload = () => window.ymaps.ready(() => setLoaded(true));
    s.onerror = () => setMapError("Не удалось загрузить карту");
    document.head.appendChild(s);
  }, []);

  const placeMarker = useCallback(async (lat: number, lon: number) => {
    if (!window.ymaps) return;
    const ymaps = window.ymaps;
    if (placemarkRef.current) {
      placemarkRef.current.geometry.setCoordinates([lat, lon]);
    } else {
      placemarkRef.current = new ymaps.Placemark([lat, lon], {}, { preset: "islands#redDotIcon" });
      mapRef.current.geoObjects.add(placemarkRef.current);
    }
    try {
      const r = await ymaps.geocode([lat, lon]);
      const geo = r.geoObjects.get(0);
      onLocationSelect(lat, lon, geo ? geo.getAddressLine() : lat.toFixed(5) + ", " + lon.toFixed(5));
    } catch {
      onLocationSelect(lat, lon, lat.toFixed(5) + ", " + lon.toFixed(5));
    }
  }, [onLocationSelect]);

  useEffect(() => {
    if (!loaded || !containerRef.current || mapRef.current) return;
    const ymaps = window.ymaps;
    const map = new ymaps.Map(containerRef.current, { center: [55.75, 37.62], zoom: 5, controls: ["zoomControl", "typeSelector"] });
    mapRef.current = map;
    map.events.add("click", (e: any) => { const c = e.get("coords"); placeMarker(c[0], c[1]); });
    return () => { map.destroy(); mapRef.current = null; };
  }, [loaded, placeMarker]);

  const handleLocate = useCallback(() => {
    setLocating(true); setMapError("");
    const onPos = (lat: number, lon: number) => {
      if (mapRef.current) mapRef.current.setCenter([lat, lon], 14);
      placeMarker(lat, lon); setLocating(false);
    };
    // Try browser Geolocation API directly (works on HTTP too)
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => onPos(pos.coords.latitude, pos.coords.longitude),
        (err) => {
          // Fallback: try Yandex
          if (window.ymaps) {
            window.ymaps.geolocation.get({ provider: "browser", mapStateAutoApply: false })
              .then((r: any) => { const c = r.geoObjects.get(0).geometry.getCoordinates(); onPos(c[0], c[1]); })
              .catch(() => { setMapError("Не удалось. Кликните на карту."); setLocating(false); });
          } else {
            setMapError("Геолокация недоступна. Кликните на карту.");
            setLocating(false);
          }
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
      );
    } else {
      setMapError("Кликните на карту чтобы указать точку");
      setLocating(false);
    }
  }, [placeMarker]);

  if (!loaded && !mapError) return <div className="w-full h-full flex items-center justify-center bg-[#f5f7fa] text-[#64748b]">Загрузка карты...</div>;

  if (mapError && !loaded) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center bg-[#f5f7fa] gap-3 p-6">
        <p className="text-[#64748b] text-sm">{mapError}</p>
        <p className="text-xs text-[#94a3b8]">Или введите координаты:</p>
        <div className="flex gap-2">
          <input id="mlat" type="number" step="any" placeholder="55.75" className="px-3 py-2 border rounded-lg text-sm w-32" />
          <input id="mlon" type="number" step="any" placeholder="37.62" className="px-3 py-2 border rounded-lg text-sm w-32" />
          <button onClick={() => {
            const lat = parseFloat((document.getElementById("mlat") as HTMLInputElement).value);
            const lon = parseFloat((document.getElementById("mlon") as HTMLInputElement).value);
            if (!isNaN(lat) && !isNaN(lon)) onLocationSelect(lat, lon, lat.toFixed(5) + ", " + lon.toFixed(5));
          }} className="px-4 py-2 bg-[#f0a500] text-white rounded-lg text-sm font-medium">OK</button>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full" />
      {mapError && <div className="absolute top-4 left-4 right-4 z-[1000] p-3 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-800">{mapError}</div>}
      <button onClick={handleLocate} disabled={locating}
        className="absolute bottom-4 right-4 z-[1000] px-4 py-2 bg-white border border-[#e2e8f0] rounded-xl shadow-md text-sm font-medium hover:bg-[#f5f7fa] transition disabled:opacity-50">
        {locating ? "Определение..." : "Моё местоположение"}
      </button>
    </div>
  );
}

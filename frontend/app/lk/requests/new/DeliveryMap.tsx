"use client";
import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

interface Props {
  onLocationSelect: (lat: number, lon: number, address: string) => void;
}

export default function DeliveryMap({ onLocationSelect }: Props) {
  const mapRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [locating, setLocating] = useState(false);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = L.map(containerRef.current).setView([55.75, 37.62], 5);
    mapRef.current = map;
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 19,
    }).addTo(map);

    map.on("click", async (e: L.LeafletMouseEvent) => {
      const { lat, lng } = e.latlng;
      if (markerRef.current) {
        markerRef.current.setLatLng([lat, lng]);
      } else {
        markerRef.current = L.marker([lat, lng]).addTo(map);
      }
      try {
        const url = "https://nominatim.openstreetmap.org/reverse?lat=" + lat + "&lon=" + lng + "&format=json&accept-language=ru";
        const resp = await fetch(url);
        const data = await resp.json();
        const addr = data.display_name || lat.toFixed(5) + ", " + lng.toFixed(5);
        onLocationSelect(lat, lng, addr);
      } catch {
        onLocationSelect(lat, lng, lat.toFixed(5) + ", " + lng.toFixed(5));
      }
    });

    return () => { map.remove(); mapRef.current = null; };
  }, []);

  const handleLocate = () => {
    if (!mapRef.current) return;
    setLocating(true);
    mapRef.current.locate({ setView: true, maxZoom: 14 });
    mapRef.current.once("locationfound", (e) => {
      const { lat, lng } = e.latlng;
      if (markerRef.current) {
        markerRef.current.setLatLng([lat, lng]);
      } else {
        markerRef.current = L.marker([lat, lng]).addTo(mapRef.current!);
      }
      const url = "https://nominatim.openstreetmap.org/reverse?lat=" + lat + "&lon=" + lng + "&format=json&accept-language=ru";
      fetch(url).then(r => r.json()).then(data => {
        onLocationSelect(lat, lng, data.display_name || lat.toFixed(5) + ", " + lng.toFixed(5));
      }).catch(() => {
        onLocationSelect(lat, lng, lat.toFixed(5) + ", " + lng.toFixed(5));
      });
      setLocating(false);
    });
    mapRef.current.once("locationerror", () => setLocating(false));
  };

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

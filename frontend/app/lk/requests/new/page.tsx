"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { createRequest, geocodeAddress } from "@/lib/api";
import { IconPlus, IconHardHat, IconMapPin } from "@/components/icons";

export default function NewRequestPage() {
  const router = useRouter();
  const [rawText, setRawText] = useState("");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [geoLoading, setGeoLoading] = useState(false);
  const [geoResult, setGeoResult] = useState<any>(null);
  const [error, setError] = useState("");

  const handleGeocode = async () => {
    if (!deliveryAddress.trim()) return;
    setGeoLoading(true);
    setError("");
    try {
      const result = await geocodeAddress(deliveryAddress);
      setGeoResult(result);
    } catch (err: any) {
      // Geocoding failed - user can still proceed without coordinates
      setGeoResult(null);
      setError("Адрес не найден на карте. Можно продолжить без координат — поиск поставщиков будет по городу.");
    } finally {
      setGeoLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawText.trim()) return;
    setError("");
    setLoading(true);
    try {
      const req = await createRequest(
        rawText,
        comment || undefined,
        deliveryAddress || undefined,
        geoResult || undefined
      );
      router.push("/lk/requests/" + req.id);
    } catch (err: any) {
      setError(err.message || "Ошибка создания заявки");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#1a1a2e]">Новая заявка</h1>
        <p className="text-[#64748b] mt-1">Вставьте список материалов — система распознает позиции автоматически</p>
      </div>

      <div className="bg-white rounded-2xl border border-[#e2e8f0] shadow-sm overflow-hidden">
        <div className="p-6 border-b border-[#e2e8f0] bg-[#f5f7fa]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#1e3a5f]/10 flex items-center justify-center">
              <IconHardHat className="w-5 h-5 text-[#1e3a5f]" />
            </div>
            <div>
              <p className="font-semibold text-[#1a1a2e]">Список материалов</p>
              <p className="text-xs text-[#64748b]">Можно вставлять из Excel, сметы или писать вручную</p>
            </div>
          </div>
        </div>

        {error && (
          <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <textarea value={rawText} onChange={(e) => setRawText(e.target.value)}
            required rows={10}
            placeholder="Керамогранит серый 600x600 — 150 м² | Плиточный клей KNAUF Fliesen 25 кг — 100 мешков"
            className="w-full px-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition resize-y text-sm leading-relaxed" />

          {/* Delivery address */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm font-medium text-[#1a1a2e]">
              <IconMapPin className="w-4 h-4 text-[#f0a500]" />
              Адрес доставки
            </label>
            <div className="flex gap-2">
              <input value={deliveryAddress} onChange={(e) => { setDeliveryAddress(e.target.value); setGeoResult(null); }}
                type="text" placeholder="г. Подольск, ул. Ленина 5"
                className="flex-1 px-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition" />
              <button type="button" onClick={handleGeocode}
                disabled={geoLoading || !deliveryAddress.trim()}
                className="px-4 py-3 bg-[#1e3a5f] text-white rounded-xl text-sm font-medium hover:bg-[#162d4a] transition disabled:opacity-50 whitespace-nowrap">
                {geoLoading ? "Поиск..." : "Найти"}
              </button>
            </div>
            {geoResult && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-xl text-sm text-green-800">
                Найдено: {geoResult.city || geoResult.full_address}
                <span className="text-green-600 ml-2">({geoResult.latitude.toFixed(4)}, {geoResult.longitude.toFixed(4)})</span>
              </div>
            )}
            <p className="text-xs text-[#94a3b8]">Укажите адрес доставки — система подберёт ближайших поставщиков</p>
          </div>

          <input value={comment} onChange={(e) => setComment(e.target.value)}
            type="text" placeholder="Комментарий (необязательно)"
            className="w-full px-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition" />

          <button type="submit" disabled={loading || !rawText.trim()}
            className="w-full flex items-center justify-center gap-2 py-3.5 bg-[#f0a500] text-[#1a1a2e] rounded-xl font-bold text-base hover:bg-[#fcc419] hover:shadow-lg transition disabled:opacity-50">
            <IconPlus className="w-5 h-5" />
            {loading ? "Создаём..." : "Создать заявку"}
          </button>
        </form>
      </div>
    </div>
  );
}
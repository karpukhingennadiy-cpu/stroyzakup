"use client";
import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { createRequest, matchSuppliers, sendRfq, api } from "@/lib/api";
const SupplierMap = dynamic(() => import("./SupplierMap"), { ssr: false });
import { IconPlus, IconMapPin, IconHardHat, IconTruck } from "@/components/icons";

const DeliveryMap = dynamic(() => import("./DeliveryMap"), { ssr: false });

interface MaterialRow {
  id: number;
  name: string;
  specs: string;
  quantity: string;
  unit: string;
}

interface SupplierMatch {
  supplier_id: number;
  name: string;
  email: string;
  phone: string;
  city: string;
  distance_km: number | null;
  total_score: number;
  category_score: number;
  distance_score: number;
  rating_score: number;
  completeness_score: number;
  matched_count: number;
  total_categories: number;
  matched_categories: string[];
  supplier_type?: string;
  source?: string;
  manufacturer_bonus?: number;
}

const UNITS = ["m2", "m3", "kg", "ton", "bag", "piece", "pack", "roll", "pog_m", "liter", "sht"];

export default function NewRequestPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [rows, setRows] = useState<MaterialRow[]>([
    { id: 1, name: "", specs: "", quantity: "", unit: "m2" },
  ]);
  const [comment, setComment] = useState("");
  const addRow = () => setRows([...rows, { id: Date.now(), name: "", specs: "", quantity: "", unit: "m2" }]);
  const removeRow = (id: number) => rows.length > 1 && setRows(rows.filter(r => r.id !== id));
  const updateRow = (id: number, field: keyof MaterialRow, value: string) => {
    setRows(rows.map(r => r.id === id ? { ...r, [field]: value } : r));
  };

  const [deliveryLat, setDeliveryLat] = useState<number | null>(null);
  const [deliveryLon, setDeliveryLon] = useState<number | null>(null);
  const [deliveryAddr, setDeliveryAddr] = useState("");
  const [requestId, setRequestId] = useState<number | null>(null);
  const [suppliers, setSuppliers] = useState<SupplierMatch[]>([]);
  const [selectedSuppliers, setSelectedSuppliers] = useState<Set<number>>(new Set());
  const [sentCount, setSentCount] = useState(0);
  const [sourceFilter, setSourceFilter] = useState<string>("all");
  const [supplierLimit, setSupplierLimit] = useState(10);

  const buildRawText = () => {
    return rows.filter(r => r.name.trim()).map(r => {
      let line = r.name.trim();
      if (r.specs.trim()) line += " " + r.specs.trim();
      if (r.quantity.trim()) line += " - " + r.quantity.trim() + " " + r.unit;
      return line;
    }).join(String.fromCharCode(10));
  };

  const handleStep1Next = async () => {
    const filled = rows.filter(r => r.name.trim());
    if (filled.length === 0) { setError("Добавьте хотя бы один материал"); return; }
    setError("");
    setLoading(true);
    try {
      const rawText = buildRawText();
      const req = await createRequest(rawText, comment || undefined, undefined, undefined);
      setRequestId(req.id);
      setStep(2);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const handleStep2Next = async () => {
    if (!deliveryLat || !deliveryLon) { setError("Укажите точку доставки на карте"); return; }
    if (!requestId) return;
    setError("");
    setLoading(true);
    try {
      await api("/requests/" + requestId + "/", {
        method: "PATCH",
        body: JSON.stringify({ delivery_address: deliveryAddr, latitude: deliveryLat, longitude: deliveryLon }),
      });
      const result = await matchSuppliers(requestId, supplierLimit);
      setSuppliers(result.suppliers || []);
      setStep(3);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const toggleSupplier = (id: number) => {
    const next = new Set(selectedSuppliers);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelectedSuppliers(next);
  };

  const handleSendRfq = async () => {
    if (selectedSuppliers.size === 0) { setError("Выберите хотя бы одного поставщика"); return; }
    if (!requestId) return;
    setError("");
    setLoading(true);
    try {
      const result = await sendRfq(requestId, Array.from(selectedSuppliers));
      setSentCount(result.sent || 0);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#1a1a2e]">Новая заявка</h1>
        <div className="flex gap-6 mt-4">
          {[1, 2, 3].map(s => (
            <div key={s} className={"flex items-center gap-2 " + (step >= s ? "text-[#1e3a5f]" : "text-[#cbd5e1]")}>
              <div className={"w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold " + (step >= s ? "bg-[#1e3a5f] text-white" : "bg-[#e2e8f0] text-[#94a3b8]")}>{s}</div>
              <span className="text-sm font-medium">{s === 1 ? "Материалы" : s === 2 ? "Доставка" : "Поставщики"}</span>
              {s < 3 && <span className="text-[#cbd5e1] mx-2">→</span>}
            </div>
          ))}
        </div>
      </div>

      {error && <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">{error}</div>}

      {step === 1 && (
        <div className="bg-white rounded-2xl border border-[#e2e8f0] shadow-sm overflow-hidden">
          <div className="p-6 border-b border-[#e2e8f0] bg-[#f5f7fa]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#1e3a5f]/10 flex items-center justify-center"><IconHardHat className="w-5 h-5 text-[#1e3a5f]" /></div>
              <div><p className="font-semibold text-[#1a1a2e]">Шаг 1: Список материалов</p><p className="text-xs text-[#64748b]">Заполните таблицу — каждый товар отдельной строкой</p></div>
            </div>
          </div>
          <div className="p-6">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-[#e2e8f0] text-left">
                <th className="py-2 pr-2 font-semibold text-[#64748b] w-1/3">Материал</th>
                <th className="py-2 px-2 font-semibold text-[#64748b] w-1/3">Габариты / Спецификация</th>
                <th className="py-2 px-2 font-semibold text-[#64748b] w-1/6">Кол-во</th>
                <th className="py-2 px-2 font-semibold text-[#64748b] w-20">Ед.</th>
                <th className="py-2 w-10"></th>
              </tr></thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={row.id} className="border-b border-[#f5f7fa]">
                    <td className="py-1.5 pr-2"><input value={row.name} onChange={e => updateRow(row.id, "name", e.target.value)} placeholder="Керамогранит, Доска, Бетон..." className="w-full px-2 py-2 bg-[#f5f7fa] border border-[#e2e8f0] rounded-lg focus:bg-white focus:border-[#1e3a5f] transition text-sm" /></td>
                    <td className="py-1.5 px-2"><input value={row.specs} onChange={e => updateRow(row.id, "specs", e.target.value)} placeholder="600x600 серый, 25x150x6000, М300..." className="w-full px-2 py-2 bg-[#f5f7fa] border border-[#e2e8f0] rounded-lg focus:bg-white focus:border-[#1e3a5f] transition text-sm" /></td>
                    <td className="py-1.5 px-2"><input value={row.quantity} onChange={e => updateRow(row.id, "quantity", e.target.value)} type="number" min="0" step="any" placeholder="150" className="w-full px-2 py-2 bg-[#f5f7fa] border border-[#e2e8f0] rounded-lg focus:bg-white focus:border-[#1e3a5f] transition text-sm" /></td>
                    <td className="py-1.5 px-2"><select value={row.unit} onChange={e => updateRow(row.id, "unit", e.target.value)} className="w-full px-1 py-2 bg-[#f5f7fa] border border-[#e2e8f0] rounded-lg focus:bg-white text-sm">{UNITS.map(u => <option key={u} value={u}>{u}</option>)}</select></td>
                    <td className="py-1.5 text-center">{rows.length > 1 && <button onClick={() => removeRow(row.id)} className="p-1 text-[#94a3b8] hover:text-red-500 transition" title="Удалить строку">✕</button>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <button onClick={addRow} className="mt-3 flex items-center gap-1 text-sm text-[#1e3a5f] hover:text-[#f0a500] transition font-medium"><IconPlus className="w-4 h-4" /> Добавить строку</button>
            <div className="mt-4"><input value={comment} onChange={e => setComment(e.target.value)} placeholder="Комментарий к заявке (необязательно)" className="w-full px-4 py-2.5 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition text-sm" /></div>
            <button onClick={handleStep1Next} disabled={loading || !rows.some(r => r.name.trim())} className="mt-6 w-full py-3.5 bg-[#f0a500] text-[#1a1a2e] rounded-xl font-bold text-base hover:bg-[#fcc419] hover:shadow-lg transition disabled:opacity-50">{loading ? "Создаём..." : "Далее: точка доставки →"}</button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="bg-white rounded-2xl border border-[#e2e8f0] shadow-sm overflow-hidden">
          <div className="p-6 border-b border-[#e2e8f0] bg-[#f5f7fa]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#f0a500]/10 flex items-center justify-center"><IconMapPin className="w-5 h-5 text-[#f0a500]" /></div>
              <div><p className="font-semibold text-[#1a1a2e]">Шаг 2: Точка доставки</p><p className="text-xs text-[#64748b]">Кликните на карту чтобы указать адрес доставки</p></div>
            </div>
          </div>
          <div className="h-[450px] relative">
            <DeliveryMap onSelect={(lat: number, lon: number, addr: string) => { setDeliveryLat(lat); setDeliveryLon(lon); setDeliveryAddr(addr); }} />
          </div>
          {deliveryLat && deliveryLon && (
            <div className="p-4 bg-green-50 border-t border-green-200 flex items-center gap-3">
              <IconMapPin className="w-5 h-5 text-green-600" />
              <div><p className="text-sm font-medium text-green-800">{deliveryAddr || deliveryLat.toFixed(5) + ", " + deliveryLon.toFixed(5)}</p><p className="text-xs text-green-600">Координаты: {deliveryLat.toFixed(5)}, {deliveryLon.toFixed(5)}</p></div>
            </div>
          )}
          <div className="p-6 flex gap-3">
            <button onClick={() => setStep(1)} className="px-5 py-3 border border-[#e2e8f0] rounded-xl text-sm font-medium hover:bg-[#f5f7fa] transition">← Назад к материалам</button>
            <button onClick={handleStep2Next} disabled={loading || !deliveryLat} className="flex-1 py-3.5 bg-[#f0a500] text-[#1a1a2e] rounded-xl font-bold text-base hover:bg-[#fcc419] hover:shadow-lg transition disabled:opacity-50">{loading ? "Подбираем поставщиков..." : "Подобрать поставщиков →"}</button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div>
          {sentCount > 0 ? (
            <div className="bg-white rounded-2xl border border-[#e2e8f0] shadow-sm p-12 text-center">
              <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4"><IconTruck className="w-8 h-8 text-green-600" /></div>
              <h2 className="text-2xl font-bold text-[#1a1a2e] mb-2">Запросы отправлены!</h2>
              <p className="text-[#64748b] mb-6">РФК отправлены {sentCount} поставщикам. Ожидайте коммерческие предложения.</p>
              <button onClick={() => router.push("/lk/requests/" + requestId)} className="px-6 py-3 bg-[#f0a500] text-[#1a1a2e] rounded-xl font-bold hover:bg-[#fcc419] transition">Перейти к заявке</button>
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-[#e2e8f0] shadow-sm overflow-hidden">
              <div className="p-6 border-b border-[#e2e8f0] bg-[#f5f7fa]">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[#27ae60]/10 flex items-center justify-center"><IconTruck className="w-5 h-5 text-[#27ae60]" /></div>
                  <div><p className="font-semibold text-[#1a1a2e]">Шаг 3: Выбор поставщиков</p><p className="text-xs text-[#64748b]">Найдено {suppliers.length} поставщиков.
              <select value={sourceFilter} onChange={e => setSourceFilter(e.target.value)}
                className="ml-2 px-2 py-0.5 border rounded text-xs">
                <option value="all">Все источники</option>
                <option value="seed">Из базы</option>
                <option value="llm">AI-поиск</option>
                <option value="web">Веб-поиск</option>
                <option value="2gis">2GIS</option>
                <option value="dadata">DaData</option>
              </select> Отметьте кому отправить запрос КП. <select value={supplierLimit} onChange={e => setSupplierLimit(Number(e.target.value))} className="ml-2 px-2 py-0.5 border rounded text-xs">{[5,10,15,20].map(n => <option key={n} value={n}>{n}</option>)}</select> показывать</p></div>
                </div>
              </div>
              <div className="p-6">
                {deliveryLat && deliveryLon && suppliers.length > 0 && (
            <div className="h-[300px] mb-4 rounded-xl overflow-hidden border border-[#e2e8f0]">
              <SupplierMap suppliers={suppliers as any} centerLat={deliveryLat} centerLon={deliveryLon} />
            </div>
          )}
          {suppliers.length === 0 ? (
                  <div className="text-center py-8 text-[#64748b]">Поставщики не найдены. Попробуйте изменить точку доставки.</div>
                ) : (
                  <table className="w-full text-sm">
                    <thead><tr className="border-b border-[#e2e8f0] text-left">
                      <th className="py-2 w-10"><input type="checkbox" onChange={e => { if (e.target.checked) setSelectedSuppliers(new Set(suppliers.map(s => s.supplier_id))); else setSelectedSuppliers(new Set()); }} checked={selectedSuppliers.size === suppliers.length && suppliers.length > 0} className="w-4 h-4 accent-[#f0a500]" /></th>
                      <th className="py-2 font-semibold text-[#64748b]">Поставщик</th>
                      <th className="py-2 font-semibold text-[#64748b] text-center">Баллы</th>
                      <th className="py-2 font-semibold text-[#64748b] text-center">Категории</th>
                      <th className="py-2 font-semibold text-[#64748b] text-center">Расст.</th>
                      <th className="py-2 font-semibold text-[#64748b]">Город</th>
                    </tr></thead>
                    <tbody>
                      {suppliers.filter(s => sourceFilter === "all" || s.source === sourceFilter).map(s => (
                        <tr key={s.supplier_id} className={"border-b border-[#f5f7fa] cursor-pointer hover:bg-[#f8fafc] " + (selectedSuppliers.has(s.supplier_id) ? "bg-amber-50" : "")} onClick={() => toggleSupplier(s.supplier_id)}>
                          <td className="py-2"><input type="checkbox" checked={selectedSuppliers.has(s.supplier_id)} onChange={() => toggleSupplier(s.supplier_id)} className="w-4 h-4 accent-[#f0a500]" /></td>
                          <td className="py-2"><p className="font-medium text-[#1a1a2e]">{s.name}</p><p className="text-xs text-[#94a3b8]">{s.email}</p></td>
                          <td className="py-2 text-center"><span className="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-100 text-amber-800 rounded-full text-xs font-bold">{s.total_score.toFixed(0)}</span></td>
                          <td className="py-2 text-center text-xs text-[#64748b]">{s.matched_count}/{s.total_categories}</td>
                          <td className="py-2 text-center text-xs text-[#64748b]">{s.distance_km ? s.distance_km + " км" : "—"}</td>
                          <td className="py-2 text-xs text-[#64748b]">{s.city || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
                <div className="mt-6 flex gap-3">
                  <button onClick={() => setStep(2)} className="px-5 py-3 border border-[#e2e8f0] rounded-xl text-sm font-medium hover:bg-[#f5f7fa] transition">← Назад к карте</button>
                  <button onClick={handleSendRfq} disabled={loading || selectedSuppliers.size === 0} className="flex-1 py-3.5 bg-[#27ae60] text-white rounded-xl font-bold text-base hover:bg-[#219a52] transition disabled:opacity-50">{loading ? "Отправляем..." : "Отправить запрос КП (" + selectedSuppliers.size + ")"}</button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

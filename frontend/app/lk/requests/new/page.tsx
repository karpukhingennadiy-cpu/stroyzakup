"use client";
import { useState, useEffect, Fragment } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { createRequest, matchSuppliers, sendRfq, api, geocodeAddress } from "@/lib/api";
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

interface ScoreBreakdown {
  category: string;
  distance: string;
  rating: string;
  completeness: string;
  manufacturer_bonus: string;
  material_type: string;
  product_match: string;
  total: number;
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
  material_type_score: number;
  product_match_score: number;
  matched_count: number;
  total_categories: number;
  matched_categories: string[];
  supplier_type?: string;
  moderation_status?: string;
  source?: string;
  manufacturer_bonus?: number;
  score_breakdown?: ScoreBreakdown;
}

interface ParsedItem {
  id: number;
  name: string;
  spec: string;
  confidence: number;
  needs_clarification: boolean;
  clarification_question: string;
}

const DRAFT_KEY = "minitender_request_draft";
const STAGE_LABELS: Record<string, string> = {
  create: "Создаём заявку...",
  parse: "ИИ анализирует материалы: извлекаем позиции, определяем категории и единицы измерения...",
  match: "Подбираем поставщиков: скоринг по категориям, расстоянию и ассортименту...",
  send: "Отправляем запросы КП поставщикам...",
};

const UNITS = ["m2", "m3", "kg", "ton", "bag", "piece", "pack", "roll", "pog_m", "liter", "sht"];

export default function NewRequestPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState<string>("");
  const [error, setError] = useState("");

  const [rows, setRows] = useState<MaterialRow[]>([
    { id: 1, name: "", specs: "", quantity: "", unit: "m2" },
  ]);
  const [comment, setComment] = useState("");
  const [draftRestored, setDraftRestored] = useState(false);

  // B6: draft in localStorage — protection against accidental refresh
  useEffect(() => {
    try {
      const saved = localStorage.getItem(DRAFT_KEY);
      if (saved) {
        const draft = JSON.parse(saved);
        if (draft.rows?.length && draft.rows.some((r: MaterialRow) => r.name?.trim())) {
          setRows(draft.rows);
          setComment(draft.comment || "");
          setDraftRestored(true);
        }
      }
    } catch { /* ignore broken drafts */ }
  }, []);

  useEffect(() => {
    const hasContent = rows.some(r => r.name.trim()) || comment.trim();
    try {
      if (hasContent) localStorage.setItem(DRAFT_KEY, JSON.stringify({ rows, comment }));
      else localStorage.removeItem(DRAFT_KEY);
    } catch { /* storage full/blocked — non-fatal */ }
  }, [rows, comment]);
  const addRow = () => setRows([...rows, { id: Date.now(), name: "", specs: "", quantity: "", unit: "m2" }]);
  const removeRow = (id: number) => rows.length > 1 && setRows(rows.filter(r => r.id !== id));
  const updateRow = (id: number, field: keyof MaterialRow, value: string) => {
    setRows(rows.map(r => r.id === id ? { ...r, [field]: value } : r));
  };

  const [deliveryLat, setDeliveryLat] = useState<number | null>(null);
  const [deliveryLon, setDeliveryLon] = useState<number | null>(null);
  const [deliveryAddr, setDeliveryAddr] = useState("");
  const [cityInput, setCityInput] = useState("");
  const [cityLoading, setCityLoading] = useState(false);
  const [requestId, setRequestId] = useState<number | null>(null);
  const [suppliers, setSuppliers] = useState<SupplierMatch[]>([]);
  const [selectedSuppliers, setSelectedSuppliers] = useState<Set<number>>(new Set());
  const [sentCount, setSentCount] = useState(0);
  const [discoveredCount, setDiscoveredCount] = useState(0);
  const [clarifications, setClarifications] = useState<ParsedItem[]>([]);
  const [clarifyAnswers, setClarifyAnswers] = useState<Record<number, string>>({});
  const [sourceFilter, setSourceFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [supplierLimit, setSupplierLimit] = useState(10);
  const [expandedSupplier, setExpandedSupplier] = useState<number | null>(null);

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
      setStage("create");
      const rawText = buildRawText();
      const req = await createRequest(rawText, comment || undefined, undefined, undefined);
      setRequestId(req.id);
      setStage("parse");
      try {
        const parsed = await api("/requests/" + req.id + "/parse/", { method: "POST" });
        // B6: show LLM follow-up questions for low-confidence items
        const unclear = (parsed.items || []).filter(
          (i: ParsedItem) => i.clarification_question || i.needs_clarification
        );
        setClarifications(unclear);
      } catch (e) {
        console.warn("Parse failed, continuing anyway:", e);
      }
      setStep(2);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); setStage(""); }
  };

  // B6: answer an LLM clarification question — append to item spec
  const handleClarify = async (item: ParsedItem) => {
    const answer = (clarifyAnswers[item.id] || "").trim();
    if (!answer || !requestId) return;
    try {
      await api("/requests/" + requestId + "/update_item/", {
        method: "POST",
        body: JSON.stringify({
          item_id: item.id,
          spec: (item.spec ? item.spec + "; " : "") + answer,
          is_confirmed: true,
        }),
      });
      setClarifications(clarifications.filter(c => c.id !== item.id));
    } catch (e: any) { setError("Не удалось сохранить уточнение: " + e.message); }
  };

  // Fallback: geocode city name via backend API
  const handleCitySearch = async () => {
    if (!cityInput.trim()) return;
    setCityLoading(true);
    setError("");
    try {
      const result = await geocodeAddress(cityInput.trim());
      if (result && result.latitude && result.longitude) {
        setDeliveryLat(result.latitude);
        setDeliveryLon(result.longitude);
        setDeliveryAddr(result.address || cityInput.trim());
      } else {
        setError("Город не найден. Попробуйте указать область (например: Пенза, Пензенская обл.)");
      }
    } catch (e: any) {
      setError("Ошибка геокодирования: " + e.message);
    } finally {
      setCityLoading(false);
    }
  };

  const handleStep2Next = async () => {
    if (!deliveryLat || !deliveryLon) { setError("Укажите точку доставки на карте или введите город"); return; }
    if (!requestId) return;
    setError("");
    setLoading(true);
    try {
      await api("/requests/" + requestId + "/", {
        method: "PATCH",
        body: JSON.stringify({ delivery_address: deliveryAddr, latitude: deliveryLat, longitude: deliveryLon }),
      });
      setStage("match");
      const result = await matchSuppliers(requestId, supplierLimit);
      setSuppliers(result.suppliers || []);
      setDiscoveredCount(result.discovered || 0);
      setStep(3);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); setStage(""); }
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
      setStage("send");
      const result = await sendRfq(requestId, Array.from(selectedSuppliers));
      setSentCount(result.sent || 0);
      // Draft no longer needed once the tender is launched
      try { localStorage.removeItem(DRAFT_KEY); } catch { /* non-fatal */ }
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); setStage(""); }
  };

  const filteredSuppliers = suppliers.filter(s => {
    const sourceOk = sourceFilter === "all" || s.source === sourceFilter;
    const typeOk = typeFilter === "all" || s.supplier_type === typeFilter;
    return sourceOk && typeOk;
  });

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

      {loading && stage && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-[#1e3a5f] border-t-transparent rounded-full animate-spin shrink-0" />
          <p className="text-sm text-[#1e3a5f] font-medium">{STAGE_LABELS[stage] || stage}</p>
        </div>
      )}

      {draftRestored && step === 1 && !loading && (
        <div className="mb-6 p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl text-sm flex items-center justify-between">
          <span>Черновик заявки восстановлен из автосохранения.</span>
          <button onClick={() => { setRows([{ id: 1, name: "", specs: "", quantity: "", unit: "m2" }]); setComment(""); setDraftRestored(false); try { localStorage.removeItem(DRAFT_KEY); } catch {} }} className="text-xs font-bold hover:underline ml-4 shrink-0">Очистить</button>
        </div>
      )}

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
        <div>
        {clarifications.length > 0 && (
          <div className="mb-6 bg-white rounded-2xl border border-amber-300 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-amber-200 bg-amber-50">
              <p className="font-semibold text-[#1a1a2e] text-sm">ИИ просит уточнить ({clarifications.length})</p>
              <p className="text-xs text-[#64748b]">По этим позициям не хватает данных для точной оценки — ответьте, и поставщики получат полную спецификацию</p>
            </div>
            <div className="p-4 space-y-3">
              {clarifications.map(item => (
                <div key={item.id} className="flex flex-col sm:flex-row sm:items-center gap-2 text-sm">
                  <div className="flex-1">
                    <p className="font-medium text-[#1a1a2e]">{item.name}</p>
                    <p className="text-xs text-[#64748b]">{item.clarification_question || "Уточните характеристики"}</p>
                  </div>
                  <div className="flex gap-2 sm:w-1/2">
                    <input
                      value={clarifyAnswers[item.id] || ""}
                      onChange={e => setClarifyAnswers({ ...clarifyAnswers, [item.id]: e.target.value })}
                      onKeyDown={e => e.key === 'Enter' && handleClarify(item)}
                      placeholder="Ваш ответ (например: сосна, 25×150 мм)"
                      className="flex-1 px-3 py-2 bg-[#f5f7fa] border border-[#e2e8f0] rounded-lg text-sm focus:border-[#1e3a5f] outline-none"
                    />
                    <button onClick={() => handleClarify(item)} disabled={!(clarifyAnswers[item.id] || "").trim()} className="px-3 py-2 bg-[#1e3a5f] text-white rounded-lg text-xs font-bold hover:bg-[#2a4a7f] transition disabled:opacity-50">OK</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        <div className="bg-white rounded-2xl border border-[#e2e8f0] shadow-sm overflow-hidden">
          <div className="p-6 border-b border-[#e2e8f0] bg-[#f5f7fa]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#f0a500]/10 flex items-center justify-center"><IconMapPin className="w-5 h-5 text-[#f0a500]" /></div>
              <div><p className="font-semibold text-[#1a1a2e]">Шаг 2: Точка доставки</p><p className="text-xs text-[#64748b]">Кликните на карту или введите город</p></div>
            </div>
          </div>
          <div className="h-[450px] relative">
            <DeliveryMap onSelect={(lat: number, lon: number, addr: string) => { setDeliveryLat(lat); setDeliveryLon(lon); setDeliveryAddr(addr); }} />
          </div>
          {/* Fallback: text city input */}
          <div className="p-4 border-t border-[#e2e8f0] bg-[#f8fafc]">
            <p className="text-xs text-[#64748b] mb-2">Или введите город вручную:</p>
            <div className="flex gap-2">
              <input
                value={cityInput}
                onChange={e => setCityInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleCitySearch()}
                placeholder="Например: Подольск, Московская обл."
                className="flex-1 px-3 py-2 bg-white border border-[#e2e8f0] rounded-lg text-sm focus:border-[#1e3a5f] outline-none"
              />
              <button
                onClick={handleCitySearch}
                disabled={cityLoading || !cityInput.trim()}
                className="px-4 py-2 bg-[#1e3a5f] text-white rounded-lg text-sm font-medium hover:bg-[#2a4a7f] transition disabled:opacity-50"
              >
                {cityLoading ? "..." : "Найти"}
              </button>
            </div>
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
        </div>
      )}

      {step === 3 && (
        <div>
          {sentCount > 0 ? (
            <div className="bg-white rounded-2xl border border-[#e2e8f0] shadow-sm p-12 text-center">
              <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4"><IconTruck className="w-8 h-8 text-green-600" /></div>
              <h2 className="text-2xl font-bold text-[#1a1a2e] mb-2">Тендер запущен!</h2>
              <p className="text-[#64748b] mb-6">РФК отправлены {sentCount} поставщикам. Ожидайте коммерческие предложения.</p>
              <button onClick={() => router.push("/lk/requests/" + requestId)} className="px-6 py-3 bg-[#f0a500] text-[#1a1a2e] rounded-xl font-bold hover:bg-[#fcc419] transition">Перейти к заявке</button>
            </div>
          ) : (
            <div>
            {discoveredCount > 0 && (
              <div className="mb-4 p-3 bg-violet-50 border border-violet-200 text-violet-800 rounded-xl text-sm">
                Найдено {discoveredCount} новых поставщиков из интернета — они добавлены в базу и участвуют в подборе.
              </div>
            )}
            <div className="bg-white rounded-2xl border border-[#e2e8f0] shadow-sm overflow-hidden">
              <div className="p-6 border-b border-[#e2e8f0] bg-[#f5f7fa]">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[#27ae60]/10 flex items-center justify-center"><IconTruck className="w-5 h-5 text-[#27ae60]" /></div>
                  <div><p className="font-semibold text-[#1a1a2e]">Шаг 3: Выбор поставщиков</p><p className="text-xs text-[#64748b]">Найдено {filteredSuppliers.length} поставщиков.
              <select value={sourceFilter} onChange={e => setSourceFilter(e.target.value)}
                className="ml-2 px-2 py-0.5 border rounded text-xs">
                <option value="all">Все источники</option>
                <option value="seed">Из базы</option>
                <option value="llm">AI-поиск</option>
                <option value="web">Веб-поиск</option>
                <option value="2gis">2GIS</option>
                <option value="dadata">DaData</option>
              </select>
              <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)}
                className="ml-2 px-2 py-0.5 border rounded text-xs">
                <option value="all">Все типы</option>
                <option value="manufacturer">Только производители</option>
                <option value="dealer">Только дилеры</option>
                <option value="unknown">Неизвестно</option>
              </select>
              Отметьте кому отправить запрос КП. <select value={supplierLimit} onChange={e => setSupplierLimit(Number(e.target.value))} className="ml-2 px-2 py-0.5 border rounded text-xs">{[5,10,15,20].map(n => <option key={n} value={n}>{n}</option>)}</select> показывать</p></div>
                </div>
              </div>
              <div className="p-6">
                {deliveryLat && deliveryLon && filteredSuppliers.length > 0 && (
            <div className="h-[300px] mb-4 rounded-xl overflow-hidden border border-[#e2e8f0]">
              <SupplierMap suppliers={filteredSuppliers as any} centerLat={deliveryLat} centerLon={deliveryLon} />
            </div>
          )}
          {filteredSuppliers.length === 0 ? (
                  <div className="text-center py-8 text-[#64748b]">Поставщики не найдены. Попробуйте изменить точку доставки или снять фильтры.</div>
                ) : (
                  <table className="w-full text-sm">
                    <thead><tr className="border-b border-[#e2e8f0] text-left">
                      <th className="py-2 w-10"><input type="checkbox" onChange={e => { if (e.target.checked) setSelectedSuppliers(new Set(filteredSuppliers.map(s => s.supplier_id))); else setSelectedSuppliers(new Set()); }} checked={selectedSuppliers.size === filteredSuppliers.length && filteredSuppliers.length > 0} className="w-4 h-4 accent-[#f0a500]" /></th>
                      <th className="py-2 font-semibold text-[#64748b]">Поставщик</th>
                      <th className="py-2 font-semibold text-[#64748b] text-center">Баллы</th>
                      <th className="py-2 font-semibold text-[#64748b] text-center">Категории</th>
                      <th className="py-2 font-semibold text-[#64748b] text-center">Расст.</th>
                      <th className="py-2 font-semibold text-[#64748b]">Город</th>
                    </tr></thead>
                    <tbody>
                      {filteredSuppliers.map(s => (
                        <Fragment key={s.supplier_id}>
                        <tr className={"border-b border-[#f5f7fa] cursor-pointer hover:bg-[#f8fafc] " + (selectedSuppliers.has(s.supplier_id) ? "bg-amber-50" : "")} onClick={() => toggleSupplier(s.supplier_id)}>
                          <td className="py-2"><input type="checkbox" checked={selectedSuppliers.has(s.supplier_id)} onChange={() => toggleSupplier(s.supplier_id)} className="w-4 h-4 accent-[#f0a500]" /></td>
                          <td className="py-2"><p className="font-medium text-[#1a1a2e] flex items-center gap-2 flex-wrap">{s.name}{s.supplier_type === "manufacturer" && <span className="inline-flex items-center px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px] font-bold">Производитель</span>}{s.supplier_type === "dealer" && <span className="inline-flex items-center px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded text-[10px] font-bold">Дилер</span>}{s.moderation_status === "unverified" && <span className="inline-flex items-center px-1.5 py-0.5 bg-orange-100 text-orange-700 rounded text-[10px] font-bold" title="Поставщик ещё не прошёл модерацию">На проверке</span>}</p><p className="text-xs text-[#94a3b8]">{s.email}</p></td>
                          <td className="py-2 text-center">
                            <button onClick={(e) => { e.stopPropagation(); setExpandedSupplier(expandedSupplier === s.supplier_id ? null : s.supplier_id); }} className="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-100 text-amber-800 rounded-full text-xs font-bold hover:bg-amber-200 transition">
                              {s.total_score.toFixed(0)}
                              <span className="text-[8px]">{expandedSupplier === s.supplier_id ? "▲" : "▼"}</span>
                            </button>
                          </td>
                          <td className="py-2 text-center text-xs text-[#64748b]">{s.matched_count}/{s.total_categories}</td>
                          <td className="py-2 text-center text-xs text-[#64748b]">{s.distance_km ? s.distance_km + " км" : "—"}</td>
                          <td className="py-2 text-xs text-[#64748b]">{s.city || "—"}</td>
                        </tr>
                        {expandedSupplier === s.supplier_id && s.score_breakdown && (
                          <tr className="bg-[#f8fafc]">
                            <td colSpan={6} className="px-4 py-3 text-xs">
                              <div className="grid grid-cols-2 gap-2 text-[#64748b]">
                                <div><span className="font-semibold">Категории:</span> {s.score_breakdown.category}</div>
                                <div><span className="font-semibold">Расстояние:</span> {s.score_breakdown.distance}</div>
                                <div><span className="font-semibold">Рейтинг:</span> {s.score_breakdown.rating}</div>
                                <div><span className="font-semibold">Полнота:</span> {s.score_breakdown.completeness}</div>
                                <div><span className="font-semibold">Производитель:</span> {s.score_breakdown.manufacturer_bonus}</div>
                                <div><span className="font-semibold">Тип материала:</span> {s.score_breakdown.material_type}</div>
                                <div><span className="font-semibold">Ассортимент:</span> {s.score_breakdown.product_match}</div>
                                <div className="col-span-2 font-bold text-[#1a1a2e]">Итого: {s.score_breakdown.total} баллов</div>
                              </div>
                            </td>
                          </tr>
                        )}
                        </Fragment>
                      ))}
                    </tbody>
                  </table>
                )}
                <div className="mt-6 flex gap-3">
                  <button onClick={() => setStep(2)} className="px-5 py-3 border border-[#e2e8f0] rounded-xl text-sm font-medium hover:bg-[#f5f7fa] transition">← Назад к карте</button>
                  <button onClick={handleSendRfq} disabled={loading || selectedSuppliers.size === 0} className="flex-1 py-3.5 bg-[#27ae60] text-white rounded-xl font-bold text-base hover:bg-[#219a52] transition disabled:opacity-50">{loading ? "Отправляем..." : "Начать тендер (" + selectedSuppliers.size + ")"}</button>
                </div>
              </div>
            </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

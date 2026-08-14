"use client";
import { useState, useEffect, Fragment } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { createRequest, matchSuppliers, sendRfq, api, geocodeAddress } from "@/lib/api";
const SupplierMap = dynamic(() => import("./SupplierMap"), {
  ssr: false,
  loading: () => <div className="w-full h-full bg-[var(--fill-1)] animate-pulse rounded-[var(--radius-lg)]" />,
});
import { IconPlus, IconMapPin, IconTile, IconTruck } from "@/components/icons";
import { Button, Card, Badge } from "@/components/ui";

const DeliveryMap = dynamic(() => import("./DeliveryMap"), {
  ssr: false,
  loading: () => <div className="w-full h-full bg-[var(--fill-1)] animate-pulse rounded-[var(--radius-lg)]" />,
});

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
  has_email?: boolean;
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
const STEP_LABELS = ["Материалы", "Доставка", "Поставщики"];

// B2: poll request status while a Celery task is running (202 mode)
async function pollUntilDone(requestId: number, pendingStatuses: string[], timeoutSec: number): Promise<any> {
  const deadline = Date.now() + timeoutSec * 1000;
  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, 2000));
    const req = await api("/requests/" + requestId + "/");
    if (!pendingStatuses.includes(req.status)) return req;
  }
  throw new Error("Превышено время ожидания обработки");
}

/** Индикатор шагов мастера — a11y: ol + aria-current */
function Stepper({ step }: { step: number }) {
  return (
    <ol className="flex flex-wrap gap-x-6 gap-y-2 mt-4" aria-label="Шаги создания заявки">
      {STEP_LABELS.map((label, i) => {
        const n = i + 1;
        const active = step >= n;
        return (
          <li key={n} aria-current={step === n ? "step" : undefined}
            className={"flex items-center gap-2 " + (active ? "text-label-1" : "text-label-4")}>
            <span className={"w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold " +
              (active ? "bg-[var(--label-primary)] text-[var(--bg-primary)]" : "bg-[var(--fill-2)] text-label-4")}>
              {n}
            </span>
            <span className="text-sm font-medium">{label}</span>
            {n < 3 && <span className="text-label-4 ml-2" aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5"><path d="m9 18 6-6-6-6"/></svg></span>}
          </li>
        );
      })}
    </ol>
  );
}

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
        let parsed = await api("/requests/" + req.id + "/parse/", { method: "POST" });
        // B2: async mode (202 + task_id) — poll until parsing finishes
        if (parsed.status === "parsing" && parsed.task_id) {
          parsed = await pollUntilDone(req.id, ["parsing"], 90);
        }
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
      let result = await matchSuppliers(requestId, supplierLimit);
      // B2: async mode (202 + task_id) — poll until matching finishes
      if (result.status === "matching" && result.task_id) {
        const done = await pollUntilDone(requestId, ["matching"], 120);
        result = { ...result, ...(done.match_results || {}), status: done.status };
      }
      setSuppliers(result.suppliers || []);
      setDiscoveredCount(result.discovered || 0);
      setStep(3);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); setStage(""); }
  };

  const toggleSupplier = (id: number) => {
    const s = suppliers.find((x) => x.supplier_id === id);
    if (s && !s.has_email) {
      setError("У этого поставщика нет email — запрос КП отправить нельзя");
      return;
    }
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
      // Backend returns {status, results[]} — count actual sends and skips
      const results = result.results || [];
      const sent = results.filter((r: any) => r.status === "sent").length;
      const skipped = results.filter((r: any) => r.status === "skipped" || r.status === "needs_review").length;
      setSentCount(sent);
      if (sent === 0) {
        setError(skipped > 0
          ? `Письма не отправлены: у ${skipped} поставщик(ов) нет валидного email или письмо на модерации`
          : "Письма не отправлены");
      }
      // Draft no longer needed once the tender is launched
      if (sent > 0) { try { localStorage.removeItem(DRAFT_KEY); } catch { /* non-fatal */ } }
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
        <h1 className="text-xl font-semibold text-label-1">Новая заявка</h1>
        <Stepper step={step} />
      </div>

      {error && (
        <div className="mb-6 p-4 bg-[var(--danger-soft)] border border-[var(--separator)] text-[var(--danger)] rounded-[var(--radius-lg)] text-sm" role="alert">
          {error}
        </div>
      )}

      {loading && stage && (
        <div className="mb-6 p-4 bg-[var(--accent-soft)] border border-[var(--separator)] rounded-[var(--radius-lg)] flex items-center gap-3" role="status">
          <div className="w-5 h-5 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin shrink-0" aria-hidden="true" />
          <p className="text-sm text-[var(--accent)] font-medium">{STAGE_LABELS[stage] || stage}</p>
        </div>
      )}

      {draftRestored && step === 1 && !loading && (
        <div className="mb-6 p-3 bg-[var(--warning-soft)] border border-[var(--separator)] text-label-1 rounded-[var(--radius-lg)] text-sm flex items-center justify-between gap-3" role="status">
          <span>Черновик заявки восстановлен из автосохранения.</span>
          <Button size={26} variant="outline" onClick={() => { setRows([{ id: 1, name: "", specs: "", quantity: "", unit: "m2" }]); setComment(""); setDraftRestored(false); try { localStorage.removeItem(DRAFT_KEY); } catch {} }}>
            Очистить
          </Button>
        </div>
      )}

      {step === 1 && (
        <Card
          title="Шаг 1: Список материалов"
          subtitle="Заполните таблицу — каждый товар отдельной строкой"
          icon={<IconTile className="w-5 h-5" />}
        >
          {/* Desktop: таблица */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-separator text-left">
                <th scope="col" className="py-2 pr-2 font-medium text-label-3 text-xs w-1/3">Материал</th>
                <th scope="col" className="py-2 px-2 font-medium text-label-3 text-xs w-1/3">Габариты / Спецификация</th>
                <th scope="col" className="py-2 px-2 font-medium text-label-3 text-xs w-1/6">Кол-во</th>
                <th scope="col" className="py-2 px-2 font-medium text-label-3 text-xs w-20">Ед.</th>
                <th scope="col" className="py-2 w-10"><span className="sr-only">Действия</span></th>
              </tr></thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id} className="border-b border-[var(--fill-1)]">
                    <td className="py-1.5 pr-2">
                      <label htmlFor={"mat-name-" + row.id} className="sr-only">Материал, строка</label>
                      <input id={"mat-name-" + row.id} value={row.name} onChange={e => updateRow(row.id, "name", e.target.value)} placeholder="Керамогранит, Доска, Бетон..." className="field-input" />
                    </td>
                    <td className="py-1.5 px-2">
                      <label htmlFor={"mat-specs-" + row.id} className="sr-only">Спецификация</label>
                      <input id={"mat-specs-" + row.id} value={row.specs} onChange={e => updateRow(row.id, "specs", e.target.value)} placeholder="600x600 серый, 25x150x6000, М300..." className="field-input" />
                    </td>
                    <td className="py-1.5 px-2">
                      <label htmlFor={"mat-qty-" + row.id} className="sr-only">Количество</label>
                      <input id={"mat-qty-" + row.id} value={row.quantity} onChange={e => updateRow(row.id, "quantity", e.target.value)} type="number" min="0" step="any" placeholder="150" className="field-input" />
                    </td>
                    <td className="py-1.5 px-2">
                      <label htmlFor={"mat-unit-" + row.id} className="sr-only">Единица измерения</label>
                      <select id={"mat-unit-" + row.id} value={row.unit} onChange={e => updateRow(row.id, "unit", e.target.value)} className="field-input">{UNITS.map(u => <option key={u} value={u}>{u}</option>)}</select>
                    </td>
                    <td className="py-1.5 text-center">
                      {rows.length > 1 && (
                        <button type="button" onClick={() => removeRow(row.id)} aria-label="Удалить строку"
                          className="w-8 h-8 inline-flex items-center justify-center rounded-[var(--radius-sm)] text-label-4 hover:text-[var(--danger)] hover:bg-[var(--danger-soft)] transition-colors"><IconPlus className="w-3.5 h-3.5 rotate-45" /></button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile (320px+): карточки вместо таблицы */}
          <div className="md:hidden space-y-4">
            {rows.map((row, i) => (
              <fieldset key={row.id} className="rounded-[var(--radius-md)] border border-separator p-3 space-y-2.5">
                <legend className="text-xs text-label-3 px-1">Позиция {i + 1}</legend>
                <div>
                  <label htmlFor={"m-name-" + row.id} className="block text-xs font-medium text-label-2 mb-1">Материал</label>
                  <input id={"m-name-" + row.id} value={row.name} onChange={e => updateRow(row.id, "name", e.target.value)} placeholder="Керамогранит, Доска, Бетон..." className="field-input" />
                </div>
                <div>
                  <label htmlFor={"m-specs-" + row.id} className="block text-xs font-medium text-label-2 mb-1">Габариты / Спецификация</label>
                  <input id={"m-specs-" + row.id} value={row.specs} onChange={e => updateRow(row.id, "specs", e.target.value)} placeholder="600x600 серый, М300..." className="field-input" />
                </div>
                <div className="flex gap-2">
                  <div className="flex-1">
                    <label htmlFor={"m-qty-" + row.id} className="block text-xs font-medium text-label-2 mb-1">Кол-во</label>
                    <input id={"m-qty-" + row.id} value={row.quantity} onChange={e => updateRow(row.id, "quantity", e.target.value)} type="number" min="0" step="any" placeholder="150" className="field-input" />
                  </div>
                  <div className="w-24">
                    <label htmlFor={"m-unit-" + row.id} className="block text-xs font-medium text-label-2 mb-1">Ед.</label>
                    <select id={"m-unit-" + row.id} value={row.unit} onChange={e => updateRow(row.id, "unit", e.target.value)} className="field-input">{UNITS.map(u => <option key={u} value={u}>{u}</option>)}</select>
                  </div>
                  {rows.length > 1 && (
                    <div className="flex items-end">
                      <button type="button" onClick={() => removeRow(row.id)} aria-label={"Удалить позицию " + (i + 1)}
                        className="w-10 h-10 inline-flex items-center justify-center rounded-[var(--radius-sm)] text-label-4 hover:text-[var(--danger)] hover:bg-[var(--danger-soft)] transition-colors"><IconPlus className="w-3.5 h-3.5 rotate-45" /></button>
                    </div>
                  )}
                </div>
              </fieldset>
            ))}
          </div>

          <Button variant="outline" size={32} onClick={addRow} leftIcon={<IconPlus className="w-[18px] h-[18px]" />} className="mt-3">
            Добавить строку
          </Button>
          <div className="mt-4">
            <label htmlFor="request-comment" className="sr-only">Комментарий к заявке</label>
            <input id="request-comment" value={comment} onChange={e => setComment(e.target.value)} placeholder="Комментарий к заявке (необязательно)" className="field-input" />
          </div>
          <Button
            variant="primary" size={44} className="mt-6 w-full"
            onClick={handleStep1Next}
            loading={loading}
            disabled={!rows.some(r => r.name.trim())}
          >
            {loading ? "Создаём..." : "Далее: точка доставки"}
          </Button>
        </Card>
      )}

      {step === 2 && (
        <div>
          {clarifications.length > 0 && (
            <div className="mb-6 surface-card overflow-hidden border-[var(--warning)]">
              <div className="p-4 border-b border-separator bg-[var(--warning-soft)]">
                <p className="font-medium text-label-1 text-sm">ИИ просит уточнить ({clarifications.length})</p>
                <p className="text-xs text-label-3 mt-0.5">По этим позициям не хватает данных для точной оценки — ответьте, и поставщики получат полную спецификацию</p>
              </div>
              <div className="p-4 space-y-3">
                {clarifications.map(item => (
                  <div key={item.id} className="flex flex-col sm:flex-row sm:items-center gap-2 text-sm">
                    <div className="flex-1">
                      <p className="font-medium text-label-1">{item.name}</p>
                      <p className="text-xs text-label-3">{item.clarification_question || "Уточните характеристики"}</p>
                    </div>
                    <div className="flex gap-2 sm:w-1/2">
                      <label htmlFor={"clarify-" + item.id} className="sr-only">Ответ на уточнение по позиции {item.name}</label>
                      <input
                        id={"clarify-" + item.id}
                        value={clarifyAnswers[item.id] || ""}
                        onChange={e => setClarifyAnswers({ ...clarifyAnswers, [item.id]: e.target.value })}
                        onKeyDown={e => e.key === 'Enter' && handleClarify(item)}
                        placeholder="Ваш ответ (например: сосна, 25×150 мм)"
                        className="field-input flex-1"
                      />
                      <Button size={32} variant="primary" onClick={() => handleClarify(item)} disabled={!(clarifyAnswers[item.id] || "").trim()}>OK</Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          <Card
            title="Шаг 2: Точка доставки"
            subtitle="Кликните на карту или введите город"
            icon={<IconMapPin className="w-5 h-5" />}
            padding={false}
          >
            <div className="h-[300px] sm:h-[450px] relative">
              <DeliveryMap onSelect={(lat: number, lon: number, addr: string) => { setDeliveryLat(lat); setDeliveryLon(lon); setDeliveryAddr(addr); }} />
            </div>
            {/* Fallback: text city input */}
            <div className="p-4 border-t border-separator bg-[var(--fill-1)]">
              <label htmlFor="city-input" className="block text-xs text-label-3 mb-2">Или введите город вручную:</label>
              <div className="flex gap-2">
                <input
                  id="city-input"
                  value={cityInput}
                  onChange={e => setCityInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleCitySearch()}
                  placeholder="Например: Подольск, Московская обл."
                  className="field-input flex-1 bg-[var(--bg-primary)]"
                />
                <Button size={32} variant="primary" onClick={handleCitySearch} loading={cityLoading} disabled={!cityInput.trim()}>
                  {cityLoading ? "..." : "Найти"}
                </Button>
              </div>
            </div>
            {deliveryLat && deliveryLon && (
              <div className="p-4 bg-[var(--success-soft)] border-t border-separator flex items-center gap-3" role="status">
                <IconMapPin className="w-5 h-5 text-[var(--success)] shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-label-1 truncate">{deliveryAddr || deliveryLat.toFixed(5) + ", " + deliveryLon.toFixed(5)}</p>
                  <p className="text-xs text-[var(--success)] tabular-nums">Координаты: {deliveryLat.toFixed(5)}, {deliveryLon.toFixed(5)}</p>
                </div>
              </div>
            )}
            <div className="p-6 flex flex-col sm:flex-row gap-3">
              <Button variant="outline" size={44} onClick={() => setStep(1)}>Назад к материалам</Button>
              <Button
                variant="primary" size={44} className="flex-1"
                onClick={handleStep2Next}
                loading={loading}
                disabled={!deliveryLat}
              >
                {loading ? "Подбираем поставщиков..." : "Подобрать поставщиков"}
              </Button>
            </div>
          </Card>
        </div>
      )}

      {step === 3 && (
        <div>
          {sentCount > 0 ? (
            <Card padding={false} className="p-8 sm:p-12 text-center">
              <div className="w-16 h-16 rounded-full bg-[var(--success-soft)] flex items-center justify-center mx-auto mb-4">
                <IconTruck className="w-8 h-8 text-[var(--success)]" />
              </div>
              <h2 className="text-xl font-semibold text-label-1 mb-2">Тендер запущен!</h2>
              <p className="text-label-3 text-sm mb-6">РФК отправлены {sentCount} поставщикам. Ожидайте коммерческие предложения.</p>
              <Button variant="primary" size={44} onClick={() => router.push("/lk/requests/" + requestId)}>Перейти к заявке</Button>
            </Card>
          ) : (
            <div>
              {discoveredCount > 0 && (
                <div className="mb-4 p-3 bg-[var(--accent-soft)] border border-[var(--separator)] text-label-1 rounded-[var(--radius-lg)] text-sm" role="status">
                  Найдено {discoveredCount} новых поставщиков из интернета — они добавлены в базу и участвуют в подборе.
                </div>
              )}
              <Card
                title="Шаг 3: Выбор поставщиков"
                subtitle={"Найдено " + filteredSuppliers.length + " поставщиков. Отметьте, кому отправить запрос КП."}
                icon={<IconTruck className="w-5 h-5" />}
              >
                <div className="flex flex-wrap gap-2 mb-4">
                  <label htmlFor="source-filter" className="sr-only">Источник</label>
                  <select id="source-filter" value={sourceFilter} onChange={e => setSourceFilter(e.target.value)} className="field-input w-auto">
                    <option value="all">Все источники</option>
                    <option value="seed">Из базы</option>
                    <option value="llm">AI-поиск</option>
                    <option value="web">Веб-поиск</option>
                    <option value="2gis">2GIS</option>
                    <option value="dadata">DaData</option>
                  </select>
                  <label htmlFor="type-filter" className="sr-only">Тип поставщика</label>
                  <select id="type-filter" value={typeFilter} onChange={e => setTypeFilter(e.target.value)} className="field-input w-auto">
                    <option value="all">Все типы</option>
                    <option value="manufacturer">Только производители</option>
                    <option value="dealer">Только дилеры</option>
                    <option value="unknown">Неизвестно</option>
                  </select>
                  <label htmlFor="supplier-limit" className="sr-only">Показывать поставщиков</label>
                  <select id="supplier-limit" value={supplierLimit} onChange={e => setSupplierLimit(Number(e.target.value))} className="field-input w-auto">
                    {[5, 10, 15, 20].map(n => <option key={n} value={n}>{n} шт.</option>)}
                  </select>
                </div>

                {deliveryLat && deliveryLon && filteredSuppliers.length > 0 && (
                  <div className="h-[250px] sm:h-[300px] mb-4 rounded-[var(--radius-lg)] overflow-hidden border border-separator">
                    <SupplierMap suppliers={filteredSuppliers as any} centerLat={deliveryLat} centerLon={deliveryLon} />
                  </div>
                )}
                {filteredSuppliers.length === 0 ? (
                  <div className="text-center py-8 text-label-3 text-sm">Поставщики не найдены. Попробуйте изменить точку доставки или снять фильтры.</div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm min-w-[640px]">
                      <thead><tr className="border-b border-separator text-left">
                        <th scope="col" className="py-2 w-10">
                          <input type="checkbox" aria-label="Выбрать всех поставщиков"
                            onChange={e => { if (e.target.checked) setSelectedSuppliers(new Set(filteredSuppliers.map(s => s.supplier_id))); else setSelectedSuppliers(new Set()); }}
                            checked={selectedSuppliers.size === filteredSuppliers.length && filteredSuppliers.length > 0}
                            className="w-4 h-4 accent-[var(--accent)]" />
                        </th>
                        <th scope="col" className="py-2 font-medium text-label-3 text-xs">Поставщик</th>
                        <th scope="col" className="py-2 font-medium text-label-3 text-xs text-center">Баллы</th>
                        <th scope="col" className="py-2 font-medium text-label-3 text-xs text-center">Категории</th>
                        <th scope="col" className="py-2 font-medium text-label-3 text-xs text-center">Расст.</th>
                        <th scope="col" className="py-2 font-medium text-label-3 text-xs">Город</th>
                      </tr></thead>
                      <tbody>
                        {filteredSuppliers.map(s => (
                          <Fragment key={s.supplier_id}>
                            <tr className={"border-b border-[var(--fill-1)] cursor-pointer hover:bg-[var(--fill-1)] transition-colors " + (selectedSuppliers.has(s.supplier_id) ? "bg-[var(--accent-soft)]" : "")}
                              onClick={() => toggleSupplier(s.supplier_id)}>
                              <td className="py-2">
                                <input type="checkbox" aria-label={"Выбрать " + s.name}
                                  checked={selectedSuppliers.has(s.supplier_id) && s.has_email}
                              disabled={!s.has_email}
                              onChange={() => toggleSupplier(s.supplier_id)}
                                  onClick={e => e.stopPropagation()}
                                  className="w-4 h-4 accent-[var(--accent)]" />
                              </td>
                              <td className="py-2">
                                <p className="font-medium text-label-1 flex items-center gap-2 flex-wrap">
                                  {s.name}
                                  {s.supplier_type === "manufacturer" && <Badge tone="accent">Производитель</Badge>}
                                  {s.supplier_type === "dealer" && <Badge>Дилер</Badge>}
                                  {s.moderation_status === "unverified" && <Badge tone="warning">На проверке</Badge>}
                                </p>
                                <p className="text-xs text-label-4">{s.email}</p>
                              </td>
                              <td className="py-2 text-center">
                                <button type="button"
                                  onClick={(e) => { e.stopPropagation(); setExpandedSupplier(expandedSupplier === s.supplier_id ? null : s.supplier_id); }}
                                  aria-expanded={expandedSupplier === s.supplier_id}
                                  aria-label={"Детализация баллов: " + s.name}
                                  className="inline-flex items-center gap-1 px-2 py-0.5 bg-[var(--fill-2)] text-label-1 rounded-full text-xs font-semibold hover:bg-[var(--fill-3)] transition-colors tabular-nums">
                                  {s.total_score.toFixed(0)}
                                  <span className={"inline-block " + (expandedSupplier === s.supplier_id ? "rotate-180" : "")} aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3 h-3"><path d="m6 9 6 6 6-6"/></svg></span>
                                </button>
                              </td>
                              <td className="py-2 text-center text-xs text-label-3 tabular-nums">{s.matched_count}/{s.total_categories}</td>
                              <td className="py-2 text-center text-xs text-label-3 tabular-nums">{s.distance_km ? s.distance_km + " км" : "—"}</td>
                              <td className="py-2 text-xs text-label-3">{s.city || "—"}</td>
                            </tr>
                            {expandedSupplier === s.supplier_id && s.score_breakdown && (
                              <tr className="bg-[var(--fill-1)]">
                                <td colSpan={6} className="px-4 py-3 text-xs">
                                  <dl className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-label-3">
                                    <div><dt className="inline font-medium text-label-2">Категории: </dt><dd className="inline">{s.score_breakdown.category}</dd></div>
                                    <div><dt className="inline font-medium text-label-2">Расстояние: </dt><dd className="inline">{s.score_breakdown.distance}</dd></div>
                                    <div><dt className="inline font-medium text-label-2">Рейтинг: </dt><dd className="inline">{s.score_breakdown.rating}</dd></div>
                                    <div><dt className="inline font-medium text-label-2">Полнота: </dt><dd className="inline">{s.score_breakdown.completeness}</dd></div>
                                    <div><dt className="inline font-medium text-label-2">Производитель: </dt><dd className="inline">{s.score_breakdown.manufacturer_bonus}</dd></div>
                                    <div><dt className="inline font-medium text-label-2">Тип материала: </dt><dd className="inline">{s.score_breakdown.material_type}</dd></div>
                                    <div><dt className="inline font-medium text-label-2">Ассортимент: </dt><dd className="inline">{s.score_breakdown.product_match}</dd></div>
                                    <div className="sm:col-span-2 font-semibold text-label-1">Итого: {s.score_breakdown.total} баллов</div>
                                  </dl>
                                </td>
                              </tr>
                            )}
                          </Fragment>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                <div className="mt-6 flex flex-col sm:flex-row gap-3">
                  <Button variant="outline" size={44} onClick={() => setStep(2)}>Назад к карте</Button>
                  <Button
                    variant="primary" size={44} className="flex-1"
                    onClick={handleSendRfq}
                    loading={loading}
                    disabled={selectedSuppliers.size === 0}
                  >
                    {loading ? "Отправляем..." : "Начать тендер (" + selectedSuppliers.size + ")"}
                  </Button>
                </div>
              </Card>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

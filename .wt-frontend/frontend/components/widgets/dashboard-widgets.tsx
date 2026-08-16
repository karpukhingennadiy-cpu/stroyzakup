"use client";
import { useEffect, useState } from "react";
import { getCompetitiveSheet, getSuppliers, api } from "@/lib/api";
import { IconList, IconChart, IconMapPin, IconTruck } from "@/components/icons";

/* ------------------------------------------------------------------ */
/* Виджет «Статусы заявок»: всего / в работе / завершено / ожидание    */
/* ------------------------------------------------------------------ */

const STATUS_GROUPS = [
  {
    key: "total", label: "Всего", tone: "text-label-1",
    match: () => true,
  },
  {
    key: "active", label: "В работе", tone: "text-[var(--accent)]",
    match: (s: string) => ["confirmed", "matched", "matching", "rfq_sent", "collecting_quotes", "ready"].includes(s),
  },
  {
    key: "done", label: "Завершено", tone: "text-[var(--success)]",
    match: (s: string) => s === "completed",
  },
  {
    key: "pending", label: "Ожидание", tone: "text-[var(--warning)]",
    match: (s: string) => ["draft", "parsing", "cancelled"].includes(s),
  },
];

export function StatusCards({ requests }: { requests: any[] }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3" role="group" aria-label="Статистика заявок">
      {STATUS_GROUPS.map((g) => {
        const count = requests.filter((r) => g.match(r.status)).length;
        return (
          <div key={g.key} className="surface-card px-4 py-3.5">
            <p className="text-xs text-label-3">{g.label}</p>
            <p className={"mt-1 text-2xl font-semibold leading-8 " + g.tone} aria-label={g.label + ": " + count}>
              {count}
            </p>
          </div>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Виджет «Карта поставщиков»: SVG-заглушка гео-поиска без API-ключа   */
/* ------------------------------------------------------------------ */

interface GeoPoint {
  name: string;
  city?: string;
  latitude: number;
  longitude: number;
}

export function SuppliersMapWidget({ lat, lon }: { lat: number; lon: number }) {
  const [points, setPoints] = useState<GeoPoint[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    // Список /suppliers/ не отдаёт координаты — догружаем детали (addresses с lat/lon)
    getSuppliers()
      .then(async (data) => {
        const list = (data.results || data || []).slice(0, 25);
        setTotal((data.results || data || []).length);
        const details = await Promise.allSettled(
          list.map((s: any) => api("/suppliers/" + s.id + "/"))
        );
        const pts: GeoPoint[] = [];
        for (const d of details) {
          if (d.status !== "fulfilled") continue;
          for (const a of d.value.addresses || []) {
            if (a.latitude != null && a.longitude != null) {
              pts.push({ name: d.value.name, city: a.city, latitude: a.latitude, longitude: a.longitude });
            }
          }
        }
        setPoints(pts.slice(0, 80));
      })
      .catch(() => setFailed(true))
      .finally(() => setLoading(false));
  }, []);

  // Проекция координат в SVG (простая азимутальная привязка к центру)
  const R = 300; // км — радиус отображения
  const project = (p: GeoPoint) => {
    const dx = (p.longitude - lon) * 111 * Math.cos((lat * Math.PI) / 180);
    const dy = (p.latitude - lat) * 111;
    return { x: 150 + (dx / R) * 140, y: 150 - (dy / R) * 140 };
  };

  return (
    <section className="surface-card overflow-hidden" aria-label="Карта поставщиков">
      <header className="px-4 py-3 border-b border-separator bg-[var(--fill-1)] flex items-center gap-2">
        <IconMapPin className="w-4 h-4 text-label-3" />
        <h2 className="text-sm font-medium text-label-1">Карта поставщиков</h2>
        <span className="ml-auto text-xs text-label-3">радиус 300 км</span>
      </header>
      <div className="p-4">
        {loading ? (
          <p className="text-sm text-label-3 py-10 text-center" role="status">Загрузка карты...</p>
        ) : failed ? (
          <p className="text-sm text-label-3 py-10 text-center">Не удалось загрузить поставщиков</p>
        ) : (
          <svg viewBox="0 0 300 300" className="w-full h-auto" role="img" aria-label={"Поставщики на карте: " + points.length}>
            {/* Кольца радиуса */}
            {[100, 200, 300].map((km) => (
              <circle key={km} cx="150" cy="150" r={(km / R) * 140} fill="none" stroke="var(--separator)" strokeWidth="0.5" strokeDasharray="3 3" />
            ))}
            {/* Поставщики */}
            {points.map((pt, i) => {
              const p = project(pt);
              if (p.x < 4 || p.x > 296 || p.y < 4 || p.y > 296) return null;
              return (
                <g key={i}>
                  <circle cx={p.x} cy={p.y} r="3.5" fill="var(--accent)" opacity="0.75">
                    <title>{pt.name}{pt.city ? " — " + pt.city : ""}</title>
                  </circle>
                </g>
              );
            })}
            {/* Центр — точка доставки */}
            <circle cx="150" cy="150" r="5" fill="var(--brand)" stroke="var(--bg-primary)" strokeWidth="1.5">
              <title>Точка доставки</title>
            </circle>
          </svg>
        )}
        <p className="mt-2 text-xs text-label-3 text-center">
          {total} поставщиков в базе · на схеме: {points.length} · точность: схематично
        </p>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Виджет «График цен»: bar chart поставщик → итоговая цена            */
/* ------------------------------------------------------------------ */

export function PriceChartWidget({ requestId }: { requestId: number | null }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!requestId) { setLoading(false); return; }
    getCompetitiveSheet(requestId)
      .then(setData)
      .catch(() => setFailed(true))
      .finally(() => setLoading(false));
  }, [requestId]);

  const rows: any[] = (data?.suppliers || [])
    .filter((s: any) => typeof s.grand_total === "number")
    .sort((a: any, b: any) => a.grand_total - b.grand_total)
    .slice(0, 6);
  const max = rows.reduce((m, s) => Math.max(m, s.grand_total), 0);
  const bestId = data?.best?.supplier_id;

  return (
    <section className="surface-card overflow-hidden" aria-label="График цен">
      <header className="px-4 py-3 border-b border-separator bg-[var(--fill-1)] flex items-center gap-2">
        <IconChart className="w-4 h-4 text-label-3" />
        <h2 className="text-sm font-medium text-label-1">График цен</h2>
        <span className="ml-auto text-xs text-label-3">по конкурентному листу</span>
      </header>
      <div className="p-4">
        {loading ? (
          <p className="text-sm text-label-3 py-10 text-center" role="status">Загрузка цен...</p>
        ) : failed || !requestId || rows.length === 0 ? (
          <div className="py-10 text-center">
            <IconTruck className="w-8 h-8 mx-auto text-label-4" />
            <p className="mt-2 text-sm text-label-3">
              {requestId ? "КП пока нет — график появится после ответов поставщиков" : "Создайте заявку, чтобы сравнивать цены"}
            </p>
          </div>
        ) : (
          <ul className="space-y-2.5">
            {rows.map((s: any) => {
              const isBest = s.supplier_id === bestId;
              const widthPct = max > 0 ? Math.max(4, (s.grand_total / max) * 100) : 4;
              return (
                <li key={s.supplier_id ?? s.supplier_name}>
                  <div className="flex items-baseline justify-between gap-2 mb-1">
                    <span className="text-xs text-label-2 truncate">
                      {s.supplier_name}
                      {isBest && <span className="ml-1.5 text-[var(--success)] font-medium">лучшее</span>}
                    </span>
                    <span className="text-xs font-medium text-label-1 shrink-0 tabular-nums">
                      {s.grand_total.toLocaleString("ru-RU")} ₽
                    </span>
                  </div>
                  <div className="h-2.5 rounded-full bg-[var(--fill-1)] overflow-hidden" role="img"
                    aria-label={s.supplier_name + ": " + s.grand_total.toLocaleString("ru-RU") + " рублей"}>
                    <div
                      className="h-full rounded-full transition-[width] duration-300 ease-kimi-out"
                      style={{
                        width: widthPct + "%",
                        backgroundColor: isBest ? "var(--success)" : "var(--accent)",
                      }}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}

export { IconList };

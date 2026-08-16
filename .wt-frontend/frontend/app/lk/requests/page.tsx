"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { getRequests } from "@/lib/api";
import { IconPlus, IconList } from "@/components/icons";
import { buttonClass, Card } from "@/components/ui";
import { StatusCards, SuppliersMapWidget, PriceChartWidget } from "@/components/widgets/dashboard-widgets";

const statusLabels: Record<string, string> = {
  draft: "Черновик", parsing: "Распознавание", confirmed: "Подтверждена",
  matched: "Поставщики подобраны", matching: "Поиск поставщиков",
  rfq_sent: "РФК отправлены", collecting_quotes: "Сбор КП",
  ready: "Готов к сравнению", completed: "Завершена", cancelled: "Отменена",
};

// Центр карты по умолчанию — Москва
const DEFAULT_LAT = 55.7558;
const DEFAULT_LON = 37.6173;

export default function RequestsPage() {
  const [requests, setRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getRequests()
      .then((data) => setRequests(data.results || data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-label-3 text-base p-8" role="status">Загрузка заявок...</div>;
  if (error) return <div className="p-8 text-[var(--danger)]" role="alert">Ошибка: {error}</div>;

  const header = (
    <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
      <div>
        <h1 className="text-xl font-semibold text-label-1">Мои заявки</h1>
        <p className="text-label-3 text-sm mt-0.5">
          {requests.length > 0 ? requests.length + " заявок" : "Управляйте закупками стройматериалов"}
        </p>
      </div>
      <Link href="/lk/requests/new" className={buttonClass({ variant: "primary", size: 44 })}>
        <IconPlus className="w-5 h-5" /> Новая заявка
      </Link>
    </div>
  );

  if (requests.length === 0) {
    return (
      <div>
        {header}
        <Card padding={false} className="p-16 text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-[var(--radius-xl)] bg-[var(--accent-soft)] flex items-center justify-center">
            <IconList className="w-10 h-10 text-[var(--accent)]" />
          </div>
          <h2 className="text-xl font-semibold text-label-1 mb-2">Нет заявок</h2>
          <p className="text-label-3 mb-6 max-w-md mx-auto text-sm">
            Создайте первую заявку — сервис найдёт поставщиков и сравнит цены.
          </p>
          <Link href="/lk/requests/new" className={buttonClass({ variant: "primary", size: 44 })}>
            <IconPlus className="w-5 h-5" /> Создать заявку
          </Link>
        </Card>
      </div>
    );
  }

  // Берём точку последней заявки с координатами для карты; иначе Москва
  const withCoords = requests.find((r) => r.latitude && r.longitude);
  const mapLat = withCoords?.latitude ?? DEFAULT_LAT;
  const mapLon = withCoords?.longitude ?? DEFAULT_LON;
  // Последняя заявка со статусом «есть шанс на КП» для графика цен
  const priceReq =
    requests.find((r) => ["rfq_sent", "collecting_quotes", "ready", "completed"].includes(r.status)) ||
    requests[0];

  return (
    <div>
      {header}

      {/* Dashboard-виджеты */}
      <div className="mb-8 space-y-4">
        <StatusCards requests={requests} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SuppliersMapWidget lat={mapLat} lon={mapLon} />
          <PriceChartWidget requestId={priceReq?.id ?? null} />
        </div>
      </div>

      <ul className="space-y-3">
        {requests.map((req: any) => (
          <li key={req.id}>
            <Link href={"/lk/requests/" + req.id}
              className="block surface-card p-5 hover:shadow-small transition-shadow duration-150 ease-kimi-out">
              <div className="flex flex-wrap justify-between items-start gap-2">
                <div className="flex items-center gap-3 min-w-0">
                  <span className="font-mono font-semibold text-[var(--accent)]">RFQ-{req.code}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--fill-2)] text-label-3 shrink-0">
                    {statusLabels[req.status] || req.status}
                  </span>
                </div>
                <span className="text-xs text-label-4 tabular-nums">{new Date(req.created_at).toLocaleDateString("ru-RU")}</span>
              </div>
              {req.raw_text && (
                <p className="text-sm text-label-3 mt-2 truncate">{req.raw_text.slice(0, 120)}</p>
              )}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { getRequests } from "@/lib/api";
import { Plus, List, Search, Sparkles, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { StatusCards, SuppliersMapWidget, PriceChartWidget } from "@/components/widgets/dashboard-widgets";

const statusLabels: Record<string, string> = {
  draft: "Черновик",
  parsing: "Распознавание",
  confirmed: "Подтверждена",
  matched: "Поставщики подобраны",
  matching: "Поиск поставщиков",
  rfq_sent: "РФК отправлены",
  collecting_quotes: "Сбор КП",
  ready: "Готов к сравнению",
  completed: "Завершена",
  cancelled: "Отменена",
  rfq_failed: "Ошибка отправки РФК",
};

const statusBadgeVariant: Record<
  string,
  "default" | "secondary" | "destructive" | "outline" | "info" | "success" | "warning" | "danger" | "neutral"
> = {
  draft: "neutral",
  parsing: "neutral",
  confirmed: "success",
  matched: "info",
  matching: "neutral",
  rfq_sent: "info",
  collecting_quotes: "info",
  ready: "success",
  completed: "success",
  cancelled: "danger",
  rfq_failed: "danger",
};

const statusTabs = [
  { key: "", label: "Все" },
  { key: "active", label: "В работе" },
  { key: "done", label: "Завершено" },
  { key: "error", label: "Ошибка" },
];

function matchesTab(status: string, tab: string): boolean {
  switch (tab) {
    case "active":
      return ["parsing", "confirmed", "matched", "matching", "rfq_sent", "collecting_quotes", "ready"].includes(status);
    case "done":
      return status === "completed";
    case "error":
      return status === "rfq_failed" || status.includes("fail") || status.includes("error");
    default:
      return true;
  }
}

const DEFAULT_LAT = 55.7558;
const DEFAULT_LON = 37.6173;

export default function RequestsPage() {
  const [requests, setRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 10;

  useEffect(() => {
    getRequests()
      .then((data) => setRequests(data.results || data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const filteredRequests = useMemo(() => {
    let result = requests;
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (r) =>
          r.code?.toLowerCase().includes(q) ||
          r.raw_text?.toLowerCase().includes(q)
      );
    }
    result = result.filter((r) => matchesTab(r.status, statusFilter));
    return result;
  }, [requests, search, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredRequests.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const paginated = filteredRequests.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-[var(--danger)]" role="alert">
        Ошибка: {error}
      </div>
    );
  }

  const withCoords = requests.find((r) => r.latitude && r.longitude);
  const mapLat = withCoords?.latitude ?? DEFAULT_LAT;
  const mapLon = withCoords?.longitude ?? DEFAULT_LON;
  const priceReq =
    requests.find((r) =>
      ["rfq_sent", "collecting_quotes", "ready", "completed"].includes(r.status)
    ) || requests[0];

  return (
    <div>
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-xl font-semibold text-[var(--label-primary)]">
            Мои заявки
          </h1>
          <p className="text-[var(--label-tertiary)] text-sm mt-0.5">
            {requests.length > 0
              ? `${requests.length} заявок`
              : "Управляйте закупками стройматериалов"}
          </p>
        </div>
        <Link href="/lk/requests/new">
          <Button>
            <Plus className="w-4 h-4 mr-2" aria-hidden="true" />
            Новая заявка
          </Button>
        </Link>
      </div>

      {/* Dashboard widgets */}
      <div className="mb-8 space-y-4">
        <StatusCards requests={requests} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SuppliersMapWidget lat={mapLat} lon={mapLon} />
          <PriceChartWidget requestId={priceReq?.id ?? null} />
        </div>
      </div>

      {/* Баннер */}
      <div className="mb-4 flex items-center gap-2 px-4 h-12 rounded-[var(--radius-lg)] bg-[var(--accent-soft)] border border-[var(--separator)]">
        <Sparkles className="w-4 h-4 text-[var(--accent)] shrink-0" aria-hidden="true" />
        <p className="text-sm text-[var(--label-primary)]">База поставщиков пополняется автоматически</p>
      </div>

      {/* Filters */}
      {requests.length > 0 && (
        <div className="flex flex-wrap gap-3 mb-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--label-quaternary)]" aria-hidden="true" />
            <Input
              placeholder="Поиск по коду или содержимому..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="pl-9"
              aria-label="Поиск заявок"
            />
          </div>
          <div className="flex items-center gap-1 bg-[var(--fill-1)] rounded-[var(--radius-lg)] p-1" role="tablist" aria-label="Фильтр по статусу">
            {statusTabs.map((tab) => (
              <button
                key={tab.key}
                type="button"
                role="tab"
                aria-selected={statusFilter === tab.key}
                onClick={() => { setStatusFilter(tab.key); setPage(1); }}
                className={
                  "px-3 py-1.5 rounded-[var(--radius-md)] text-sm font-medium transition-colors duration-150 " +
                  (statusFilter === tab.key
                    ? "bg-[var(--bg-primary)] text-[var(--label-primary)] shadow-sm"
                    : "text-[var(--label-secondary)] hover:text-[var(--label-primary)]")
                }
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Requests list */}
      {requests.length === 0 ? (
        <Card>
          <CardContent className="p-16 text-center">
            <div className="w-20 h-20 mx-auto mb-6 rounded-[var(--radius-xl)] bg-[var(--accent-soft)] flex items-center justify-center">
              <List className="w-10 h-10 text-[var(--accent)]" aria-hidden="true" />
            </div>
            <h2 className="text-xl font-semibold text-[var(--label-primary)] mb-2">
              Нет заявок
            </h2>
            <p className="text-[var(--label-tertiary)] mb-6 max-w-md mx-auto text-sm">
              Создайте первую заявку — сервис найдёт поставщиков и сравнит цены.
            </p>
            <Link href="/lk/requests/new">
              <Button>
                <Plus className="w-4 h-4 mr-2" aria-hidden="true" />
                Создать заявку
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : filteredRequests.length === 0 ? (
        <Card>
          <CardContent className="p-10 text-center">
            <p className="text-[var(--label-tertiary)]">
              Заявки не найдены по заданным фильтрам
            </p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => {
                setSearch("");
                setStatusFilter("");
              }}
            >
              Сбросить фильтры
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="rounded-[var(--radius-lg)] border border-[var(--separator)] bg-[var(--bg-primary)] overflow-hidden">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="[&>th]:bg-[var(--bg-secondary)] [&>th]:text-[var(--label-tertiary)] [&>th]:text-xs [&>th]:uppercase [&>th]:font-semibold">
                  <TableHead className="w-[120px]">Код</TableHead>
                  <TableHead>Статус</TableHead>
                  <TableHead className="hidden sm:table-cell">Описание</TableHead>
                  <TableHead className="text-right">Дата</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginated.map((req: any) => (
                  <TableRow key={req.id} className="cursor-pointer hover:bg-[var(--bg-secondary)] transition-colors">
                    <TableCell>
                      <Link
                        href={`/lk/requests/${req.id}`}
                        className="font-mono font-semibold text-[var(--accent)] hover:underline focus-visible:outline-2 focus-visible:outline-[var(--accent)] focus-visible:outline-offset-2 rounded-[var(--radius-xs)]"
                      >
                        RFQ-{req.code}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge variant={statusBadgeVariant[req.status] || "secondary"}>
                        {statusLabels[req.status] || req.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="hidden sm:table-cell max-w-xs">
                      <span className="text-sm text-[var(--label-secondary)] truncate block">
                        {req.raw_text || "—"}
                      </span>
                    </TableCell>
                    <TableCell className="text-right text-sm text-[var(--label-tertiary)] tabular-nums">
                      {new Date(req.created_at).toLocaleDateString("ru-RU")}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          {/* Пагинация */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-separator">
            <p className="text-sm text-[var(--label-tertiary)]">
              {filteredRequests.length > 0
                ? `${(safePage - 1) * PAGE_SIZE + 1}–${Math.min(safePage * PAGE_SIZE, filteredRequests.length)} из ${filteredRequests.length}`
                : "0 заявок"}
            </p>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={safePage <= 1} onClick={() => setPage(safePage - 1)}>
                <ChevronLeft className="w-4 h-4" /> Назад
              </Button>
              <Button variant="outline" size="sm" disabled={safePage >= totalPages} onClick={() => setPage(safePage + 1)}>
                Вперёд <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { getRequests } from "@/lib/api";
import { Plus, Search, List } from "lucide-react";
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
};

const statusBadgeVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  draft: "secondary",
  parsing: "secondary",
  confirmed: "default",
  matched: "default",
  matching: "secondary",
  rfq_sent: "default",
  collecting_quotes: "default",
  ready: "default",
  completed: "outline",
  cancelled: "destructive",
};

const DEFAULT_LAT = 55.7558;
const DEFAULT_LON = 37.6173;

export default function RequestsPage() {
  const [requests, setRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

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
    if (statusFilter) {
      result = result.filter((r) => r.status === statusFilter);
    }
    return result;
  }, [requests, search, statusFilter]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
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
          <h1 className="text-2xl font-semibold tracking-tight text-[var(--label-primary)]">
            Мои заявки
          </h1>
          <p className="text-[var(--label-tertiary)] text-sm mt-1">
            {requests.length > 0
              ? `${requests.length} заявок`
              : "Управляйте закупками стройматериалов"}
          </p>
        </div>
        <Link href="/lk/requests/new">
          <Button size="lg">
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
        <div className="relative rounded-[var(--radius-lg)] overflow-hidden border border-[var(--separator)] shadow-[var(--shadow-xs)]">
          <img src="/images/suppliers-network.jpg" alt="Сеть поставщиков" className="w-full h-40 object-cover" loading="lazy" />
          <div className="absolute inset-0 bg-gradient-to-r from-[var(--bg-primary)]/80 to-transparent flex items-center px-6">
            <p className="text-sm font-medium text-[var(--label-primary)]">База поставщиков пополняется автоматически — 2GIS, DaData, веб-поиск</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      {requests.length > 0 && (
        <div className="flex flex-wrap gap-3 mb-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--label-quaternary)]" aria-hidden="true" />
            <Input
              placeholder="Поиск по коду или содержимому..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
              aria-label="Поиск заявок"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-9 rounded-[var(--radius-md)] border border-[var(--separator)] bg-[var(--bg-tertiary)] px-3 text-sm text-[var(--label-primary)] shadow-[var(--shadow-input)] outline-none focus-visible:border-[var(--accent)] focus-visible:ring-2 focus-visible:ring-[var(--accent)]/30"
            aria-label="Фильтр по статусу"
          >
            <option value="">Все статусы</option>
            {Object.entries(statusLabels).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Requests list */}
      {requests.length === 0 ? (
        <Card>
          <CardContent className="p-16 text-center">
            <div className="w-20 h-20 mx-auto mb-6 rounded-[var(--radius-xl)] bg-[var(--accent-soft)] flex items-center justify-center">
              <List className="w-10 h-10 text-[var(--accent)]" aria-hidden="true" />
            </div>
            <h2 className="text-xl font-semibold tracking-tight text-[var(--label-primary)] mb-2">
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
        <div className="rounded-[var(--radius-lg)] border border-[var(--separator)] bg-[var(--bg-tertiary)] shadow-[var(--shadow-xs)] overflow-hidden">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[120px]">Код</TableHead>
                  <TableHead>Статус</TableHead>
                  <TableHead className="hidden sm:table-cell">Описание</TableHead>
                  <TableHead className="text-right">Дата</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRequests.map((req: any) => (
                  <TableRow key={req.id} className="cursor-pointer hover:bg-[var(--fill-1)]">
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
        </div>
      )}
    </div>
  );
}
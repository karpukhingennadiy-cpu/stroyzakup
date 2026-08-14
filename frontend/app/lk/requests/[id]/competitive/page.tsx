"use client";

import { useEffect, useState, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getCompetitiveSheet, downloadCompetitiveSheetXlsx } from "@/lib/api";
import { captureEvent } from "@/lib/analytics";
import { Trophy, ArrowLeft, ArrowUpDown } from "lucide-react";
import { IconChart, IconDownload } from "@/components/icons";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

type SortField = "supplier_name" | "materials_total" | "delivery" | "grand_total";
type SortDir = "asc" | "desc";

export default function CompetitivePage() {
  const params = useParams();
  const id = params.id as string;
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sort, setSort] = useState<{ field: SortField; dir: SortDir }>({
    field: "grand_total",
    dir: "asc",
  });

  useEffect(() => {
    getCompetitiveSheet(Number(id))
      .then((d) => {
        setData(d);
        captureEvent("competitive_sheet_viewed", {
          request_id: Number(id),
          suppliers_count: d?.suppliers?.length ?? 0,
        });
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleDownloadXlsx = async () => {
    try {
      const blob = await downloadCompetitiveSheetXlsx(Number(id));
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `competitive_sheet_RFQ-${id}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
      captureEvent("competitive_sheet_downloaded", {
        request_id: Number(id),
        format: "xlsx",
      });
    } catch (e: any) {
      setError(e.message);
    }
  };

  const suppliers = data?.suppliers || [];
  const best = data?.best;

  const sortedSuppliers = useMemo(() => {
    const list = [...suppliers];
    list.sort((a: any, b: any) => {
      const aVal = a[sort.field] ?? 0;
      const bVal = b[sort.field] ?? 0;
      if (typeof aVal === "string") {
        return sort.dir === "asc"
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }
      return sort.dir === "asc" ? aVal - bVal : bVal - aVal;
    });
    return list;
  }, [suppliers, sort]);

  const maxTotal = suppliers.reduce(
    (m: number, s: any) => Math.max(m, s.grand_total || 0),
    0
  );

  const toggleSort = (field: SortField) => {
    setSort((prev) => ({
      field,
      dir: prev.field === field && prev.dir === "asc" ? "desc" : "asc",
    }));
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <Skeleton className="h-8 w-64" />
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

  return (
    <div className="max-w-5xl mx-auto">
      {/* Back link */}
      <Link
        href={`/lk/requests/${id}`}
        className="inline-flex items-center gap-1 text-sm text-[var(--label-tertiary)] hover:text-[var(--label-primary)] mb-4 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" aria-hidden="true" />
        К заявке
      </Link>

      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-[var(--label-primary)]">
            Конкурентный лист
          </h1>
          <p className="text-[var(--label-tertiary)] text-sm mt-0.5">
            Сравнение коммерческих предложений — {suppliers.length} поставщиков
          </p>
        </div>
        {suppliers.length > 0 && (
          <Button variant="outline" onClick={handleDownloadXlsx}>
            <IconDownload className="w-4 h-4 mr-2" aria-hidden="true" />
            Скачать XLSX
          </Button>
        )}
      </div>

      {suppliers.length === 0 ? (
        <Card>
          <CardContent className="p-16 text-center">
            <div className="w-20 h-20 mx-auto mb-6 rounded-[var(--radius-xl)] bg-[var(--accent-soft)] flex items-center justify-center">
              <IconChart className="w-10 h-10 text-[var(--accent)]" aria-hidden="true" />
            </div>
            <h2 className="text-xl font-semibold text-[var(--label-primary)] mb-2">
              Ожидайте предложения
            </h2>
            <p className="text-[var(--label-tertiary)] max-w-md mx-auto text-sm">
              После отправки запросов КП здесь появится сравнение цен от поставщиков.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <CardHeader className="pb-0">
            <CardTitle className="text-base">Сравнение предложений</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>
                      <button
                        onClick={() => toggleSort("supplier_name")}
                        className="inline-flex items-center gap-1 hover:text-[var(--accent)] transition-colors"
                      >
                        Поставщик
                        <ArrowUpDown className="w-3 h-3" aria-hidden="true" />
                      </button>
                    </TableHead>
                    <TableHead className="text-right">
                      <button
                        onClick={() => toggleSort("materials_total")}
                        className="inline-flex items-center gap-1 hover:text-[var(--accent)] transition-colors"
                      >
                        Материалы
                        <ArrowUpDown className="w-3 h-3" aria-hidden="true" />
                      </button>
                    </TableHead>
                    <TableHead className="text-right">
                      <button
                        onClick={() => toggleSort("delivery")}
                        className="inline-flex items-center gap-1 hover:text-[var(--accent)] transition-colors"
                      >
                        Доставка
                        <ArrowUpDown className="w-3 h-3" aria-hidden="true" />
                      </button>
                    </TableHead>
                    <TableHead className="text-right">
                      <button
                        onClick={() => toggleSort("grand_total")}
                        className="inline-flex items-center gap-1 hover:text-[var(--accent)] transition-colors"
                      >
                        Итого
                        <ArrowUpDown className="w-3 h-3" aria-hidden="true" />
                      </button>
                    </TableHead>
                    <TableHead>Сравнение</TableHead>
                    <TableHead>Оплата</TableHead>
                    <TableHead>Срок</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedSuppliers.map((s: any, i: number) => {
                    const isBest = best && s.supplier_id === best.supplier_id;
                    const widthPct =
                      maxTotal > 0
                        ? Math.max(3, ((s.grand_total || 0) / maxTotal) * 100)
                        : 3;
                    return (
                      <TableRow
                        key={i}
                        className={isBest ? "bg-[var(--success-soft)]" : ""}
                      >
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-[var(--label-primary)]">
                              {s.supplier_name}
                            </span>
                            {isBest && (
                              <Badge
                                variant="default"
                                className="bg-[var(--success)] text-white"
                              >
                                <Trophy className="w-3 h-3 mr-1" aria-hidden="true" />
                                Лучшее
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-right text-[var(--label-secondary)] tabular-nums">
                          {s.materials_total?.toLocaleString("ru-RU")} ₽
                        </TableCell>
                        <TableCell className="text-right text-[var(--label-secondary)] tabular-nums">
                          {s.delivery?.toLocaleString("ru-RU")} ₽
                        </TableCell>
                        <TableCell className="text-right font-semibold text-[var(--label-primary)] tabular-nums">
                          {s.grand_total?.toLocaleString("ru-RU")} ₽
                        </TableCell>
                        <TableCell className="w-40">
                          <div
                            className="h-2 rounded-full bg-[var(--fill-1)] overflow-hidden"
                            role="img"
                            aria-label={`${s.supplier_name}: ${(s.grand_total || 0).toLocaleString("ru-RU")} рублей`}
                          >
                            <div
                              className="h-full rounded-full"
                              style={{
                                width: `${widthPct}%`,
                                backgroundColor: isBest
                                  ? "var(--success)"
                                  : "var(--accent)",
                              }}
                            />
                          </div>
                        </TableCell>
                        <TableCell className="text-sm text-[var(--label-tertiary)]">
                          {s.payment_terms || "—"}
                        </TableCell>
                        <TableCell className="text-sm text-[var(--label-tertiary)]">
                          {s.delivery_time || "—"}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

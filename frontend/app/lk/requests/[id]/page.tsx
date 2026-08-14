"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getRequest, parseRequest, confirmRequest, downloadWinnerProtocolPdf } from "@/lib/api";
import { captureEvent } from "@/lib/analytics";
import { CheckCircle2, AlertTriangle, ArrowLeft, Check } from "lucide-react";
import { IconSparkles, IconChart, IconDownload } from "@/components/icons";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

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

const statusOrder = [
  "draft",
  "parsing",
  "confirmed",
  "matching",
  "matched",
  "rfq_sent",
  "collecting_quotes",
  "ready",
  "completed",
];

function ConfBadge({ confidence, needsClarification }: { confidence: number; needsClarification?: boolean }) {
  const pct = Math.round(confidence * 100);
  let variant: "default" | "secondary" | "destructive" | "outline" = "default";
  if (needsClarification || pct < 60) variant = "outline";
  if (pct < 40) variant = "destructive";
  return <Badge variant={variant}>{pct}%</Badge>;
}

function StatusStepper({ currentStatus }: { currentStatus: string }) {
  const currentIndex = statusOrder.indexOf(currentStatus);
  return (
    <ol className="flex items-start mb-6 overflow-x-auto pb-1" aria-label="Статус заявки">
      {statusOrder.map((status, i) => {
        const done = i < currentIndex;
        const active = status === currentStatus;
        return (
          <li key={status} className="flex items-center flex-1 min-w-[90px] last:flex-none">
            <div className="flex flex-col items-center w-full">
              <div
                className={
                  "flex items-center justify-center size-7 rounded-full border text-xs font-semibold shrink-0 " +
                  (active
                    ? "bg-[var(--accent)] border-[var(--accent)] text-white"
                    : done
                    ? "bg-[var(--success)] border-[var(--success)] text-white"
                    : "bg-[var(--fill-1)] border-[var(--separator)] text-[var(--label-quaternary)]")
                }
              >
                {done ? <Check className="size-3.5" aria-hidden="true" /> : i + 1}
              </div>
              <span
                className={
                  "mt-1.5 text-[11px] leading-tight text-center " +
                  (active
                    ? "text-[var(--label-primary)] font-medium"
                    : done
                    ? "text-[var(--label-secondary)]"
                    : "text-[var(--label-tertiary)]")
                }
              >
                {statusLabels[status]}
              </span>
            </div>
            {i < statusOrder.length - 1 && (
              <div
                className={
                  "h-px flex-1 -mt-3.5 mx-1 " +
                  (i < currentIndex ? "bg-[var(--success)]" : "bg-[var(--separator)]")
                }
                aria-hidden="true"
              />
            )}
          </li>
        );
      })}
    </ol>
  );
}

export default function RequestDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [req, setReq] = useState<any>(null);
  const [clarifications, setClarifications] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState("");
  const [error, setError] = useState("");

  const load = () => {
    getRequest(Number(id))
      .then((data) => {
        setReq(data);
        setClarifications(data.clarifications || []);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, [id]);

  const handleParse = async () => {
    setActionLoading("parse");
    setError("");
    try {
      const result = await parseRequest(Number(id));
      setReq(result);
      setClarifications(result.clarifications || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setActionLoading("");
    }
  };

  const handleConfirm = async () => {
    setActionLoading("confirm");
    setError("");
    try {
      const result = await confirmRequest(Number(id));
      setReq(result.request || result);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setActionLoading("");
    }
  };

  const handleDownloadProtocol = async () => {
    try {
      const blob = await downloadWinnerProtocolPdf(Number(id));
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `winner_protocol_RFQ-${req.code}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
      captureEvent("protocol_downloaded", {
        request_id: Number(id),
        format: "pdf",
      });
    } catch (e: any) {
      setError(e.message);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-[var(--label-tertiary)] text-base" role="status">
        Загрузка заявки...
      </div>
    );
  }

  if (error && !req) {
    return (
      <div className="p-8 text-[var(--danger)]" role="alert">
        Ошибка: {error}
      </div>
    );
  }

  if (!req) {
    return <div className="p-8 text-[var(--label-tertiary)]">Заявка не найдена</div>;
  }

  const itemsNeedClarification =
    req.items?.filter((i: any) => i.needs_clarification || i.confidence < 0.6) || [];

  return (
    <div className="max-w-4xl mx-auto">
      {/* Back link */}
      <Link
        href="/lk/requests"
        className="inline-flex items-center gap-1 text-sm text-[var(--label-tertiary)] hover:text-[var(--label-primary)] mb-4 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" aria-hidden="true" />
        К списку заявок
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-[var(--label-primary)]">
            Заявка RFQ-{req.code}
          </h1>
          <p className="text-[var(--label-tertiary)] text-sm mt-1">
            Статус: {statusLabels[req.status] || req.status}
          </p>
        </div>
        <Link href={`/lk/requests/${id}/competitive`}>
          <Button variant="outline">
            <IconChart className="w-4 h-4 mr-2" aria-hidden="true" />
            Конкурентный лист
          </Button>
        </Link>
      </div>

      {/* Status stepper */}
      <StatusStepper currentStatus={req.status} />

      {error && (
        <div
          className="mb-6 p-4 bg-[var(--danger-soft)] border border-[var(--separator)] text-[var(--danger)] rounded-[var(--radius-lg)] text-sm"
          role="alert"
          aria-live="assertive"
        >
          {error}
        </div>
      )}

      {/* Clarifications */}
      {clarifications.length > 0 && (
        <Card className="mb-6 border-[var(--warning)]">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2 text-[var(--warning)]">
              <AlertTriangle className="w-5 h-5" aria-hidden="true" />
              Требуются уточнения ({clarifications.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {clarifications.map((q: string, i: number) => (
                <li key={i} className="flex gap-2 text-[var(--label-primary)] text-sm">
                  <span className="text-[var(--warning)] mt-0.5" aria-hidden="true">
                    ?
                  </span>
                  <span>{q}</span>
                </li>
              ))}
            </ul>
            <p className="text-[var(--warning)] text-xs mt-3">
              Уточните детали у заказчика перед подтверждением заявки
            </p>
          </CardContent>
        </Card>
      )}

      {/* Raw text */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">Исходный текст</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-[var(--fill-1)] rounded-[var(--radius-md)] p-4 text-sm text-[var(--label-secondary)] whitespace-pre-wrap">
            {req.raw_text || "(пусто)"}
          </div>
          <div className="flex gap-3 flex-wrap">
            {(req.status === "draft" || req.status === "parsing") && (
              <Button
                onClick={handleParse}
                disabled={actionLoading === "parse"}
                aria-busy={actionLoading === "parse"}
              >
                {actionLoading === "parse" ? (
                  "Распознаём..."
                ) : (
                  <>
                    <IconSparkles className="w-4 h-4 mr-2" aria-hidden="true" />
                    Распознать материалы
                  </>
                )}
              </Button>
            )}
            {req.status === "parsing" && req.items?.length > 0 && (
              <Button
                variant="outline"
                onClick={handleConfirm}
                disabled={actionLoading === "confirm"}
                aria-busy={actionLoading === "confirm"}
              >
                {actionLoading === "confirm" ? (
                  "Подтверждаем..."
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4 mr-2" aria-hidden="true" />
                    Подтвердить позиции
                  </>
                )}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Items table */}
      {req.items && req.items.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-base">
              Распознанные позиции ({req.items.length})
            </CardTitle>
            {itemsNeedClarification.length > 0 && (
              <CardDescription>
                {itemsNeedClarification.length} требуют уточнения
              </CardDescription>
            )}
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Материал</TableHead>
                    <TableHead className="hidden sm:table-cell">Категория</TableHead>
                    <TableHead className="text-right">Кол-во</TableHead>
                    <TableHead>Ед.</TableHead>
                    <TableHead className="hidden sm:table-cell">Бренд</TableHead>
                    <TableHead className="text-center">Точность</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {req.items.map((item: any) => (
                    <TableRow
                      key={item.id}
                      className={item.needs_clarification ? "bg-[var(--warning-soft)]" : ""}
                    >
                      <TableCell>
                        <div className="flex items-center gap-1">
                          {item.needs_clarification && (
                            <AlertTriangle
                              className="w-4 h-4 text-[var(--warning)] shrink-0"
                              aria-label="Требует уточнения"
                            />
                          )}
                          <span className="text-[var(--label-primary)]">{item.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="hidden sm:table-cell text-[var(--label-tertiary)]">
                        {item.category_name || "—"}
                      </TableCell>
                      <TableCell className="text-right text-[var(--label-primary)] tabular-nums">
                        {item.quantity}
                      </TableCell>
                      <TableCell className="text-[var(--label-tertiary)]">
                        {item.unit_name || "—"}
                      </TableCell>
                      <TableCell className="hidden sm:table-cell text-[var(--label-tertiary)]">
                        {item.brand || "—"}
                      </TableCell>
                      <TableCell className="text-center">
                        <ConfBadge
                          confidence={item.confidence || 0}
                          needsClarification={item.needs_clarification}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <div className="flex gap-3 flex-wrap">
        {(req.status === "ready" || req.status === "completed") && (
          <Button
            variant="outline"
            onClick={handleDownloadProtocol}
          >
            <IconDownload className="w-4 h-4 mr-2" aria-hidden="true" />
            Протокол PDF
          </Button>
        )}
      </div>
    </div>
  );
}
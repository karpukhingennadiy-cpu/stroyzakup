"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getRequest, parseRequest, confirmRequest } from "@/lib/api";
import { IconChart, IconSparkles } from "@/components/icons";
import { Button, buttonClass, Card, Badge } from "@/components/ui";

const statusLabels: Record<string, string> = {
  draft: "Черновик", parsing: "Распознавание", confirmed: "Подтверждена",
  matched: "Поставщики подобраны", matching: "Поиск поставщиков",
  rfq_sent: "РФК отправлены", collecting_quotes: "Сбор КП",
  ready: "Готов к сравнению", completed: "Завершена", cancelled: "Отменена",
};

function ConfBadge({ confidence, needsClarification }: { confidence: number; needsClarification?: boolean }) {
  const pct = Math.round(confidence * 100);
  let tone: "success" | "warning" | "danger" = "success";
  if (needsClarification || pct < 60) tone = "warning";
  if (pct < 40) tone = "danger";
  return <Badge tone={tone}>{pct}%</Badge>;
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
    getRequest(Number(id)).then((data) => {
      setReq(data);
      setClarifications(data.clarifications || []);
    }).catch((e) => setError(e.message)).finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleParse = async () => {
    setActionLoading("parse");
    setError("");
    try {
      const result = await parseRequest(Number(id));
      setReq(result);
      setClarifications(result.clarifications || []);
    } catch (e: any) { setError(e.message); }
    finally { setActionLoading(""); }
  };

  const handleConfirm = async () => {
    setActionLoading("confirm");
    setError("");
    try {
      const result = await confirmRequest(Number(id));
      setReq(result.request || result);
    } catch (e: any) { setError(e.message); }
    finally { setActionLoading(""); }
  };

  if (loading) return <div className="p-8 text-label-3 text-base" role="status">Загрузка заявки...</div>;
  if (error && !req) return <div className="p-8 text-[var(--danger)]" role="alert">Ошибка: {error}</div>;
  if (!req) return <div className="p-8 text-label-3">Заявка не найдена</div>;

  const itemsNeedClarification = req.items?.filter((i: any) => i.needs_clarification || i.confidence < 0.6) || [];

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-label-1">Заявка RFQ-{req.code}</h1>
        <p className="text-label-3 text-sm mt-0.5">Статус: {statusLabels[req.status] || req.status}</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-[var(--danger-soft)] border border-[var(--separator)] text-[var(--danger)] rounded-[var(--radius-lg)] text-sm" role="alert">
          {error}
        </div>
      )}

      {/* Clarifications box */}
      {clarifications.length > 0 && (
        <div className="bg-[var(--warning-soft)] border border-[var(--separator)] rounded-[var(--radius-lg)] p-6 mb-6" role="alert">
          <h2 className="font-semibold text-[var(--warning)] text-base mb-3">
            Требуются уточнения ({clarifications.length})
          </h2>
          <ul className="space-y-2">
            {clarifications.map((q: string, i: number) => (
              <li key={i} className="flex gap-2 text-label-1 text-sm">
                <span className="text-[var(--warning)] mt-0.5" aria-hidden="true">?</span>
                <span>{q}</span>
              </li>
            ))}
          </ul>
          <p className="text-[var(--warning)] text-xs mt-3">
            Уточните детали у заказчика перед подтверждением заявки
          </p>
        </div>
      )}

      {/* Raw text */}
      <Card title="Исходный текст" className="mb-6">
        <div className="bg-[var(--fill-1)] rounded-[var(--radius-md)] p-4 text-sm text-label-2 whitespace-pre-wrap">
          {req.raw_text || "(пусто)"}
        </div>
        <div className="mt-4 flex gap-3 flex-wrap">
          {(req.status === "draft" || req.status === "parsing") && (
            <Button
              variant="primary" size={44}
              onClick={handleParse}
              loading={actionLoading === "parse"}
              leftIcon={<IconSparkles className="w-5 h-5" />}
            >
              {actionLoading === "parse" ? "Распознаём..." : "Распознать материалы"}
            </Button>
          )}
          {req.status === "parsing" && req.items?.length > 0 && (
            <Button
              variant="secondary" size={44}
              onClick={handleConfirm}
              loading={actionLoading === "confirm"}
            >
              {actionLoading === "confirm" ? "Подтверждаем..." : "Подтвердить позиции"}
            </Button>
          )}
        </div>
      </Card>

      {/* Items table */}
      {req.items && req.items.length > 0 && (
        <Card
          title={"Распознанные позиции (" + req.items.length + ")"}
          subtitle={itemsNeedClarification.length > 0 ? itemsNeedClarification.length + " требуют уточнения" : undefined}
          className="mb-6" padding={false}
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm min-w-[560px]">
              <thead className="border-b border-separator">
                <tr>
                  <th scope="col" className="px-6 py-3 font-medium text-label-3 text-xs">Материал</th>
                  <th scope="col" className="px-3 py-3 font-medium text-label-3 text-xs">Категория</th>
                  <th scope="col" className="px-3 py-3 font-medium text-label-3 text-xs text-right">Кол-во</th>
                  <th scope="col" className="px-3 py-3 font-medium text-label-3 text-xs">Ед.</th>
                  <th scope="col" className="px-3 py-3 font-medium text-label-3 text-xs">Бренд</th>
                  <th scope="col" className="px-6 py-3 font-medium text-label-3 text-xs text-center">Точность</th>
                </tr>
              </thead>
              <tbody>
                {req.items.map((item: any) => (
                  <tr key={item.id} className={"border-b border-[var(--fill-1)] " + (item.needs_clarification ? "bg-[var(--warning-soft)]" : "")}>
                    <td className="px-6 py-2.5 text-label-1">
                      {item.needs_clarification && <span className="text-[var(--warning)] mr-1" title="Требует уточнения" role="img" aria-label="Требует уточнения">⚠</span>}
                      {item.name}
                    </td>
                    <td className="px-3 py-2.5 text-label-3">{item.category_name || "-"}</td>
                    <td className="px-3 py-2.5 text-right text-label-1 tabular-nums">{item.quantity}</td>
                    <td className="px-3 py-2.5 text-label-3">{item.unit_name || "-"}</td>
                    <td className="px-3 py-2.5 text-label-3">{item.brand || "-"}</td>
                    <td className="px-6 py-2.5 text-center">
                      <ConfBadge confidence={item.confidence || 0} needsClarification={item.needs_clarification} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <div className="flex gap-3">
        <Link href={"/lk/requests/" + id + "/competitive"}
          className={buttonClass({ variant: "primary", size: 44 })}>
          <IconChart className="w-5 h-5" /> Конкурентный лист
        </Link>
      </div>
    </div>
  );
}

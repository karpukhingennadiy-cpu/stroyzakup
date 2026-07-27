"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getRequest, parseRequest, confirmRequest } from "@/lib/api";
import { IconChart, IconSparkles } from "@/components/icons";

const statusLabels: Record<string, string> = {
  draft: "Черновик", parsing: "Распознавание", confirmed: "Подтверждена",
  matched: "Поставщики подобраны", matching: "Поиск поставщиков",
  rfq_sent: "РФК отправлены", collecting_quotes: "Сбор КП",
  ready: "Готов к сравнению", completed: "Завершена", cancelled: "Отменена",
};

function ConfBadge({ confidence, needsClarification }: { confidence: number; needsClarification?: boolean }) {
  const pct = Math.round(confidence * 100);
  let bg = "bg-green-100 text-green-700";
  if (needsClarification || pct < 60) bg = "bg-amber-100 text-amber-700";
  if (pct < 40) bg = "bg-red-100 text-red-700";
  return (
    <span className={"px-2 py-0.5 rounded-full text-xs font-medium " + bg}>
      {pct}%
    </span>
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
    getRequest(id).then((data) => {
      setReq(data);
      setClarifications(data.clarifications || []);
    }).catch((e) => setError(e.message)).finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, [id]);

  const handleParse = async () => {
    setActionLoading("parse");
    setError("");
    try {
      const result = await parseRequest(id);
      setReq(result);
      setClarifications(result.clarifications || []);
    } catch (e: any) { setError(e.message); }
    finally { setActionLoading(""); }
  };

  const handleConfirm = async () => {
    setActionLoading("confirm");
    setError("");
    try {
      const result = await confirmRequest(id);
      setReq(result.request || result);
    } catch (e: any) { setError(e.message); }
    finally { setActionLoading(""); }
  };

  if (loading) return <div className="p-8 text-[#64748b] text-lg">Загрузка заявки...</div>;
  if (error) return <div className="p-8 text-red-600">Ошибка: {error}</div>;
  if (!req) return <div className="p-8 text-[#64748b]">Заявка не найдена</div>;

  const itemsNeedClarification = req.items?.filter((i: any) => i.needs_clarification || i.confidence < 0.6) || [];

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#1a1a2e]">Заявка RFQ-{req.code}</h1>
        <p className="text-[#64748b] mt-1">Статус: {statusLabels[req.status] || req.status}</p>
      </div>

      {/* Clarifications box */}
      {clarifications.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 mb-6">
          <h2 className="font-bold text-amber-800 text-lg mb-3">
            ⚠ Требуются уточнения ({clarifications.length})
          </h2>
          <ul className="space-y-2">
            {clarifications.map((q: string, i: number) => (
              <li key={i} className="flex gap-2 text-amber-900 text-sm">
                <span className="text-amber-500 mt-0.5">?</span>
                <span>{q}</span>
              </li>
            ))}
          </ul>
          <p className="text-amber-600 text-xs mt-3">
            Уточните детали у заказчика перед подтверждением заявки
          </p>
        </div>
      )}

      {/* Raw text */}
      <div className="bg-white rounded-2xl border border-[#e2e8f0] p-8 mb-6">
        <h2 className="font-bold text-lg text-[#1a1a2e] mb-4">Исходный текст</h2>
        <div className="bg-[#f5f7fa] rounded-xl p-4 text-sm text-[#64748b] whitespace-pre-wrap">
          {req.raw_text || "(пусто)"}
        </div>
        <div className="mt-4 flex gap-3 flex-wrap">
          {(req.status === "draft" || req.status === "parsing") && (
            <button onClick={handleParse} disabled={actionLoading === "parse"}
              className="px-5 py-2.5 bg-[#27ae60] text-white rounded-xl font-semibold text-sm hover:bg-[#219a52] transition disabled:opacity-50 flex items-center gap-2">
              <IconSparkles className="w-4 h-4" />
              {actionLoading === "parse" ? "Распознаём..." : "Распознать материалы"}
            </button>
          )}
          {req.status === "parsing" && req.items?.length > 0 && (
            <button onClick={handleConfirm} disabled={actionLoading === "confirm"}
              className="px-5 py-2.5 bg-[#f0a500] text-[#1a1a2e] rounded-xl font-bold text-sm hover:bg-[#fcc419] transition disabled:opacity-50">
              {actionLoading === "confirm" ? "Подтверждаем..." : "Подтвердить позиции"}
            </button>
          )}
        </div>
      </div>

      {/* Items table */}
      {req.items && req.items.length > 0 && (
        <div className="bg-white rounded-2xl border border-[#e2e8f0] p-8 mb-6">
          <h2 className="font-bold text-lg text-[#1a1a2e] mb-4">
            Распознанные позиции ({req.items.length})
            {itemsNeedClarification.length > 0 && (
              <span className="ml-2 text-amber-600 text-sm font-normal">
                — {itemsNeedClarification.length} требуют уточнения
              </span>
            )}
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-[#e2e8f0]">
                <tr>
                  <th className="py-2 font-semibold text-[#64748b]">Материал</th>
                  <th className="py-2 font-semibold text-[#64748b]">Категория</th>
                  <th className="py-2 font-semibold text-[#64748b] text-right">Кол-во</th>
                  <th className="py-2 font-semibold text-[#64748b]">Ед.</th>
                  <th className="py-2 font-semibold text-[#64748b]">Бренд</th>
                  <th className="py-2 font-semibold text-[#64748b] text-center">Точность</th>
                </tr>
              </thead>
              <tbody>
                {req.items.map((item: any) => (
                  <tr key={item.id} className={"border-b border-[#f5f7fa] " + (item.needs_clarification ? "bg-amber-50/50" : "")}>
                    <td className="py-2.5">
                      {item.needs_clarification && <span className="text-amber-500 mr-1" title="Требует уточнения">⚠</span>}
                      {item.name}
                    </td>
                    <td className="py-2.5 text-[#64748b]">{item.category_name || "-"}</td>
                    <td className="py-2.5 text-right">{item.quantity}</td>
                    <td className="py-2.5 text-[#64748b]">{item.unit_name || "-"}</td>
                    <td className="py-2.5 text-[#64748b]">{item.brand || "-"}</td>
                    <td className="py-2.5 text-center">
                      <ConfBadge confidence={item.confidence || 0} needsClarification={item.needs_clarification} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <Link href={"/lk/requests/" + id + "/competitive"}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#f0a500] text-[#1a1a2e] rounded-xl font-bold text-sm hover:bg-[#fcc419] transition">
          <IconChart className="w-4 h-4" /> Конкурентный лист
        </Link>
      </div>
    </div>
  );
}

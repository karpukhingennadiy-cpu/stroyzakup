"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getRequest, parseRequest } from "@/lib/api";
import { IconChart } from "@/components/icons";

const statusLabels: Record<string, string> = {
  draft: "Черновик", parsing: "Распознавание", confirmed: "Подтверждена",
  matching: "Поиск поставщиков", rfq_sent: "РФК отправлены", collecting_quotes: "Сбор КП",
  ready: "Готов к сравнению", completed: "Завершена", cancelled: "Отменена",
};

export default function RequestDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [req, setReq] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState("");
  const [error, setError] = useState("");

  const load = () => {
    getRequest(id).then(setReq).catch((e) => setError(e.message)).finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, [id]);

  const handleParse = async () => {
    setActionLoading("parse");
    try { await parseRequest(id); load(); }
    catch (e: any) { setError(e.message); }
    finally { setActionLoading(""); }
  };

  if (loading) return <div className="p-8 text-[#64748b] text-lg">Загрузка заявки...</div>;
  if (error) return <div className="p-8 text-red-600">Ошибка: {error}</div>;
  if (!req) return <div className="p-8 text-[#64748b]">Заявка не найдена</div>;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#1a1a2e]">Заявка RFQ-{req.code}</h1>
        <p className="text-[#64748b] mt-1">Статус: {statusLabels[req.status] || req.status}</p>
      </div>

      <div className="bg-white rounded-2xl border border-[#e2e8f0] p-8 mb-6">
        <h2 className="font-bold text-lg text-[#1a1a2e] mb-4">Исходный текст</h2>
        <div className="bg-[#f5f7fa] rounded-xl p-4 text-sm text-[#64748b] whitespace-pre-wrap">{req.raw_text || "(пусто)"}</div>
        <div className="mt-4 flex gap-3">
          {req.status === "draft" && (
            <button onClick={handleParse} disabled={actionLoading === "parse"}
              className="px-5 py-2.5 bg-[#27ae60] text-white rounded-xl font-semibold text-sm hover:bg-[#219a52] transition disabled:opacity-50">
              {actionLoading === "parse" ? "Распознаём..." : "Распознать материалы"}
            </button>
          )}
        </div>
      </div>

      {req.items && req.items.length > 0 && (
        <div className="bg-white rounded-2xl border border-[#e2e8f0] p-8 mb-6">
          <h2 className="font-bold text-lg text-[#1a1a2e] mb-4">Распознанные позиции ({req.items.length})</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-[#e2e8f0]">
                <tr>
                  <th className="py-2 font-semibold text-[#64748b]">Материал</th>
                  <th className="py-2 font-semibold text-[#64748b]">Категория</th>
                  <th className="py-2 font-semibold text-[#64748b] text-right">Кол-во</th>
                  <th className="py-2 font-semibold text-[#64748b]">Ед.</th>
                  <th className="py-2 font-semibold text-[#64748b]">Бренд</th>
                </tr>
              </thead>
              <tbody>
                {req.items.map((item: any) => (
                  <tr key={item.id} className="border-b border-[#f5f7fa]">
                    <td className="py-2.5">{item.name}</td>
                    <td className="py-2.5 text-[#64748b]">{item.category_name || "-"}</td>
                    <td className="py-2.5 text-right">{item.quantity}</td>
                    <td className="py-2.5 text-[#64748b]">{item.unit_name || "-"}</td>
                    <td className="py-2.5 text-[#64748b]">{item.brand || "-"}</td>
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

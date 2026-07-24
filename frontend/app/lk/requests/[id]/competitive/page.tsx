"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getCompetitiveSheet } from "@/lib/api";
import { IconChart } from "@/components/icons";

export default function CompetitivePage() {
  const params = useParams();
  const id = params.id as string;
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getCompetitiveSheet(id)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="p-8 text-[#64748b] text-lg">Загрузка конкурентного листа...</div>;
  if (error) return <div className="p-8 text-red-600">Ошибка: {error}</div>;

  const suppliers = data?.suppliers || [];
  const best = data?.best;

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#1a1a2e]">Конкурентный лист</h1>
        <p className="text-[#64748b] mt-1">Сравнение коммерческих предложений — {suppliers.length} поставщиков</p>
      </div>

      {suppliers.length === 0 ? (
        <div className="bg-white rounded-2xl border border-[#e2e8f0] p-16 text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-[#1e3a5f]/5 flex items-center justify-center">
            <IconChart className="w-10 h-10 text-[#1e3a5f]" />
          </div>
          <h2 className="text-xl font-bold text-[#1a1a2e] mb-2">Ожидайте предложения</h2>
          <p className="text-[#64748b] max-w-md mx-auto">После отправки запросов КП здесь появится сравнение цен от поставщиков.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-[#e2e8f0] shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-[#f5f7fa] border-b border-[#e2e8f0]">
                  <th className="px-6 py-4 text-xs font-semibold text-[#64748b] uppercase tracking-wider">Поставщик</th>
                  <th className="px-6 py-4 text-xs font-semibold text-[#64748b] uppercase tracking-wider text-right">Материалы</th>
                  <th className="px-6 py-4 text-xs font-semibold text-[#64748b] uppercase tracking-wider text-right">Доставка</th>
                  <th className="px-6 py-4 text-xs font-semibold text-[#64748b] uppercase tracking-wider text-right">Итого</th>
                  <th className="px-6 py-4 text-xs font-semibold text-[#64748b] uppercase tracking-wider">Оплата</th>
                  <th className="px-6 py-4 text-xs font-semibold text-[#64748b] uppercase tracking-wider">Срок</th>
                </tr>
              </thead>
              <tbody>
                {suppliers.map((s: any, i: number) => {
                  const isBest = best && s.supplier_id === best.supplier_id;
                  return (
                    <tr key={i} className={"border-b border-[#f5f7fa] " + (isBest ? "bg-green-50/50" : "")}>
                      <td className="px-6 py-4">
                        <span className="font-semibold text-[#1a1a2e]">{s.supplier_name}</span>
                        {isBest && <span className="ml-2 text-xs px-2 py-0.5 bg-[#27ae60] text-white rounded-full">Лучшее</span>}
                      </td>
                      <td className="px-6 py-4 text-right">{s.materials_total?.toLocaleString("ru-RU")} ₽</td>
                      <td className="px-6 py-4 text-right">{s.delivery?.toLocaleString("ru-RU")} ₽</td>
                      <td className="px-6 py-4 text-right font-bold text-[#1a1a2e]">{s.grand_total?.toLocaleString("ru-RU")} ₽</td>
                      <td className="px-6 py-4 text-sm text-[#64748b]">{s.payment_terms || "-"}</td>
                      <td className="px-6 py-4 text-sm text-[#64748b]">{s.delivery_time || "-"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

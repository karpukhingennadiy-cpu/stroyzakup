"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getCompetitiveSheet } from "@/lib/api";
import { IconChart } from "@/components/icons";
import { Card, Badge } from "@/components/ui";

export default function CompetitivePage() {
  const params = useParams();
  const id = params.id as string;
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getCompetitiveSheet(Number(id))
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="p-8 text-label-3 text-base" role="status">Загрузка конкурентного листа...</div>;
  if (error) return <div className="p-8 text-[var(--danger)]" role="alert">Ошибка: {error}</div>;

  const suppliers = data?.suppliers || [];
  const best = data?.best;
  const maxTotal = suppliers.reduce((m: number, s: any) => Math.max(m, s.grand_total || 0), 0);

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-label-1">Конкурентный лист</h1>
        <p className="text-label-3 text-sm mt-0.5">Сравнение коммерческих предложений — {suppliers.length} поставщиков</p>
      </div>

      {suppliers.length === 0 ? (
        <Card padding={false} className="p-16 text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-[var(--radius-xl)] bg-[var(--accent-soft)] flex items-center justify-center">
            <IconChart className="w-10 h-10 text-[var(--accent)]" />
          </div>
          <h2 className="text-xl font-semibold text-label-1 mb-2">Ожидайте предложения</h2>
          <p className="text-label-3 max-w-md mx-auto text-sm">После отправки запросов КП здесь появится сравнение цен от поставщиков.</p>
        </Card>
      ) : (
        <Card padding={false}>
          <div className="overflow-x-auto">
            <table className="w-full text-left min-w-[720px]">
              <thead>
                <tr className="bg-[var(--fill-1)] border-b border-separator">
                  <th scope="col" className="px-6 py-3 text-xs font-medium text-label-3">Поставщик</th>
                  <th scope="col" className="px-4 py-3 text-xs font-medium text-label-3 text-right">Материалы</th>
                  <th scope="col" className="px-4 py-3 text-xs font-medium text-label-3 text-right">Доставка</th>
                  <th scope="col" className="px-4 py-3 text-xs font-medium text-label-3 text-right">Итого</th>
                  <th scope="col" className="px-4 py-3 text-xs font-medium text-label-3">Сравнение</th>
                  <th scope="col" className="px-4 py-3 text-xs font-medium text-label-3">Оплата</th>
                  <th scope="col" className="px-6 py-3 text-xs font-medium text-label-3">Срок</th>
                </tr>
              </thead>
              <tbody>
                {suppliers.map((s: any, i: number) => {
                  const isBest = best && s.supplier_id === best.supplier_id;
                  const widthPct = maxTotal > 0 ? Math.max(3, ((s.grand_total || 0) / maxTotal) * 100) : 3;
                  return (
                    <tr key={i} className={"border-b border-[var(--fill-1)] " + (isBest ? "bg-[var(--success-soft)]" : "")}>
                      <td className="px-6 py-4">
                        <span className="font-medium text-label-1">{s.supplier_name}</span>
                        {isBest && <Badge tone="success" className="ml-2">Лучшее</Badge>}
                      </td>
                      <td className="px-4 py-4 text-right text-label-2 tabular-nums">{s.materials_total?.toLocaleString("ru-RU")} ₽</td>
                      <td className="px-4 py-4 text-right text-label-2 tabular-nums">{s.delivery?.toLocaleString("ru-RU")} ₽</td>
                      <td className="px-4 py-4 text-right font-semibold text-label-1 tabular-nums">{s.grand_total?.toLocaleString("ru-RU")} ₽</td>
                      <td className="px-4 py-4 w-40">
                        <div className="h-2 rounded-full bg-[var(--fill-1)] overflow-hidden" role="img"
                          aria-label={s.supplier_name + ": " + (s.grand_total || 0).toLocaleString("ru-RU") + " рублей"}>
                          <div className="h-full rounded-full" style={{ width: widthPct + "%", backgroundColor: isBest ? "var(--success)" : "var(--accent)" }} />
                        </div>
                      </td>
                      <td className="px-4 py-4 text-sm text-label-3">{s.payment_terms || "-"}</td>
                      <td className="px-6 py-4 text-sm text-label-3">{s.delivery_time || "-"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}

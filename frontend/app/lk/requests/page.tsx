"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { getRequests } from "@/lib/api";
import { IconPlus, IconList } from "@/components/icons";

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

  if (loading) return <div className="text-[#64748b] text-lg p-8">Загрузка заявок...</div>;
  if (error) return <div className="p-8 text-red-600">Ошибка: {error}</div>;

  if (requests.length === 0) {
    return (
      <div>
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-[#1a1a2e]">Мои заявки</h1>
            <p className="text-[#64748b] mt-1">Управляйте закупками стройматериалов</p>
          </div>
          <Link href="/lk/requests/new"
            className="flex items-center gap-2 px-5 py-3 bg-[#1e3a5f] text-white rounded-xl font-semibold hover:bg-[#2d5a8e] hover:shadow-lg transition">
            <IconPlus className="w-5 h-5" /> Новая заявка
          </Link>
        </div>
        <div className="bg-white rounded-2xl border border-[#e2e8f0] p-16 text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-[#1e3a5f]/5 flex items-center justify-center">
            <IconList className="w-10 h-10 text-[#1e3a5f]" />
          </div>
          <h2 className="text-xl font-bold text-[#1a1a2e] mb-2">Нет заявок</h2>
          <p className="text-[#64748b] mb-6 max-w-md mx-auto">
            Создайте первую заявку — сервис найдёт поставщиков и сравнит цены.
          </p>
          <Link href="/lk/requests/new"
            className="inline-flex items-center gap-2 px-6 py-3 bg-[#f0a500] text-[#1a1a2e] rounded-xl font-bold hover:bg-[#fcc419] transition">
            <IconPlus className="w-5 h-5" /> Создать заявку
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-[#1a1a2e]">Мои заявки</h1>
          <p className="text-[#64748b] mt-1">{requests.length} заявок</p>
        </div>
        <Link href="/lk/requests/new"
          className="flex items-center gap-2 px-5 py-3 bg-[#1e3a5f] text-white rounded-xl font-semibold hover:bg-[#2d5a8e] hover:shadow-lg transition">
          <IconPlus className="w-5 h-5" /> Новая заявка
        </Link>
      </div>
      <div className="space-y-3">
        {requests.map((req: any) => (
          <Link key={req.id} href={"/lk/requests/" + req.id}
            className="block bg-white p-5 rounded-xl border border-[#e2e8f0] hover:shadow-md hover:border-[#1e3a5f]/30 transition">
            <div className="flex justify-between items-start">
              <div>
                <span className="font-mono font-bold text-[#1e3a5f]">RFQ-{req.code}</span>
                <span className="ml-3 text-xs px-2 py-0.5 bg-[#f5f7fa] rounded-full text-[#64748b]">{req.status}</span>
              </div>
              <span className="text-xs text-[#94a3b8]">{new Date(req.created_at).toLocaleDateString("ru-RU")}</span>
            </div>
            {req.raw_text && (
              <p className="text-sm text-[#64748b] mt-2 truncate">{req.raw_text.slice(0, 120)}</p>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}

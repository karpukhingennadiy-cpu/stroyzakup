"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { createRequest } from "@/lib/api";
import { IconPlus, IconHardHat } from "@/components/icons";

export default function NewRequestPage() {
  const router = useRouter();
  const [rawText, setRawText] = useState("");
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawText.trim()) return;
    setError("");
    setLoading(true);
    try {
      const req = await createRequest(rawText, comment || undefined);
      router.push("/lk/requests/" + req.id);
    } catch (err: any) {
      setError(err.message || "Ошибка создания заявки");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#1a1a2e]">Новая заявка</h1>
        <p className="text-[#64748b] mt-1">Вставьте список материалов — система распознает позиции автоматически</p>
      </div>

      <div className="bg-white rounded-2xl border border-[#e2e8f0] shadow-sm overflow-hidden">
        <div className="p-6 border-b border-[#e2e8f0] bg-[#f5f7fa]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#1e3a5f]/10 flex items-center justify-center">
              <IconHardHat className="w-5 h-5 text-[#1e3a5f]" />
            </div>
            <div>
              <p className="font-semibold text-[#1a1a2e]">Список материалов</p>
              <p className="text-xs text-[#64748b]">Можно вставлять из Excel, сметы или писать вручную</p>
            </div>
          </div>
        </div>

        {error && (
          <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <textarea value={rawText} onChange={(e) => setRawText(e.target.value)}
            required rows={10}
            placeholder="Керамогранит серый 600x600 — 150 м² | Плиточный клей KNAUF Fliesen 25 кг — 100 мешков | Доставка: г. Подольск"
            className="w-full px-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition resize-y text-sm leading-relaxed" />

          <input value={comment} onChange={(e) => setComment(e.target.value)}
            type="text" placeholder="Комментарий (необязательно)"
            className="w-full px-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition" />

          <button type="submit" disabled={loading || !rawText.trim()}
            className="w-full flex items-center justify-center gap-2 py-3.5 bg-[#f0a500] text-[#1a1a2e] rounded-xl font-bold text-base hover:bg-[#fcc419] hover:shadow-lg transition disabled:opacity-50">
            <IconPlus className="w-5 h-5" />
            {loading ? "Создаём..." : "Создать заявку"}
          </button>
        </form>
      </div>
    </div>
  );
}

import Link from "next/link";
import { IconPlus, IconList } from "@/components/icons";

export default function RequestsPage() {
  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-[#1a1a2e]">Мои заявки</h1>
          <p className="text-[#64748b] mt-1">Управляйте закупками стройматериалов</p>
        </div>
        <Link href="/lk/requests/new"
          className="flex items-center gap-2 px-5 py-3 bg-[#1e3a5f] text-white rounded-xl font-semibold hover:bg-[#2d5a8e] hover:shadow-lg transition">
          <IconPlus className="w-5 h-5" />
          Новая заявка
        </Link>
      </div>

      {/* Empty state */}
      <div className="bg-white rounded-2xl border border-[#e2e8f0] p-16 text-center">
        <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-[#1e3a5f]/5 flex items-center justify-center">
          <IconList className="w-10 h-10 text-[#1e3a5f]" />
        </div>
        <h2 className="text-xl font-bold text-[#1a1a2e] mb-2">Нет заявок</h2>
        <p className="text-[#64748b] mb-6 max-w-md mx-auto">
          Создайте первую заявку на закупку материалов — сервис автоматически найдёт поставщиков и сравнит цены.
        </p>
        <Link href="/lk/requests/new"
          className="inline-flex items-center gap-2 px-6 py-3 bg-[#f0a500] text-[#1a1a2e] rounded-xl font-bold hover:bg-[#fcc419] transition">
          <IconPlus className="w-5 h-5" />
          Создать заявку
        </Link>
      </div>
    </div>
  );
}
import { IconTruck, IconSearch } from "@/components/icons";

export default function SuppliersPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#1a1a2e]">Поставщики</h1>
        <p className="text-[#64748b] mt-1">База проверенных поставщиков стройматериалов</p>
      </div>

      {/* Search bar */}
      <div className="bg-white rounded-2xl border border-[#e2e8f0] p-4 mb-6">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <IconSearch className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#94a3b8]" />
            <input type="text" placeholder="Поиск по названию или городу..."
              className="w-full pl-12 pr-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition" />
          </div>
          <button className="px-6 py-3 bg-[#1e3a5f] text-white rounded-xl font-semibold hover:bg-[#2d5a8e] transition">
            Найти
          </button>
        </div>
      </div>

      {/* Empty state */}
      <div className="bg-white rounded-2xl border border-[#e2e8f0] p-16 text-center">
        <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-[#1e3a5f]/5 flex items-center justify-center">
          <IconTruck className="w-10 h-10 text-[#1e3a5f]" />
        </div>
        <h2 className="text-xl font-bold text-[#1a1a2e] mb-2">Поставщики появятся здесь</h2>
        <p className="text-[#64748b] max-w-md mx-auto">
          Создайте заявку — система автоматически найдёт поставщиков в радиусе вашего объекта и покажет их здесь.
        </p>
      </div>
    </div>
  );
}
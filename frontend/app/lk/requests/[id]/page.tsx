import { IconChart } from "@/components/icons";

export default function RequestDetailPage() {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#1a1a2e]">Заявка RFQ-XXXXXX</h1>
        <p className="text-[#64748b] mt-1">Статус: Черновик</p>
      </div>

      <div className="bg-white rounded-2xl border border-[#e2e8f0] p-8 mb-6">
        <h2 className="font-bold text-lg text-[#1a1a2e] mb-4">Исходный текст</h2>
        <div className="bg-[#f5f7fa] rounded-xl p-4 text-sm text-[#64748b] whitespace-pre-wrap">
          Керамогранит серый 600×600 — 150 м² | Плиточный клей KNAUF — 100 мешков | г. Подольск
        </div>
        <div className="mt-4 flex gap-3">
          <button className="px-5 py-2.5 bg-[#27ae60] text-white rounded-xl font-semibold text-sm hover:bg-[#219a52] transition">
            Распознать материалы
          </button>
          <button className="px-5 py-2.5 bg-[#1e3a5f] text-white rounded-xl font-semibold text-sm hover:bg-[#2d5a8e] transition">
            Найти поставщиков
          </button>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-[#e2e8f0] p-8">
        <h2 className="font-bold text-lg text-[#1a1a2e] mb-4">Распознанные позиции</h2>
        <p className="text-[#64748b] text-sm">После распознавания здесь появятся позиции с ценами от поставщиков.</p>
        <div className="mt-6 flex justify-end">
          <a href="./competitive"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#f0a500] text-[#1a1a2e] rounded-xl font-bold text-sm hover:bg-[#fcc419] transition">
            <IconChart className="w-4 h-4" />
            Конкурентный лист
          </a>
        </div>
      </div>
    </div>
  );
}
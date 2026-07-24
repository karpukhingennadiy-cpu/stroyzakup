import { IconPlus, IconHardHat } from "@/components/icons";

export default function NewRequestPage() {
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

        <form className="p-6 space-y-5">
          <div>
            <textarea name="raw_text" required rows={10}
              placeholder="Керамогранит серый 600x600 — 150 м² | Плиточный клей KNAUF Fliesen 25 кг — 100 мешков | Доставка: г. Подольск"
              className="w-full px-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition resize-y text-sm leading-relaxed" />
          </div>

          <div>
            <label className="block text-sm font-semibold text-[#1a1a2e] mb-1.5">Комментарий</label>
            <input name="comment" type="text"
              placeholder="Например: срочная закупка, нужна доставка до пятницы"
              className="w-full px-4 py-3 bg-[#f5f7fa] border border-[#e2e8f0] rounded-xl focus:bg-white focus:border-[#1e3a5f] transition" />
          </div>

          <button type="submit"
            className="w-full flex items-center justify-center gap-2 py-3.5 bg-[#f0a500] text-[#1a1a2e] rounded-xl font-bold text-base hover:bg-[#fcc419] hover:shadow-lg transition">
            <IconPlus className="w-5 h-5" />
            Создать заявку
          </button>
        </form>
      </div>
    </div>
  );
}
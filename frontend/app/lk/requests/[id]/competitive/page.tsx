import { IconChart } from "@/components/icons";

export default function CompetitivePage() {
  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#1a1a2e]">Конкурентный лист</h1>
        <p className="text-[#64748b] mt-1">Сравнение коммерческих предложений от поставщиков</p>
      </div>

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
              <tr>
                <td colSpan={6} className="px-6 py-16 text-center">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[#1e3a5f]/5 flex items-center justify-center">
                    <IconChart className="w-8 h-8 text-[#1e3a5f]" />
                  </div>
                  <p className="text-[#64748b] font-medium">Ожидайте предложения от поставщиков</p>
                  <p className="text-[#94a3b8] text-sm mt-1">После отправки запросов КП здесь появится сравнение цен</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
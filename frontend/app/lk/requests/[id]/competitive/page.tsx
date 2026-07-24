export default function CompetitiveSheetPage() {
  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Konkurentnyj list</h1>
      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-sm font-medium">Postavshchik</th>
              <th className="px-4 py-3 text-sm font-medium text-right">Materialy</th>
              <th className="px-4 py-3 text-sm font-medium text-right">Dostavka</th>
              <th className="px-4 py-3 text-sm font-medium text-right">Itogo</th>
              <th className="px-4 py-3 text-sm font-medium">Oplata</th>
              <th className="px-4 py-3 text-sm font-medium">Srok</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">
              Ozhidajte predlozheniya ot postavshchikov. Oni otobrazyatsya zdes posle polucheniya KP.
            </td></tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}

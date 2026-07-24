export default function SuppliersPage() {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Postavshchiki</h1>
      <div className="bg-white rounded-lg border p-6 shadow-sm">
        <div className="flex gap-4 mb-4">
          <input type="text" placeholder="Poisk po nazvaniyu..." 
            className="flex-1 px-4 py-2 border rounded-lg" />
          <input type="text" placeholder="Gorod" 
            className="w-48 px-4 py-2 border rounded-lg" />
          <button className="px-6 py-2 bg-blue-600 text-white rounded-lg">Nayti</button>
        </div>
        <p className="text-gray-500 text-sm mt-4">
          Dlya poiska postavshchikov sozdayte zayavku — sistema avtomaticheski naydyot postavshchikov v radiuse vashego obekta.
        </p>
      </div>
    </div>
  )
}

export default function NewRequestPage() {
  return <div className="max-w-2xl mx-auto">
    <h1 className="text-2xl font-bold mb-4">Novaya zayavka</h1>
    <form className="bg-white border rounded-lg p-6 space-y-4">
      <textarea rows={8} placeholder="Keramogranit 600x600 - 150 m2 | g. Podolsk" className="w-full px-3 py-2 border rounded-lg" />
      <button type="submit" className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold">Sozdat zayavku</button>
    </form>
  </div>;
}
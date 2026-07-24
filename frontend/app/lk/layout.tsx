import Link from "next/link";

export default function LkLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-white border-r border-gray-200 p-4">
        <Link href="/" className="text-lg font-bold text-blue-600">StroyZakup</Link>
        <nav className="mt-4 space-y-2">
          <Link href="/lk/requests" className="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-100 text-sm">Zayavki</Link>
          <Link href="/lk/requests/new" className="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-100 text-sm">+ Novaya</Link>
          <Link href="/lk/suppliers" className="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-100 text-sm">Postavshchiki</Link>
        </nav>
      </aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
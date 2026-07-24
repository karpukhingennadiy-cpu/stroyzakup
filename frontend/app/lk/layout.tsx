"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getMe, clearTokens } from "@/lib/api";

export default function LkLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => {
        clearTokens();
        router.push("/login");
      })
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = () => {
    clearTokens();
    router.push("/");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">Zagruzka...</div>
      </div>
    );
  }

  const nav = [
    { href: "/lk/requests", label: "Zayavki" },
    { href: "/lk/requests/new", label: "+ Novaya" },
  ];

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <a href="/" className="text-lg font-bold text-blue-600">StroyZakup</a>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          {nav.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className={}
            >
              {item.label}
            </a>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-200">
          <p className="text-sm text-gray-500 truncate">{user?.email}</p>
          <button
            onClick={handleLogout}
            className="mt-2 w-full py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition"
          >
            Vyyti
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}

"use client";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { getMe, clearTokens } from "@/lib/api";
import { IconList, IconPlus, IconTruck, IconHardHat, IconLogOut } from "@/components/icons";

const navItems = [
  { href: "/lk/requests", label: "Мои заявки", icon: IconList },
  { href: "/lk/requests/new", label: "Новая заявка", icon: IconPlus },
  { href: "/lk/suppliers", label: "Поставщики", icon: IconTruck },
];

export default function LkLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => { clearTokens(); router.push("/login"); })
      .finally(() => setLoading(false));
  }, []);

  // Close the mobile menu on navigation
  useEffect(() => { setMenuOpen(false); }, [pathname]);

  const handleLogout = () => { clearTokens(); router.push("/"); };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f5f7fa]">
        <div className="text-[#64748b] text-lg">Загрузка...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-[#f5f7fa]">
      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 inset-x-0 z-50 h-14 bg-[#1a1a2e] text-white flex items-center gap-3 px-4">
        <button onClick={() => setMenuOpen(!menuOpen)} aria-label="Меню"
          className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-white/10 transition text-xl leading-none">
          {menuOpen ? "✕" : "☰"}
        </button>
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-[#f0a500] flex items-center justify-center">
            <IconHardHat className="w-4 h-4 text-[#1a1a2e]" />
          </div>
          <span className="font-bold tracking-tight">Минитендер</span>
        </Link>
      </div>

      {/* Backdrop for mobile menu */}
      {menuOpen && (
        <div className="md:hidden fixed inset-0 z-40 bg-black/40" onClick={() => setMenuOpen(false)} />
      )}

      <aside className={
        "w-64 bg-[#1a1a2e] text-white flex flex-col fixed inset-y-0 left-0 z-40 transition-transform duration-200 " +
        (menuOpen ? "translate-x-0" : "-translate-x-full") + " md:translate-x-0"
      }>
        <div className="p-6 border-b border-white/10">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#f0a500] flex items-center justify-center">
              <IconHardHat className="w-5 h-5 text-[#1a1a2e]" />
            </div>
            <span className="font-bold text-lg tracking-tight">Минитендер</span>
          </Link>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link key={item.href} href={item.href}
                className={"flex items-center gap-3 px-3 py-2.5 rounded-xl transition text-sm font-medium " +
                  (active ? "bg-white/10 text-white" : "text-white/60 hover:text-white hover:bg-white/10")}>
                <item.icon className="w-5 h-5" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-white/10">
          <div className="px-3 py-2 text-sm text-white/40 truncate">{user?.email || ""}</div>
          <button onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-white/40 hover:text-white/70 hover:bg-white/5 transition text-sm mt-1">
            <IconLogOut className="w-5 h-5" />
            Выйти
          </button>
        </div>
      </aside>
      <main className="flex-1 md:ml-64 p-4 pt-20 md:p-8 w-full min-w-0">{children}</main>
    </div>
  );
}

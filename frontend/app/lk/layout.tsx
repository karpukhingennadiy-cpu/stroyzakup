"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { HardHat, ListPlus, Truck, LogOut, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme";
import { getMe } from "@/lib/api";

const navItems = [
  { href: "/lk/requests", label: "Мои заявки", icon: ListPlus },
  { href: "/lk/requests/new", label: "Новая заявка", icon: ListPlus },
  { href: "/lk/suppliers", label: "Поставщики", icon: Truck },
];

export default function LkLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    getMe().then(setUser).catch(() => {});
  }, []);

  const handleLogout = async () => {
    
    router.push("/login");
  };

  return (
    <div className="min-h-screen flex bg-[var(--bg-ground)]">
      <a
        href="#lk-main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[1000] focus:px-3 focus:py-2 focus:rounded-md focus:bg-[var(--accent)] focus:text-white"
      >
        К содержимому
      </a>

      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 inset-x-0 z-[500] h-14 glass border-b border-[var(--separator)] flex items-center gap-2 px-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label={menuOpen ? "Закрыть меню" : "Открыть меню"}
          aria-expanded={menuOpen}
          aria-controls="lk-nav"
        >
          {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </Button>
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-[var(--radius-sm)] gradient-bg flex items-center justify-center">
            <HardHat className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold tracking-tight text-[var(--label-primary)]">Минитендер</span>
        </Link>
        <div className="ml-auto">
          <ThemeToggle />
        </div>
      </div>

      {menuOpen && (
        <div
          className="md:hidden fixed inset-0 z-[499] bg-black/40 backdrop-blur-sm"
          onClick={() => setMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside
        id="lk-nav"
        className={
          "w-64 bg-[var(--sidebar-bg)] text-white flex flex-col fixed inset-y-0 left-0 z-[500] transition-transform duration-200 ease-out " +
          (menuOpen ? "translate-x-0" : "-translate-x-full") + " md:translate-x-0"
        }
      >
        <div className="p-6 border-b border-white/10 flex items-center justify-between gap-2">
          <Link href="/" className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-[var(--radius-sm)] gradient-bg flex items-center justify-center shrink-0">
              <HardHat className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight truncate">Минитендер</span>
          </Link>
          <ThemeToggle className="hidden md:inline-flex" />
        </div>

        <nav className="flex-1 p-4 space-y-1" aria-label="Основная навигация">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={
                  "flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-md)] transition-all duration-200 text-sm font-medium " +
                  (active
                    ? "bg-white/12 text-white shadow-sm"
                    : "text-white/50 hover:text-white hover:bg-white/[0.08]")
                }
              >
                <item.icon className="w-5 h-5" aria-hidden="true" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-white/10">
          <div className="px-3 py-2 text-sm text-white/35 truncate" title={user?.email || ""}>
            {user?.email || ""}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-[var(--radius-md)] text-white/35 hover:text-white/60 hover:bg-white/5 transition-all duration-200 text-sm mt-1 justify-start"
          >
            <LogOut className="w-5 h-5" aria-hidden="true" />
            Выйти
          </Button>
        </div>
      </aside>

      <main
        id="lk-main"
        className="flex-1 md:ml-64 p-4 pt-20 md:p-8 w-full min-w-0"
      >
        {children}
      </main>
    </div>
  );
}

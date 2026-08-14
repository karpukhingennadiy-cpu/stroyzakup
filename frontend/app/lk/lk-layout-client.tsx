"use client";

import { Menu, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { getMe, clearTokens } from "@/lib/api";
import { IconList, IconPlus, IconTruck, IconHardHat, IconLogOut } from "@/components/icons";
import { ThemeToggle } from "@/components/theme";

const navItems = [
  { href: "/lk/requests", label: "Мои заявки", icon: IconList },
  { href: "/lk/requests/new", label: "Новая заявка", icon: IconPlus },
  { href: "/lk/suppliers", label: "Поставщики", icon: IconTruck },
];

export function LkLayoutClient({ children }: { children: React.ReactNode }) {
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
  }, [router]);

  // Close the mobile menu on navigation
  useEffect(() => { setMenuOpen(false); }, [pathname]);

  // Escape закрывает мобильное меню (a11y: клавиатурная навигация)
  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setMenuOpen(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [menuOpen]);

  const handleLogout = () => { clearTokens(); router.push("/"); };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg-ground)]">
        <div className="text-sm text-[var(--label-tertiary)]" role="status">Загрузка...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-[var(--bg-ground)]">
      {/* Skip-link для клавиатурной навигации */}
      <a href="#lk-main" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-toast focus:px-3 focus:py-2 focus:rounded-[var(--radius-md)] focus:bg-[var(--accent)] focus:text-white">
        К содержимому
      </a>

      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 inset-x-0 z-header h-14 glass border-b border-[var(--separator)] text-[var(--label-primary)] flex items-center gap-2 px-3">
        <button
          type="button"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label={menuOpen ? "Закрыть меню" : "Открыть меню"}
          aria-expanded={menuOpen}
          aria-controls="lk-nav"
          className="w-10 h-10 flex items-center justify-center rounded-[var(--radius-md)] hover:bg-[var(--fill-1)] transition-colors text-xl leading-none"
        >
          {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-[var(--radius-md)] bg-[var(--accent)] flex items-center justify-center">
            <IconHardHat className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold tracking-tight">Минитендер</span>
        </Link>
        <div className="ml-auto">
          <ThemeToggle variant="sidebar" />
        </div>
      </div>

      {/* Backdrop for mobile menu */}
      {menuOpen && (
        <div className="md:hidden fixed inset-0 z-[calc(var(--z-header)-1)] bg-black/40" onClick={() => setMenuOpen(false)} aria-hidden="true" />
      )}

      <aside
        id="lk-nav"
        className={
          "w-64 bg-[var(--sidebar-bg)] text-white flex flex-col fixed inset-y-0 left-0 z-header transition-transform duration-200 ease-out " +
          (menuOpen ? "translate-x-0" : "-translate-x-full") + " md:translate-x-0"
        }
      >
        <div className="p-5 border-b border-white/10 flex items-center justify-between gap-2">
          <Link href="/" className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-[var(--radius-md)] bg-[var(--accent)] flex items-center justify-center shrink-0 shadow-[var(--shadow-glow)]">
              <IconHardHat className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-base tracking-tight truncate">Минитендер</span>
          </Link>
          <ThemeToggle variant="sidebar" className="hidden md:inline-flex" />
        </div>

        <nav className="flex-1 p-3 space-y-1" aria-label="Основная навигация">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link key={item.href} href={item.href}
                aria-current={active ? "page" : undefined}
                className={"flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-md)] transition-colors text-sm font-medium " +
                  (active ? "bg-[var(--accent)] text-white shadow-[var(--shadow-glow)]" : "text-white/50 hover:text-white hover:bg-white/[0.08]")}>
                <item.icon className="w-5 h-5" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t border-white/10">
          <div className="px-3 py-2 text-sm text-white/35 truncate" title={user?.email || ""}>{user?.email || ""}</div>
          <button type="button" onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-[var(--radius-md)] text-white/35 hover:text-white/60 hover:bg-white/5 transition-colors text-sm mt-1">
            <IconLogOut className="w-5 h-5" />
            Выйти
          </button>
        </div>
      </aside>
      <main id="lk-main" className="flex-1 md:ml-64 p-4 pt-20 md:p-8 w-full min-w-0">{children}</main>
    </div>
  );
}
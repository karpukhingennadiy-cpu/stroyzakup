"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Hammer, Menu, X } from "lucide-react";
import { ThemeToggle } from "@/components/theme";
import { useState } from "react";

export function LandingHeader() {
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="fixed top-4 left-0 right-0 z-header px-4">
      <div className="mx-auto max-w-5xl glass rounded-[var(--radius-full)] px-5 py-3 shadow-small">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-sm)] gradient-bg text-white transition-transform duration-300 group-hover:scale-105">
              <Hammer className="h-4 w-4" />
            </div>
            <span className="text-lg font-semibold tracking-tight text-[var(--label-primary)]">
              Минитендер
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-1" aria-label="Разделы">
            {[
              { href: "#how", label: "Как работает" },
              { href: "#features", label: "Возможности" },
              { href: "#pricing", label: "Тарифы" },
            ].map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="px-3 py-1.5 text-sm font-medium text-[var(--label-secondary)] rounded-[var(--radius-full)] hover:text-[var(--label-primary)] hover:bg-[var(--fill-1)] transition-all duration-200"
              >
                {item.label}
              </a>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-2">
            <ThemeToggle />
            <button
              onClick={() => router.push("/lk")}
              className="px-3 py-1.5 text-sm font-medium text-[var(--label-secondary)] hover:text-[var(--label-primary)] transition-colors"
            >
              Войти
            </button>
            <button
              onClick={() => router.push("/lk/requests/new")}
              className="relative overflow-hidden rounded-[var(--radius-full)] gradient-bg px-4 py-1.5 text-sm font-semibold text-white shadow-small hover:shadow-glow active:scale-[0.97] transition-all duration-200 btn-shimmer"
            >
              Начать бесплатно
            </button>
          </div>

          <button
            className="md:hidden p-2 text-[var(--label-secondary)]"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Меню"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden mt-2 glass rounded-[var(--radius-lg)] p-4 shadow-medium animate-reveal">
          <nav className="flex flex-col gap-1">
            {[
              { href: "#how", label: "Как работает" },
              { href: "#features", label: "Возможности" },
              { href: "#pricing", label: "Тарифы" },
            ].map((item) => (
              <a
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className="px-3 py-2 text-sm font-medium text-[var(--label-secondary)] rounded-[var(--radius-sm)] hover:bg-[var(--fill-1)] hover:text-[var(--label-primary)] transition-colors"
              >
                {item.label}
              </a>
            ))}
            <div className="mt-2 pt-2 border-t border-[var(--separator)] flex flex-col gap-2">
              <button
                onClick={() => router.push("/lk")}
                className="w-full px-3 py-2 text-sm font-medium text-[var(--label-secondary)] hover:text-[var(--label-primary)] transition-colors text-left rounded-[var(--radius-sm)]"
              >
                Войти
              </button>
              <button
                onClick={() => router.push("/lk/requests/new")}
                className="w-full rounded-[var(--radius-sm)] gradient-bg px-3 py-2 text-sm font-semibold text-white text-center"
              >
                Начать бесплатно
              </button>
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}

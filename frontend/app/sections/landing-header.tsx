"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Menu, X } from "lucide-react";
import { useState } from "react";
import { IconHardHat } from "@/components/icons";

export function LandingHeader() {
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--separator)] bg-[var(--glass-bg)] backdrop-blur-sm">
      <div className="mx-auto max-w-6xl px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent)] text-white">
              <IconHardHat className="w-4 h-4" />
            </div>
            <span className="text-base font-semibold tracking-tight text-[var(--label-primary)]">
              Минитендер
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-6" aria-label="Разделы">
            {[
              { href: "#how", label: "Как работает" },
              { href: "#features", label: "Возможности" },
              { href: "#pricing", label: "Тарифы" },
            ].map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="text-sm font-medium text-[var(--label-secondary)] hover:text-[var(--label-primary)]"
              >
                {item.label}
              </a>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-3">
            <button
              onClick={() => router.push("/lk")}
              className="text-sm font-medium text-[var(--label-secondary)] hover:text-[var(--label-primary)]"
            >
              Войти
            </button>
            <button
              onClick={() => router.push("/lk/requests/new")}
              className="rounded-[var(--radius-md)] bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent-hover)]"
            >
              Начать бесплатно
            </button>
          </div>

          <button
            className="md:hidden p-2 text-[var(--label-secondary)] hover:text-[var(--label-primary)]"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Меню"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden border-t border-[var(--separator)] bg-[var(--bg-tertiary)] px-6 py-4">
          <nav className="flex flex-col gap-3">
            {[
              { href: "#how", label: "Как работает" },
              { href: "#features", label: "Возможности" },
              { href: "#pricing", label: "Тарифы" },
            ].map((item) => (
              <a
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className="text-sm font-medium text-[var(--label-secondary)] hover:text-[var(--label-primary)]"
              >
                {item.label}
              </a>
            ))}
            <div className="mt-2 pt-3 border-t border-[var(--separator)] flex flex-col gap-2">
              <button
                onClick={() => router.push("/lk")}
                className="w-full px-3 py-2 text-sm font-medium text-[var(--label-secondary)] text-left"
              >
                Войти
              </button>
              <button
                onClick={() => router.push("/lk/requests/new")}
                className="w-full rounded-[var(--radius-md)] bg-[var(--accent)] px-3 py-2 text-sm font-medium text-white text-center"
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
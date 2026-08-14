"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Hammer, Menu, X } from "lucide-react";
import { useState } from "react";

export function LandingHeader() {
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-neutral-200 bg-white/90 backdrop-blur-sm">
      <div className="mx-auto max-w-6xl px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-neutral-900 text-white">
              <Hammer className="h-4 w-4" />
            </div>
            <span className="text-base font-semibold tracking-tight text-neutral-900">
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
                className="text-sm font-medium text-neutral-500 hover:text-neutral-900"
              >
                {item.label}
              </a>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-3">
            <button
              onClick={() => router.push("/lk")}
              className="text-sm font-medium text-neutral-600 hover:text-neutral-900"
            >
              Войти
            </button>
            <button
              onClick={() => router.push("/lk/requests/new")}
              className="rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-700"
            >
              Начать бесплатно
            </button>
          </div>

          <button
            className="md:hidden p-2 text-neutral-600"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Меню"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden border-t border-neutral-200 bg-white px-6 py-4">
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
                className="text-sm font-medium text-neutral-600 hover:text-neutral-900"
              >
                {item.label}
              </a>
            ))}
            <div className="mt-2 pt-3 border-t border-neutral-100 flex flex-col gap-2">
              <button
                onClick={() => router.push("/lk")}
                className="w-full px-3 py-2 text-sm font-medium text-neutral-600 text-left"
              >
                Войти
              </button>
              <button
                onClick={() => router.push("/lk/requests/new")}
                className="w-full rounded-lg bg-neutral-900 px-3 py-2 text-sm font-medium text-white text-center"
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

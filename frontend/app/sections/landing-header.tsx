"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { ThemeToggle } from "@/components/theme";
import { Hammer } from "lucide-react";

export function LandingHeader() {
  const router = useRouter();
  return (
    <header className="sticky top-0 z-header border-b border-separator bg-[var(--bg-primary)]/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-[var(--radius-sm)] bg-brand text-brand-ink">
            <Hammer className="h-5 w-5" />
          </div>
          <span className="hidden min-[380px]:inline text-xl font-semibold tracking-tight text-label-1">Минитендер</span>
        </Link>
        <nav className="hidden items-center gap-8 md:flex" aria-label="Разделы лендинга">
          <a href="#how" className="text-sm font-medium text-label-2 hover:text-label-1 transition-colors">Как работает</a>
          <a href="#features" className="text-sm font-medium text-label-2 hover:text-label-1 transition-colors">Возможности</a>
          <a href="#pricing" className="text-sm font-medium text-label-2 hover:text-label-1 transition-colors">Тарифы</a>
        </nav>
        <div className="flex items-center gap-2">
          <span className="[&_button]:text-[var(--label-secondary)] [&_button:hover]:bg-[var(--fill-1)] [&_button:hover]:text-[var(--label-primary)]">
            <ThemeToggle />
          </span>
          <button
            onClick={() => router.push("/lk")}
            className="hidden text-sm font-medium text-label-2 hover:text-label-1 transition-colors sm:block px-2 py-2"
          >
            Войти
          </button>
          <button
            onClick={() => router.push("/lk/requests/new")}
            className="rounded-[var(--radius-md)] bg-brand px-3 py-2 text-xs font-semibold text-brand-ink hover:bg-brand-hover active:scale-[0.97] transition-all duration-150 sm:px-4 sm:text-sm"
          >
            Начать бесплатно
          </button>
        </div>
      </div>
    </header>
  );
}

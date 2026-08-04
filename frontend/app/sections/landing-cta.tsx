"use client";

import { useRouter } from "next/navigation";
import { ChevronRight } from "lucide-react";

export function LandingCTA() {
  const router = useRouter();
  return (
    <section className="bg-brand-sidebar py-24">
      <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
        <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">Готовы сэкономить на закупках?</h2>
        <p className="mt-4 text-lg text-white/60">Первые 50 заявок обрабатываются бесплатно. Никаких подписок — только результат.</p>
        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <button
            onClick={() => router.push("/lk/requests/new")}
            className="inline-flex items-center gap-2 rounded-[var(--radius-lg)] bg-brand px-8 py-4 text-base font-semibold text-brand-ink hover:bg-brand-hover active:scale-[0.97] transition-all duration-150"
          >
            Начать бесплатно
            <ChevronRight className="h-5 w-5" />
          </button>
          <a
            href="mailto:info@minitender.ru"
            className="inline-flex items-center gap-2 rounded-[var(--radius-lg)] bg-white/5 px-8 py-4 text-base font-semibold text-white ring-1 ring-white/10 hover:bg-white/10 transition-colors duration-150"
          >
            Связаться с нами
          </a>
        </div>
        <p className="mt-6 text-xs text-white/40">По вопросам корпоративного доступа: info@minitender.ru</p>
      </div>
    </section>
  );
}

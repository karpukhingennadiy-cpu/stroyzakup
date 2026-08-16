"use client";

import { useRouter } from "next/navigation";
import { ChevronRight, Rocket } from "lucide-react";

export function LandingCTA() {
  const router = useRouter();
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-[var(--bg-dark)] to-[var(--bg-dark-elevated)] py-24">
      {/* Янтарное свечение снизу */}
      <div
        className="absolute inset-x-0 bottom-0 h-40 pointer-events-none"
        aria-hidden="true"
        style={{ background: "radial-gradient(60% 100% at 50% 100%, rgba(240, 165, 0, 0.22), transparent 70%)" }}
      />
      <div className="relative mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-[var(--radius-xl)] bg-brand/15 ring-1 ring-brand/30" aria-hidden="true">
          <Rocket className="h-7 w-7 text-brand" />
        </div>
        <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">Готовы сэкономить на закупках?</h2>
        <p className="mt-4 text-lg text-white/60">Первые 50 заявок обрабатываются бесплатно. Никаких подписок — только результат.</p>
        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <button
            onClick={() => router.push("/lk/requests/new")}
            className="inline-flex w-full sm:w-auto items-center justify-center gap-2 rounded-[var(--radius-lg)] bg-brand px-10 py-4 text-base font-semibold text-brand-ink shadow-glow-brand hover:bg-brand-hover hover:shadow-[0_0_32px_rgba(240,165,0,0.5)] active:scale-[0.97] transition-all duration-150 animate-pulse"
          >
            Начать бесплатно
            <ChevronRight className="h-5 w-5" />
          </button>
          <a
            href="mailto:info@minitender.ru"
            className="inline-flex w-full sm:w-auto items-center justify-center gap-2 rounded-[var(--radius-lg)] bg-white/5 px-10 py-4 text-base font-semibold text-white ring-1 ring-white/10 hover:bg-white/10 transition-colors duration-150"
          >
            Связаться с нами
          </a>
        </div>
        <p className="mt-6 text-xs text-white/40">По вопросам корпоративного доступа: info@minitender.ru</p>
      </div>
    </section>
  );
}

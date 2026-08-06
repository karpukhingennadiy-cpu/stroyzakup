"use client";

import { useRouter } from "next/navigation";
import { ArrowRight, Mail } from "lucide-react";

export function LandingCTA() {
  const router = useRouter();

  return (
    <section className="relative overflow-hidden py-24 sm:py-32">
      <div
        className="absolute inset-0 opacity-50"
        aria-hidden="true"
        style={{
          background: "radial-gradient(ellipse at center, var(--accent-soft) 0%, transparent 70%)",
        }}
      />

      <div className="relative mx-auto max-w-3xl px-4 text-center sm:px-6">
        <h2 className="text-3xl font-bold tracking-tight text-[var(--label-primary)] sm:text-5xl">
          Готовы <span className="gradient-text">сэкономить</span> на закупках?
        </h2>
        <p className="mt-4 text-lg text-[var(--label-secondary)] leading-relaxed">
          Первые 50 заявок обрабатываются бесплатно. Никаких подписок — только результат.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={() => router.push("/lk/requests/new")}
            className="relative overflow-hidden inline-flex items-center gap-2 rounded-[var(--radius-full)] gradient-bg px-8 py-4 text-base font-semibold text-white shadow-medium hover:shadow-glow active:scale-[0.97] transition-all duration-200 btn-shimmer"
          >
            Начать бесплатно
            <ArrowRight className="h-5 w-5" />
          </button>
          <a
            href="mailto:info@minitender.ru"
            className="inline-flex items-center gap-2 rounded-[var(--radius-full)] border border-[var(--separator)] bg-[var(--bg-tertiary)] px-8 py-4 text-base font-semibold text-[var(--label-primary)] shadow-xs hover:shadow-small hover:border-[var(--accent)]/20 transition-all duration-200"
          >
            <Mail className="h-4 w-4" />
            Связаться с нами
          </a>
        </div>

        <p className="mt-6 text-xs text-[var(--label-quaternary)]">
          Корпоративный доступ: info@minitender.ru
        </p>
      </div>
    </section>
  );
}

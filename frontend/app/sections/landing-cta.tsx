"use client";

import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";

export function LandingCTA() {
  const router = useRouter();

  return (
    <section className="border-t border-[var(--separator)] bg-[var(--bg-secondary)]">
      <div className="mx-auto max-w-6xl px-6 lg:px-8 py-24">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight text-[var(--label-primary)]">
              Готовы сэкономить на закупках?
            </h2>
            <p className="mt-4 text-lg text-[var(--label-secondary)] leading-relaxed">
              Первые 50 заявок обрабатываются бесплатно. Никаких подписок — только результат.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row items-start gap-3">
              <button
                onClick={() => router.push("/lk/requests/new")}
                className="inline-flex items-center gap-2 rounded-[var(--radius-lg)] bg-[var(--accent)] px-6 py-3 text-sm font-medium text-white hover:bg-[var(--accent-hover)]"
              >
                Начать бесплатно
                <ArrowRight className="h-4 w-4" />
              </button>
              <a
                href="mailto:info@minitender.ru"
                className="inline-flex items-center gap-2 rounded-[var(--radius-lg)] border border-[var(--separator)] bg-[var(--bg-tertiary)] px-6 py-3 text-sm font-medium text-[var(--label-primary)] hover:bg-[var(--fill-1)]"
              >
                Связаться с нами
              </a>
            </div>
          </div>
          <img
            src="/images/rfq-email.jpg"
            alt="Автоматическая рассылка запросов КП"
            className="w-full rounded-[var(--radius-xl)] border border-[var(--separator)] shadow-[var(--shadow-medium)] object-cover"
          />
        </div>
      </div>
    </section>
  );
}
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Zap, ArrowRight, Sparkles } from "lucide-react";

export function LandingHero() {
  const router = useRouter();
  const [text, setText] = useState("");

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-24 pb-16">
      <div className="absolute inset-0 mesh-gradient" aria-hidden="true" />
      <div
        className="absolute inset-0 opacity-[0.03]"
        aria-hidden="true"
        style={{
          backgroundImage: `radial-gradient(var(--label-primary) 1px, transparent 1px)`,
          backgroundSize: "32px 32px",
        }}
      />

      <div className="relative mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
        <div className="mb-8 inline-flex items-center gap-2 rounded-[var(--radius-full)] border border-[var(--accent)]/20 bg-[var(--accent-soft)] px-4 py-1.5 text-sm font-medium text-[var(--accent)] animate-reveal">
          <Sparkles className="h-3.5 w-3.5" />
          AI-powered procurement platform
        </div>

        <h1 className="text-balance text-5xl font-extrabold tracking-tight text-[var(--label-primary)] sm:text-7xl leading-[1.05] animate-reveal delay-100">
          Строительные закупки{" "}
          <span className="gradient-text">без посредников</span>
        </h1>

        <p className="mt-6 text-lg sm:text-xl leading-relaxed text-[var(--label-secondary)] max-w-2xl mx-auto animate-reveal delay-200">
          Отправьте список материалов — за 24 часа получите конкурентный лист
          с лучшими ценами от проверенных поставщиков в вашем регионе.
        </p>

        <div className="mt-10 mx-auto max-w-xl animate-reveal delay-300">
          <div className="relative group">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={`Керамогранит серый 600×600 — 150 м²\nБетон М300 — 12 м³\nДоска обрезная сосна 25×150 — 3 м³`}
              className="w-full h-36 resize-none rounded-[var(--radius-lg)] border border-[var(--separator)] bg-[var(--bg-tertiary)] px-5 py-4 text-sm text-[var(--label-primary)] placeholder:text-[var(--label-quaternary)] shadow-small focus:shadow-medium focus:border-[var(--accent)]/30 focus:ring-2 focus:ring-[var(--accent)]/10 outline-none transition-all duration-300"
            />
            <div className="absolute bottom-3 right-4 text-xs text-[var(--label-quaternary)] tabular-nums">
              {text.length} симв.
            </div>
          </div>
        </div>

        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4 animate-reveal delay-400">
          <button
            onClick={() => router.push("/lk/requests/new")}
            className="relative overflow-hidden inline-flex items-center gap-2 rounded-[var(--radius-full)] gradient-bg px-8 py-3.5 text-base font-semibold text-white shadow-medium hover:shadow-glow active:scale-[0.97] transition-all duration-200 btn-shimmer"
          >
            <Zap className="h-5 w-5" />
            Разослать заявку
          </button>
          <button
            onClick={() => document.getElementById("how")?.scrollIntoView({ behavior: "smooth" })}
            className="inline-flex items-center gap-2 rounded-[var(--radius-full)] border border-[var(--separator)] bg-[var(--bg-tertiary)] px-8 py-3.5 text-base font-semibold text-[var(--label-primary)] shadow-xs hover:shadow-small hover:border-[var(--accent)]/20 active:scale-[0.97] transition-all duration-200"
          >
            Как это работает
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        <p className="mt-6 text-xs text-[var(--label-quaternary)] animate-reveal delay-400">
          Первые 50 заявок бесплатно · Не нужна регистрация для демо · Данные обрабатывает AI
        </p>

        <div className="mt-14 relative mx-auto max-w-5xl animate-reveal delay-500">
          <div className="absolute -inset-4 rounded-[var(--radius-2xl)] bg-gradient-to-b from-[var(--accent)]/15 via-transparent to-transparent blur-2xl" aria-hidden="true" />
          <img
            src="/images/hero-construction.jpg"
            alt="Строительные материалы — визуализация платформы"
            className="relative w-full rounded-[var(--radius-2xl)] border border-[var(--separator)] shadow-glow object-cover"
            loading="eager"
          />
          <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-[var(--bg-primary)] to-transparent rounded-b-[var(--radius-2xl)]" aria-hidden="true" />
        </div>
      </div>
    </section>
  );
}

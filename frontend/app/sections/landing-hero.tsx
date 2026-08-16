"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Zap, CheckCircle2 } from "lucide-react";

export function LandingHero() {
  const router = useRouter();
  const [text, setText] = useState("");
  const trustItems = [
    "Без регистрации для демо",
    "50 первых заявок бесплатно",
    "Поставщики отвечают с почты",
  ];
  return (
    <section className="relative overflow-hidden bg-brand-sidebar text-white">
      <div
        className="absolute inset-0 opacity-[0.06]"
        aria-hidden="true"
        style={{
          backgroundImage: `linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)`,
          backgroundSize: "48px 48px",
        }}
      />
      <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
        <div className="mx-auto max-w-3xl text-center animate-fade-in">
          <div className="mb-6 inline-flex items-center rounded-full border border-brand/40 bg-brand-light px-3 py-1 text-sm font-medium text-brand animate-pulse">
            <span className="mr-2 flex h-2 w-2 rounded-full bg-brand" aria-hidden="true" />
            MVP запущен — первые 50 заявок бесплатно
          </div>
          <h1 className="text-balance text-[2rem] font-extrabold tracking-tight leading-tight sm:text-6xl animate-slide-up">
            Строительные закупки <span className="text-brand">без посредников</span>
          </h1>
          <p className="mt-6 text-lg leading-8 text-white/60 animate-slide-up [animation-delay:150ms]">
            Отправьте список материалов — за 24 часа получите конкурентный лист с лучшими ценами от поставщиков в вашем регионе.
          </p>
          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <div className="relative w-full max-w-md">
              <label htmlFor="hero-materials" className="sr-only">Список материалов</label>
              <textarea
                id="hero-materials"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder={`Пример:\nКерамогранит серый 600x600 — 150 м²\nБетон М300 — 12 м³\nДоска обрезная сосна 25×150 — 3 м³`}
                className="h-40 w-full resize-none rounded-[var(--radius-lg)] border-0 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-white/40 ring-1 ring-white/10 focus:ring-2 focus:ring-brand outline-none transition-shadow"
              />
              <div className="absolute bottom-3 right-3">
                <span className="text-xs text-white/40">{text.length} симв.</span>
              </div>
            </div>
          </div>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center animate-slide-up [animation-delay:300ms]">
            <button
              onClick={() => router.push("/lk/requests/new")}
              className="inline-flex items-center justify-center gap-2 rounded-[var(--radius-lg)] bg-brand px-8 py-3.5 text-base font-semibold text-brand-ink shadow-glow-brand hover:bg-brand-hover hover:shadow-[0_0_28px_rgba(240,165,0,0.45)] active:scale-[0.97] transition-all duration-150 w-full sm:w-auto"
            >
              <Zap className="h-5 w-5" />
              Разослать заявку
            </button>
            <button
              onClick={() => document.getElementById("how")?.scrollIntoView({ behavior: "smooth" })}
              className="inline-flex items-center justify-center gap-2 rounded-[var(--radius-lg)] bg-white/5 px-8 py-3.5 text-base font-semibold text-white ring-1 ring-white/10 hover:bg-white/10 active:scale-[0.97] transition-all duration-150 w-full sm:w-auto"
            >
              Посмотреть демо
            </button>
          </div>
          <ul className="mt-8 flex flex-col items-center gap-2 sm:flex-row sm:justify-center sm:gap-6 animate-slide-up [animation-delay:450ms]" aria-label="Преимущества">
            {trustItems.map((item) => (
              <li key={item} className="flex items-center gap-1.5 text-sm text-white/50">
                <CheckCircle2 className="h-4 w-4 text-brand shrink-0" aria-hidden="true" />
                {item}
              </li>
            ))}
          </ul>
          <p className="mt-4 text-xs text-white/40">Данные обрабатываются AI. Не нужна регистрация для просмотра демо.</p>
        </div>
      </div>
    </section>
  );
}

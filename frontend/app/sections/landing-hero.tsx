"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Sparkles } from "lucide-react";

export function LandingHero() {
  const router = useRouter();
  const [text, setText] = useState("");

  return (
    <section className="relative overflow-hidden">
      <div className="mx-auto max-w-6xl px-6 lg:px-8 pt-24 pb-20">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-neutral-200 bg-white px-3 py-1 text-xs font-medium text-neutral-600">
              <Sparkles className="h-3 w-3" />
              Платформа строительных закупок
            </div>

            <h1 className="mt-6 text-4xl sm:text-5xl font-semibold tracking-tight text-neutral-900 leading-[1.1]">
              Строительные закупки без посредников
            </h1>

            <p className="mt-5 text-lg text-neutral-500 leading-relaxed">
              Отправьте список материалов — получите конкурентный лист с ценами
              от проверенных поставщиков в вашем регионе.
            </p>

            <div className="mt-8">
              <textarea
                value={text}
                onChange={e => setText(e.target.value)}
                placeholder={"Керамогранит серый 600x600 — 150 м2\nБетон М300 — 12 м3\nДоска обрезная сосна 25x150 — 3 м3"}
                className="w-full h-32 resize-none rounded-xl border border-neutral-200 bg-white px-4 py-3 text-sm text-neutral-900 placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900/5 focus:border-neutral-300"
              />
            </div>

            <div className="mt-6 flex flex-col sm:flex-row items-center gap-3">
              <button
                onClick={() => router.push("/lk/requests/new")}
                className="inline-flex items-center gap-2 rounded-lg bg-neutral-900 px-6 py-3 text-sm font-medium text-white hover:bg-neutral-700"
              >
                Разослать заявку
                <ArrowRight className="h-4 w-4" />
              </button>
              <button
                onClick={() => document.getElementById("how")?.scrollIntoView({ behavior: "smooth" })}
                className="inline-flex items-center gap-2 rounded-lg border border-neutral-200 bg-white px-6 py-3 text-sm font-medium text-neutral-700 hover:bg-neutral-50"
              >
                Как это работает
              </button>
            </div>

            <p className="mt-6 text-xs text-neutral-400">
              Первые 50 заявок бесплатно · Не нужна регистрация для демо
            </p>
          </div>

          <div className="hidden lg:block">
            <img
              src="/images/hero-construction.jpg"
              alt="Строительные материалы"
              className="w-full rounded-2xl border border-neutral-200 shadow-sm object-cover"
            />
          </div>
        </div>
      </div>
    </section>
  );
}

// frontend/app/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ThemeToggle } from "@/components/theme";

const IconHammer = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="m15 12-9.373 9.373a1 1 0 0 1-3.001-3L12 9" />
    <path d="m18 15 4-4" />
    <path d="m21.5 11.5-1.914-1.914A2 2 0 0 1 19 8.172v-.344a2 2 0 0 0-.586-1.414l-1.657-1.657A6 6 0 0 0 12.516 3H9l1.243 1.243A6 6 0 0 1 12 8.485V10l2.5 2.5" />
  </svg>
);

const IconSearch = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx={11} cy={11} r={8} />
    <path d="m21 21-4.3-4.3" />
  </svg>
);

const IconTruck = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2" />
    <path d="M15 18H9" />
    <path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-2.33-2.91A1 1 0 0 0 18.655 9H15" />
    <circle cx={17} cy={18} r={2} />
    <circle cx={7} cy={18} r={2} />
  </svg>
);

const IconFileCheck = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z" />
    <path d="M14 2v5a1 1 0 0 0 1 1h5" />
    <path d="m9 15 2 2 4-4" />
  </svg>
);

const IconZap = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
);

const IconShield = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
    <path d="m9 12 2 2 4-4" />
  </svg>
);

const IconChevronRight = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="m9 18 6-6-6-6" />
  </svg>
);

function Header() {
  const router = useRouter();
  return (
    <header className="sticky top-0 z-header border-b border-separator bg-[var(--bg-primary)]/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <a href="/" className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-[var(--radius-sm)] bg-brand text-brand-ink">
            <IconHammer className="h-5 w-5" />
          </div>
          <span className="hidden min-[380px]:inline text-xl font-semibold tracking-tight text-label-1">Минитендер</span>
        </a>
        <nav className="hidden items-center gap-8 md:flex" aria-label="Разделы лендинга">
          <a href="#how" className="text-sm font-medium text-label-2 hover:text-label-1 transition-colors">Как работает</a>
          <a href="#features" className="text-sm font-medium text-label-2 hover:text-label-1 transition-colors">Возможности</a>
          <a href="#pricing" className="text-sm font-medium text-label-2 hover:text-label-1 transition-colors">Тарифы</a>
        </nav>
        <div className="flex items-center gap-2">
          <span className="[&_button]:text-[var(--label-secondary)] [&_button:hover]:bg-[var(--fill-1)] [&_button:hover]:text-[var(--label-primary)]">
            <ThemeToggle />
          </span>
          <button onClick={() => router.push("/lk")} className="hidden text-sm font-medium text-label-2 hover:text-label-1 transition-colors sm:block px-2 py-2">
            Войти
          </button>
          <button onClick={() => router.push("/lk/requests/new")} className="rounded-[var(--radius-md)] bg-brand px-3 py-2 text-xs font-semibold text-brand-ink hover:bg-brand-hover active:scale-[0.97] transition-all duration-150 sm:px-4 sm:text-sm">
            Начать бесплатно
          </button>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  const router = useRouter();
  const [text, setText] = useState("");
  return (
    <section className="relative overflow-hidden bg-brand-sidebar text-white">
      <div className="absolute inset-0 opacity-[0.06]" aria-hidden="true" style={{
        backgroundImage: `linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)`,
        backgroundSize: '48px 48px'
      }} />
      <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-6 inline-flex items-center rounded-full border border-brand/30 bg-brand/10 px-3 py-1 text-sm font-medium text-brand">
            <span className="mr-2 flex h-2 w-2 rounded-full bg-brand animate-pulse" aria-hidden="true" />
            MVP запущен — первые 50 заявок бесплатно
          </div>
          <h1 className="text-balance text-4xl font-extrabold tracking-tight sm:text-6xl">
            Строительные закупки <span className="text-brand">без посредников</span>
          </h1>
          <p className="mt-6 text-lg leading-8 text-white/60">
            Отправьте список материалов — за 24 часа получите конкурентный лист с лучшими ценами от поставщиков в вашем регионе.
          </p>
          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <div className="relative w-full max-w-md">
              <label htmlFor="hero-materials" className="sr-only">Список материалов</label>
              <textarea
                id="hero-materials"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder={`Пример:
Керамогранит серый 600x600 — 150 м²
Бетон М300 — 12 м³
Доска обрезная сосна 25×150 — 3 м³`}
                className="h-40 w-full resize-none rounded-[var(--radius-lg)] border-0 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-white/40 ring-1 ring-white/10 focus:ring-2 focus:ring-brand outline-none transition-shadow"
              />
              <div className="absolute bottom-3 right-3">
                <span className="text-xs text-white/40">{text.length} симв.</span>
              </div>
            </div>
          </div>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <button onClick={() => router.push("/lk/requests/new")} className="inline-flex items-center justify-center gap-2 rounded-[var(--radius-lg)] bg-brand px-8 py-3.5 text-base font-semibold text-brand-ink hover:bg-brand-hover active:scale-[0.97] transition-all duration-150">
              <IconZap className="h-5 w-5" />
              Разослать заявку
            </button>
            <button onClick={() => document.getElementById("how")?.scrollIntoView({behavior: "smooth"})} className="inline-flex items-center justify-center gap-2 rounded-[var(--radius-lg)] bg-white/5 px-8 py-3.5 text-base font-semibold text-white ring-1 ring-white/10 hover:bg-white/10 active:scale-[0.97] transition-all duration-150">
              Посмотреть демо
            </button>
          </div>
          <p className="mt-4 text-xs text-white/40">Не нужна регистрация для просмотра демо. Данные обрабатываются AI.</p>
        </div>
      </div>
    </section>
  );
}

const steps = [
  { icon: IconFileCheck, title: "Загрузите смету", desc: "Вставьте список материалов текстом или Excel. AI распознаёт позиции, категории и объёмы." },
  { icon: IconSearch, title: "AI найдёт поставщиков", desc: "Алгоритм сканирует базу производителей и дилеров в радиусе до 300 км от объекта." },
  { icon: IconTruck, title: "Авторассылка RFQ", desc: "Поставщики получают персонализированные запросы КП с вашим списком позиций." },
  { icon: IconShield, title: "Сравните предложения", desc: "Все цены собираются в единую таблицу. Выбирайте по цене, срокам и рейтингу." },
];

function HowItWorks() {
  return (
    <section id="how" className="py-24 bg-surface-primary">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-label-1 sm:text-4xl">Как это работает</h2>
          <p className="mt-4 text-lg text-label-2">Пять шагов от заявки до выбора поставщика — без телефона, без посредников.</p>
        </div>
        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, idx) => (
            <div key={idx} className="group relative rounded-[var(--radius-xl)] border border-separator bg-[var(--fill-1)] p-6 hover:shadow-small transition-shadow duration-150 ease-kimi-out">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-[var(--radius-lg)] bg-brand text-brand-ink">
                <step.icon className="h-6 w-6" />
              </div>
              <h3 className="text-base font-semibold text-label-1">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-label-2">{step.desc}</p>
              <span className="absolute right-4 top-4 text-4xl font-bold text-[var(--label-quaternary)]" aria-hidden="true">0{idx + 1}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

const features = [
  { title: "Универсальный парсинг", desc: "Понимает любые формулировки: от «сотка арматуры» до ГОСТ-описаний. Оценивает полноту данных." },
  { title: "Гибридный поиск", desc: "LLM генерирует первичный список, DaData верифицирует юрлица. Защита от фейковых контактов." },
  { title: "Гео-скоринг", desc: "Реальные координаты поставщиков через 2GIS. Сортировка по расстоянию до объекта." },
  { title: "Inbox-интеграция", desc: "Поставщик отвечает на письмо — КП создаётся автоматически. Не нужен личный кабинет у поставщика." },
  { title: "Публичная страница КП", desc: "Отправьте ссылку /quote/TOKEN заказчику. Он увидит сравнение цен без регистрации." },
  { title: "Производители в приоритете", desc: "AI-классификация «производитель / дилер». Производители получают бонус +10 к релевантности." },
];

function Features() {
  return (
    <section id="features" className="py-24 bg-surface-ground">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-label-1 sm:text-4xl">Возможности платформы</h2>
          <p className="mt-4 text-lg text-label-2">Всё, что нужно для профессиональных закупок в строительстве.</p>
        </div>
        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f, idx) => (
            <div key={idx} className="rounded-[var(--radius-xl)] bg-surface-primary p-6 ring-1 ring-[var(--separator)] hover:shadow-small transition-shadow duration-150 ease-kimi-out">
              <h3 className="text-base font-semibold text-label-1">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-label-2">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Stats() {
  const stats = [
    { value: "28", label: "категорий материалов" },
    { value: "300", label: "км радиус поиска" },
    { value: "24", label: "часа на сбор КП" },
    { value: "0", label: "руб. за первые 50 заявок" },
  ];
  return (
    <section id="pricing" className="border-y border-separator bg-surface-primary py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {stats.map((s, i) => (
            <div key={i} className="text-center">
              <div className="text-3xl font-extrabold text-brand sm:text-4xl tabular-nums">{s.value}</div>
              <div className="mt-1 text-sm font-medium text-label-2">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CTA() {
  const router = useRouter();
  return (
    <section className="bg-brand-sidebar py-24">
      <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
        <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">Готовы сэкономить на закупках?</h2>
        <p className="mt-4 text-lg text-white/60">Первые 50 заявок обрабатываются бесплатно. Никаких подписок — только результат.</p>
        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <button onClick={() => router.push("/lk/requests/new")} className="inline-flex items-center gap-2 rounded-[var(--radius-lg)] bg-brand px-8 py-4 text-base font-semibold text-brand-ink hover:bg-brand-hover active:scale-[0.97] transition-all duration-150">
            Начать бесплатно
            <IconChevronRight className="h-5 w-5" />
          </button>
          <a href="mailto:info@minitender.ru" className="inline-flex items-center gap-2 rounded-[var(--radius-lg)] bg-white/5 px-8 py-4 text-base font-semibold text-white ring-1 ring-white/10 hover:bg-white/10 transition-colors duration-150">
            Связаться с нами
          </a>
        </div>
        <p className="mt-6 text-xs text-white/40">По вопросам корпоративного доступа: info@minitender.ru</p>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-separator bg-surface-primary py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-sm)] bg-brand text-brand-ink">
              <IconHammer className="h-4 w-4" />
            </div>
            <span className="text-lg font-semibold text-label-1">Минитендер</span>
          </div>
          <p className="text-sm text-label-3">© {new Date().getFullYear()} Минитендер.рф — платформа строительных закупок</p>
          <div className="flex gap-6">
            <a href="#" className="text-sm text-label-3 hover:text-label-1 transition-colors">Политика</a>
            <a href="#" className="text-sm text-label-3 hover:text-label-1 transition-colors">API</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col">
      <Header />
      <Hero />
      <Stats />
      <HowItWorks />
      <Features />
      <CTA />
      <Footer />
    </main>
  );
}

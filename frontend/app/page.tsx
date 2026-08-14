import { Hammer } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { LandingHeader } from "./sections/landing-header";
import { LandingHero } from "./sections/landing-hero";
import { LandingCTA } from "./sections/landing-cta";

const steps = [
  { icon: "FileCheck", title: "Загрузите смету", desc: "Вставьте список материалов текстом или Excel. AI распознаёт позиции, категории и объёмы." },
  { icon: "Search", title: "AI найдёт поставщиков", desc: "Алгоритм сканирует базу производителей и дилеров в радиусе до 300 км от объекта." },
  { icon: "Truck", title: "Авторассылка RFQ", desc: "Поставщики получают персонализированные запросы КП с вашим списком позиций." },
  { icon: "Shield", title: "Сравните предложения", desc: "Все цены собираются в единую таблицу. Выбирайте по цене, срокам и рейтингу." },
];

const stepIcons: Record<string, React.ReactNode> = {
  FileCheck: (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="m9 15 2 2 4-4"/></svg>
  ),
  Search: (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
  ),
  Truck: (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6"><path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-2.48-3.1a1 1 0 0 0-.78-.376H15"/><circle cx="7" cy="18" r="2"/><path d="M15 18H9"/></svg>
  ),
  Shield: (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/></svg>
  ),
};

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
            <Card key={idx} className="group relative hover:shadow-small transition-shadow duration-150 ease-kimi-out overflow-hidden">
              <CardHeader>
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-[var(--radius-lg)] bg-brand text-brand-ink">
                  {stepIcons[step.icon]}
                </div>
                <CardTitle>{step.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-sm leading-relaxed">{step.desc}</CardDescription>
              </CardContent>
              <span className="absolute right-4 top-4 text-4xl font-bold text-[var(--label-quaternary)]" aria-hidden="true">0{idx + 1}</span>
            </Card>
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
        <div className="mt-16 grid gap-8 lg:grid-cols-2 items-center">
          <div className="relative">
            <div className="absolute -inset-3 rounded-[var(--radius-2xl)] bg-gradient-to-tr from-[var(--accent)]/10 via-transparent to-transparent blur-xl" aria-hidden="true" />
            <img
              src="/images/dashboard-preview.jpg"
              alt="Панель управления закупками"
              className="relative w-full rounded-[var(--radius-2xl)] border border-separator shadow-medium object-cover"
              loading="lazy"
            />
          </div>
          <div className="grid gap-6 sm:grid-cols-2">
            {features.map((f, idx) => (
              <Card key={idx} className="hover:shadow-small transition-shadow duration-150 ease-kimi-out">
                <CardContent className="pt-6">
                  <h3 className="text-base font-semibold text-label-1">{f.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-label-2">{f.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
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

function Footer() {
  return (
    <footer className="border-t border-separator bg-surface-primary py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-sm)] bg-brand text-brand-ink">
              <Hammer className="h-4 w-4" />
            </div>
            <span className="text-lg font-semibold text-label-1">Минитендер</span>
          </div>
          <p className="text-sm text-label-3">© 2025 Минитендер.рф — платформа строительных закупок</p>
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
      <LandingHeader />
      <LandingHero />
      <Stats />
      <HowItWorks />
      <Features />
      <LandingCTA />
      <Footer />
    </main>
  );
}

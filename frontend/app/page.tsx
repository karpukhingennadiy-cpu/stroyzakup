import { Hammer, ArrowRight, FileText, Search, MapPin, Mail, Link2, Factory, Star } from "lucide-react";
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
            <div key={idx} className="relative">
              <Card className="group relative h-full hover:shadow-small transition-shadow duration-150 ease-kimi-out">
                <CardHeader>
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-[var(--radius-lg)] bg-brand text-brand-ink">
                    {stepIcons[step.icon]}
                  </div>
                  <CardTitle>{step.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-sm leading-relaxed">{step.desc}</CardDescription>
                </CardContent>
                <span className="absolute right-4 top-4 font-mono text-4xl font-bold text-[var(--label-quaternary)]" aria-hidden="true">0{idx + 1}</span>
              </Card>
              {idx < steps.length - 1 && (
                <div className="hidden lg:flex absolute top-1/2 -right-[26px] -translate-y-1/2 z-10 text-[var(--label-quaternary)]" aria-hidden="true">
                  <ArrowRight className="h-6 w-6" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

const features = [
  { icon: FileText, title: "Универсальный парсинг", desc: "Понимает любые формулировки: от «сотка арматуры» до ГОСТ-описаний. Оценивает полноту данных." },
  { icon: Search, title: "Гибридный поиск", desc: "LLM генерирует первичный список, DaData верифицирует юрлица. Защита от фейковых контактов." },
  { icon: MapPin, title: "Гео-скоринг", desc: "Реальные координаты поставщиков через 2GIS. Сортировка по расстоянию до объекта." },
  { icon: Mail, title: "Inbox-интеграция", desc: "Поставщик отвечает на письмо — КП создаётся автоматически. Не нужен личный кабинет у поставщика." },
  { icon: Link2, title: "Публичная страница КП", desc: "Отправьте ссылку /quote/TOKEN заказчику. Он увидит сравнение цен без регистрации." },
  { icon: Factory, title: "Производители в приоритете", desc: "AI-классификация «производитель / дилер». Производители получают бонус +10 к релевантности." },
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
            <Card key={idx} className="hover:shadow-small transition-shadow duration-150 ease-kimi-out">
              <CardContent className="pt-6">
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)] bg-accent-light text-accent">
                  <f.icon className="h-5 w-5" aria-hidden="true" />
                </div>
                <h3 className="text-base font-semibold text-label-1">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-label-2">{f.desc}</p>
              </CardContent>
            </Card>
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
              <div className="text-[3.5rem] font-bold leading-none text-brand tabular-nums">{s.value}</div>
              <div className="mt-2 text-sm font-medium text-label-2">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

const testimonials = [
  {
    quote: "Раньше обзванивал 15 поставщиков, чтобы собрать цены. Теперь конкурентный лист приходит за сутки — и экономия сразу видна.",
    name: "Сергей Ковалёв",
    role: "Прораб, СК «Монолит»",
  },
  {
    quote: "Поставщики сами пишут предложения, конкуренция работает. Первая же закупка окупила всё.",
    name: "Дмитрий Абрамов",
    role: "Снабженец, «АльфаСтрой»",
  },
  {
    quote: "Разобрали смету на 120 позиций без единой ошибки — включая «сотку арматуры» и ГОСТ-описания.",
    name: "Ирина Соколова",
    role: "Сметчик, «СтройКомплект»",
  },
];

function Testimonials() {
  return (
    <section id="reviews" className="py-24 bg-surface-primary">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-label-1 sm:text-4xl">Уже используют</h2>
          <p className="mt-4 text-lg text-label-2">Строители, снабженцы и сметчики экономят на каждой закупке.</p>
        </div>
        <div className="mt-16 grid gap-6 md:grid-cols-3">
          {testimonials.map((t, idx) => (
            <Card key={idx} className="flex flex-col hover:shadow-small transition-shadow duration-150 ease-kimi-out">
              <CardContent className="pt-6 flex flex-col flex-1">
                <div className="flex gap-1 mb-4" aria-label="Оценка 5 из 5">
                  {[0, 1, 2, 3, 4].map((s) => (
                    <Star key={s} className="h-4 w-4 fill-brand text-brand" aria-hidden="true" />
                  ))}
                </div>
                <blockquote className="text-sm leading-relaxed text-label-1 flex-1">«{t.quote}»</blockquote>
                <div className="mt-6 pt-4 border-t border-separator">
                  <p className="text-sm font-semibold text-label-1">{t.name}</p>
                  <p className="text-xs text-label-3 mt-0.5">{t.role}</p>
                </div>
              </CardContent>
            </Card>
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
        <div className="flex flex-col items-center justify-between gap-8 sm:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-sm)] bg-brand text-brand-ink">
              <Hammer className="h-4 w-4" />
            </div>
            <span className="text-lg font-semibold text-label-1">Минитендер</span>
          </div>
          <nav className="flex flex-wrap justify-center gap-x-6 gap-y-2" aria-label="Навигация в подвале">
            <a href="#how" className="text-sm text-label-3 hover:text-label-1 transition-colors">Как работает</a>
            <a href="#features" className="text-sm text-label-3 hover:text-label-1 transition-colors">Возможности</a>
            <a href="#pricing" className="text-sm text-label-3 hover:text-label-1 transition-colors">Тарифы</a>
            <a href="#" className="text-sm text-label-3 hover:text-label-1 transition-colors">API</a>
            <a href="#" className="text-sm text-label-3 hover:text-label-1 transition-colors">Политика</a>
          </nav>
        </div>
        <div className="mt-8 flex flex-col items-center justify-between gap-3 border-t border-separator pt-6 sm:flex-row">
          <p className="text-sm text-label-3">© 2025 Минитендер.рф — платформа строительных закупок</p>
          <a href="mailto:support@minitender.ru" className="text-sm text-label-3 hover:text-label-1 transition-colors">
            support@minitender.ru
          </a>
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
      <Testimonials />
      <LandingCTA />
      <Footer />
    </main>
  );
}

import { IconHardHat, IconList, IconSearch, IconTruck, IconChart, IconMapPin, IconShield } from "@/components/icons";
import { LandingHeader } from "./sections/landing-header";
import { LandingHero } from "./sections/landing-hero";
import { LandingCTA } from "./sections/landing-cta";

const steps = [
  { icon: IconList, title: "Загрузите смету", desc: "Вставьте список материалов текстом или Excel. AI распознаёт позиции, категории и объёмы." },
  { icon: IconSearch, title: "AI найдёт поставщиков", desc: "Алгоритм сканирует базу производителей и дилеров в радиусе до 300 км от объекта." },
  { icon: IconTruck, title: "Авторассылка RFQ", desc: "Поставщики получают персонализированные запросы КП с вашим списком позиций." },
  { icon: IconChart, title: "Сравните предложения", desc: "Все цены собираются в единую таблицу. Выбирайте по цене, срокам и рейтингу." },
];

function HowItWorks() {
  return (
    <section id="how" className="border-b border-[var(--separator)]">
      <div className="mx-auto max-w-6xl px-6 lg:px-8 py-24">
        <div className="max-w-2xl">
          <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight text-[var(--label-primary)]">Как это работает</h2>
          <p className="mt-4 text-lg text-[var(--label-secondary)]">Пять шагов от заявки до выбора поставщика — без телефона, без посредников.</p>
        </div>
        <div className="mt-14 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, idx) => (
            <div key={idx} className="rounded-[var(--radius-lg)] border border-[var(--separator)] bg-[var(--bg-tertiary)] p-5 shadow-[var(--shadow-xs)]">
              <div className="flex items-center gap-2">
                <div className="inline-flex items-center justify-center size-8 rounded-[var(--radius-md)] bg-[var(--accent-soft)] text-[var(--accent)]">
                  <step.icon className="w-4 h-4" />
                </div>
                <div className="inline-flex items-center justify-center size-7 rounded-full bg-[var(--accent-soft)] text-xs font-semibold text-[var(--accent)] tabular-nums">
                  {idx + 1}
                </div>
              </div>
              <h3 className="mt-3 text-base font-semibold tracking-tight text-[var(--label-primary)]">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-[var(--label-secondary)]">{step.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

const features = [
  { icon: IconList, title: "Универсальный парсинг", desc: "Плитка, ламинат, краска, штукатурка, гипсокартон, обои — любые формулировки сметы на отделку." },
  { icon: IconSearch, title: "Гибридный поиск", desc: "Производители плитки, красок и материалов для благоустройства. DaData верифицирует юрлица." },
  { icon: IconMapPin, title: "Гео-скоринг", desc: "Поиск поставщиков отделки и благоустройства в радиусе до 300 км от вашего объекта." },
  { icon: IconShield, title: "Inbox-интеграция", desc: "КП от поставщиков плитки, красок и покрытий собираются автоматически из ответов на письма." },
  { icon: IconChart, title: "Публичная страница КП", desc: "Сравнение цен на отделочные материалы и благоустройство в одной таблице — без регистрации." },
  { icon: IconHardHat, title: "Производители в приоритете", desc: "Производители отделочных материалов и благоустройства получают приоритет в выдаче." },
];

function Features() {
  return (
    <section id="features">
      <div className="mx-auto max-w-6xl px-6 lg:px-8 py-24">
        <div className="max-w-2xl">
          <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight text-[var(--label-primary)]">Возможности платформы</h2>
          <p className="mt-4 text-lg text-[var(--label-secondary)]">Всё, что нужно для профессиональных закупок в строительстве.</p>
        </div>
        <div className="mt-14 grid gap-8 lg:grid-cols-2 items-center">
          <img
            src="/images/dashboard-preview.jpg"
            alt="Панель управления закупками"
            className="w-full rounded-[var(--radius-xl)] border border-[var(--separator)] shadow-[var(--shadow-medium)] object-cover"
          />
          <div className="grid gap-x-10 gap-y-8 sm:grid-cols-2">
            {features.map((f, idx) => (
              <div key={idx}>
                <div className="inline-flex items-center justify-center size-10 rounded-[var(--radius-lg)] bg-[var(--accent-soft)] text-[var(--accent)]">
                  <f.icon className="w-5 h-5" />
                </div>
                <h3 className="mt-3 text-base font-semibold tracking-tight text-[var(--label-primary)]">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[var(--label-secondary)]">{f.desc}</p>
              </div>
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
    <section id="pricing" className="border-y border-[var(--separator)] bg-[var(--bg-secondary)]">
      <div className="mx-auto max-w-6xl px-6 lg:px-8 py-16">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {stats.map((s, i) => (
            <div key={i}>
              <div className="text-3xl sm:text-4xl font-semibold tracking-tight text-[var(--label-primary)] tabular-nums">{s.value}</div>
              <div className="mt-1 text-sm text-[var(--label-secondary)]">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-[var(--separator)] bg-[var(--bg-tertiary)] py-12">
      <div className="mx-auto max-w-6xl px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent)] text-white">
              <IconHardHat className="h-4 w-4" />
            </div>
            <span className="text-base font-semibold tracking-tight text-[var(--label-primary)]">Минитендер</span>
          </div>
          <p className="text-sm text-[var(--label-tertiary)]">© 2025 Минитендер.рф — платформа строительных закупок</p>
          <div className="flex gap-6">
            <a href="#" className="text-sm text-[var(--label-secondary)] hover:text-[var(--label-primary)]">Политика</a>
            <a href="#" className="text-sm text-[var(--label-secondary)] hover:text-[var(--label-primary)]">API</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col bg-[var(--bg-primary)]">
      <LandingHeader />
      <LandingHero />
      <HowItWorks />
      <Features />
      <Stats />
      <LandingCTA />
      <Footer />
    </main>
  );
}
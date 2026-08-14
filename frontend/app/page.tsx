import { Hammer } from "lucide-react";
import { LandingHeader } from "./sections/landing-header";
import { LandingHero } from "./sections/landing-hero";
import { LandingCTA } from "./sections/landing-cta";

const steps = [
  { title: "Загрузите смету", desc: "Вставьте список материалов текстом или Excel. AI распознаёт позиции, категории и объёмы." },
  { title: "AI найдёт поставщиков", desc: "Алгоритм сканирует базу производителей и дилеров в радиусе до 300 км от объекта." },
  { title: "Авторассылка RFQ", desc: "Поставщики получают персонализированные запросы КП с вашим списком позиций." },
  { title: "Сравните предложения", desc: "Все цены собираются в единую таблицу. Выбирайте по цене, срокам и рейтингу." },
];

function HowItWorks() {
  return (
    <section id="how" className="border-b border-neutral-200">
      <div className="mx-auto max-w-6xl px-6 lg:px-8 py-24">
        <div className="max-w-2xl">
          <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight text-neutral-900">Как это работает</h2>
          <p className="mt-4 text-lg text-neutral-500">Пять шагов от заявки до выбора поставщика — без телефона, без посредников.</p>
        </div>
        <div className="mt-14 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, idx) => (
            <div key={idx}>
              <div className="text-sm font-medium text-neutral-400 tabular-nums">0{idx + 1}</div>
              <h3 className="mt-3 text-base font-semibold text-neutral-900">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-neutral-500">{step.desc}</p>
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
    <section id="features">
      <div className="mx-auto max-w-6xl px-6 lg:px-8 py-24">
        <div className="max-w-2xl">
          <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight text-neutral-900">Возможности платформы</h2>
          <p className="mt-4 text-lg text-neutral-500">Всё, что нужно для профессиональных закупок в строительстве.</p>
        </div>
        <div className="mt-14 grid gap-8 lg:grid-cols-2 items-center">
          <img
            src="/images/dashboard-preview.jpg"
            alt="Панель управления закупками"
            className="w-full rounded-2xl border border-neutral-200 shadow-sm object-cover"
          />
          <div className="grid gap-x-10 gap-y-8 sm:grid-cols-2">
            {features.map((f, idx) => (
              <div key={idx}>
                <h3 className="text-base font-semibold text-neutral-900">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-neutral-500">{f.desc}</p>
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
    <section id="pricing" className="border-y border-neutral-200 bg-neutral-50">
      <div className="mx-auto max-w-6xl px-6 lg:px-8 py-16">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {stats.map((s, i) => (
            <div key={i}>
              <div className="text-3xl sm:text-4xl font-semibold text-neutral-900 tabular-nums">{s.value}</div>
              <div className="mt-1 text-sm text-neutral-500">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-neutral-200 bg-white py-12">
      <div className="mx-auto max-w-6xl px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-neutral-900 text-white">
              <Hammer className="h-4 w-4" />
            </div>
            <span className="text-base font-semibold text-neutral-900">Минитендер</span>
          </div>
          <p className="text-sm text-neutral-400">© 2025 Минитендер.рф — платформа строительных закупок</p>
          <div className="flex gap-6">
            <a href="#" className="text-sm text-neutral-500 hover:text-neutral-900">Политика</a>
            <a href="#" className="text-sm text-neutral-500 hover:text-neutral-900">API</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col bg-white">
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

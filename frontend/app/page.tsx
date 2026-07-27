import Link from "next/link";
import { IconHardHat, IconSearch, IconChart, IconShield, IconSparkles, IconTruck } from "@/components/icons";

const features = [
  { icon: IconSparkles, title: "Умное распознавание", desc: "ИИ-парсер извлечёт позиции, количество и бренды из любого текста сметы за секунды." },
  { icon: IconSearch, title: "Поиск поставщиков", desc: "Найдём производителей и дилеров в радиусе вашего объекта — от 50 до 300 км." },
  { icon: IconChart, title: "Конкурентный лист", desc: "Автоматическое сравнение цен, доставки, сроков. Подсветка лучшего предложения." },
  { icon: IconTruck, title: "Прямые поставки", desc: "Работаем с официальными дилерами и производителями. Никаких посредников." },
  { icon: IconShield, title: "Прозрачность", desc: "Все КП сохраняются. Протокол выбора поставщика формируется автоматически." },
  { icon: IconHardHat, title: "Строительный фокус", desc: "Керамогранит, бетон, кирпич, металл, кровля — 15+ категорий материалов." },
];

export default function Home() {
  return (
    <main>
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-[#1e3a5f] via-[#1a1a2e] to-[#16213e] text-white">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-10 w-72 h-72 bg-[#f0a500] rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-10 w-96 h-96 bg-[#2d5a8e] rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-6xl mx-auto px-6 py-24 text-center">
          <div className="inline-flex items-center gap-2 mb-6 px-4 py-2 bg-white/10 rounded-full text-sm">
            <IconSparkles className="w-4 h-4 text-[#f0a500]" />
            <span>MVP запущен — первые 50 заявок бесплатно</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight mb-6 leading-tight">
            Минитендер
          </h1>
          <p className="text-xl text-white/70 max-w-2xl mx-auto mb-10 leading-relaxed">
            Отправьте список материалов — за 24 часа получите конкурентный лист с лучшими ценами от поставщиков в вашем регионе.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link href="/register" className="px-8 py-4 bg-[#f0a500] text-[#1a1a2e] rounded-xl font-bold text-lg hover:bg-[#fcc419] hover:scale-105 transition shadow-lg shadow-[#f0a500]/30">
              Попробовать бесплатно
            </Link>
            <Link href="/login" className="px-8 py-4 bg-white/10 text-white rounded-xl font-semibold text-lg hover:bg-white/20 border border-white/20 transition">
              Войти
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold text-center text-[#1a1a2e] mb-4">Как это работает</h2>
        <p className="text-center text-[#64748b] mb-12 max-w-xl mx-auto">Пять шагов от заявки до выбора поставщика — без телефона, без посредников.</p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f) => (
            <div key={f.title} className="group bg-white p-8 rounded-2xl border border-[#e2e8f0] hover:shadow-lg hover:border-[#1e3a5f]/20 transition">
              <div className="w-12 h-12 rounded-xl bg-[#1e3a5f]/5 flex items-center justify-center mb-4 group-hover:bg-[#1e3a5f]/10 transition">
                <f.icon className="w-6 h-6 text-[#1e3a5f]" />
              </div>
              <h3 className="font-bold text-lg text-[#1a1a2e] mb-2">{f.title}</h3>
              <p className="text-[#64748b] leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-[#1e3a5f] text-white py-16">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold mb-4">Готовы сэкономить на закупках?</h2>
          <p className="text-white/70 mb-8 text-lg">Первые 50 заявок обрабатываются бесплатно. Никаких подписок — только результат.</p>
          <Link href="/register" className="inline-block px-10 py-4 bg-[#f0a500] text-[#1a1a2e] rounded-xl font-bold text-lg hover:bg-[#fcc419] transition shadow-lg">
            Начать бесплатно
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#1a1a2e] text-white/40 py-8 text-center text-sm">
        © 2026 Минитендер. Сервис организации закупок стройматериалов.
      </footer>
    </main>
  );
}

import type { Metadata } from "next";
import { Inter, Geist } from "next/font/google";
import { ThemeScript } from "@/components/theme";
import { WebVitals } from "@/components/web-vitals";
import "./globals.css";
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Минитендер.рф — поиск лучших цен на стройматериалы",
  description: "Сервис организации закупок стройматериалов. Автоматический разбор сметы, поиск поставщиков, сравнение КП.",
  icons: { icon: "/favicon.svg" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={cn("font-sans", geist.variable)} suppressHydrationWarning>
      <head>
        <ThemeScript />
      </head>
      <body className="font-sans">
        {children}
        <WebVitals />
      </body>
    </html>
  );
}

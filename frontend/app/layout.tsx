import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "cyrillic"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Минитендер — поиск лучших цен на стройматериалы",
  description: "Сервис организации закупок стройматериалов. Автоматический разбор сметы, поиск поставщиков, сравнение КП.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={inter.variable}>
      <body className="min-h-screen bg-[#f5f7fa] antialiased">{children}</body>
    </html>
  );
}

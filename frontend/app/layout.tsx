import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin", "cyrillic"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "StroyZakup — poisk luchshikh tsen na stroymaterialy",
  description: "Servis organizatsii zakupok stroymaterialov. Avtomaticheskiy razbor smety, poisk postavshchikov, sravnenie KП.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ru"
      className={}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}

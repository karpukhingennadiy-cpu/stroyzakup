"use client";

import { useState, useEffect } from "react";
import { optIn, optOut } from "@/lib/analytics";

const CONSENT_KEY = "minitender_analytics_consent";

type ConsentValue = "granted" | "denied" | null;

export function ConsentBanner() {
  const [consent, setConsent] = useState<ConsentValue>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem(CONSENT_KEY) as ConsentValue;
    if (stored) {
      setConsent(stored);
      if (stored === "granted") {
        optIn();
      } else {
        optOut();
      }
    }
  }, []);

  const handleConsent = (value: ConsentValue) => {
    setConsent(value);
    localStorage.setItem(CONSENT_KEY, value ?? "denied");
    if (value === "granted") {
      optIn();
    } else {
      optOut();
    }
  };

  if (!mounted || consent !== null) return null;

  return (
    <div
      role="dialog"
      aria-label="Согласие на использование cookies"
      className="fixed bottom-4 left-4 right-4 z-[1000] mx-auto max-w-2xl rounded-[var(--radius-xl)] border border-[var(--separator)] bg-[var(--bg-tertiary)] p-4 shadow-[var(--shadow-medium)] sm:bottom-6 sm:left-6 sm:right-6"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-[var(--label-secondary)]">
          Мы используем cookies для аналитики и улучшения работы сервиса.
          Продолжая использовать сайт, вы соглашаетесь с{" "}
          <a href="/privacy" className="underline text-[var(--accent)] hover:text-[var(--accent-hover)]">
            политикой конфиденциальности
          </a>.
        </p>
        <div className="flex shrink-0 gap-2">
          <button
            onClick={() => handleConsent("denied")}
            className="rounded-[var(--radius-md)] px-4 py-2 text-sm font-medium text-[var(--label-secondary)] ring-1 ring-[var(--separator)] hover:bg-[var(--fill-1)] transition-colors"
          >
            Отклонить
          </button>
          <button
            onClick={() => handleConsent("granted")}
            className="rounded-[var(--radius-md)] bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--accent-hover)] transition-colors"
          >
            Принять
          </button>
        </div>
      </div>
    </div>
  );
}
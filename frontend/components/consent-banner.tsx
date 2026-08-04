"use client";

import { useState, useEffect } from "react";

const CONSENT_KEY = "minitender_analytics_consent";

type ConsentValue = "granted" | "denied" | null;

export function ConsentBanner() {
  const [consent, setConsent] = useState<ConsentValue>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem(CONSENT_KEY) as ConsentValue;
    if (stored) setConsent(stored);
  }, []);

  const handleConsent = (value: ConsentValue) => {
    setConsent(value);
    localStorage.setItem(CONSENT_KEY, value ?? "denied");
    // Сообщить PostHog о решении пользователя
    if (typeof window !== "undefined" && (window as any).posthog) {
      (window as any).posthog.set_config({ persistence: value === "granted" ? "localStorage+cookie" : "memory" });
    }
  };

  if (!mounted || consent !== null) return null;

  return (
    <div
      role="dialog"
      aria-label="Согласие на использование cookies"
      className="fixed bottom-4 left-4 right-4 z-[1000] mx-auto max-w-2xl rounded-[var(--radius-xl)] border border-separator bg-surface-primary p-4 shadow-small sm:bottom-6 sm:left-6 sm:right-6"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-label-2">
          Мы используем cookies для аналитики и улучшения работы сервиса.
          Продолжая использовать сайт, вы соглашаетесь с{" "}
          <a href="/privacy" className="underline text-accent hover:text-accent-hover">
            политикой конфиденциальности
          </a>.
        </p>
        <div className="flex shrink-0 gap-2">
          <button
            onClick={() => handleConsent("denied")}
            className="rounded-[var(--radius-md)] px-4 py-2 text-sm font-medium text-label-2 ring-1 ring-separator hover:bg-fill-1 transition-colors"
          >
            Отклонить
          </button>
          <button
            onClick={() => handleConsent("granted")}
            className="rounded-[var(--radius-md)] bg-brand px-4 py-2 text-sm font-semibold text-brand-ink hover:bg-brand-hover transition-colors"
          >
            Принять
          </button>
        </div>
      </div>
    </div>
  );
}

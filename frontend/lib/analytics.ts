// frontend/lib/analytics.ts
import posthog from "posthog-js";

const POSTHOG_KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY || "";
const POSTHOG_HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://app.posthog.com";

export function initPostHog() {
  if (typeof window === "undefined") return;
  if (!POSTHOG_KEY) {
    if (process.env.NODE_ENV === "development") {
      console.warn("[PostHog] NEXT_PUBLIC_POSTHOG_KEY not set");
    }
    return;
  }
  posthog.init(POSTHOG_KEY, {
    api_host: POSTHOG_HOST,
    capture_pageview: true,
    capture_pageleave: true,
    persistence: "localStorage",
    loaded: (ph) => {
      if (process.env.NODE_ENV === "development") ph.debug();
    },
  });
}

export function captureEvent(event: string, properties?: Record<string, any>) {
  if (typeof window === "undefined") return;
  if (!posthog.__loaded) return;
  posthog.capture(event, properties);
}

export function optIn() {
  if (typeof window === "undefined") return;
  posthog.opt_in_capturing();
  posthog.set_config({ persistence: "localStorage+cookie" });
}

export function optOut() {
  if (typeof window === "undefined") return;
  posthog.opt_out_capturing();
  posthog.set_config({ persistence: "memory" });
}

export { posthog };

"use client";

import { useEffect } from "react";
import { onCLS, onFCP, onFID, onLCP, onTTFB, type Metric } from "web-vitals";

function sendToAnalytics(metric: Metric) {
  // В production отправлять на analytics endpoint
  // Пока логируем в консоль для разработки
  if (process.env.NODE_ENV === "development") {
    console.log("[WebVital]", metric.name, metric.value, metric.rating);
  }
  // TODO: отправить на /api/analytics/vitals
}

export function WebVitals() {
  useEffect(() => {
    onCLS(sendToAnalytics);
    onFCP(sendToAnalytics);
    onFID(sendToAnalytics);
    onLCP(sendToAnalytics);
    onTTFB(sendToAnalytics);
  }, []);

  return null;
}

"use client";

import type { ApiError } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

export function clearTokens(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = localStorage.getItem("refresh_token");
  if (!refresh) return null;
  try {
    const res = await fetch(API_BASE + "/auth/token/refresh/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) throw new Error("Refresh failed");
    const data = await res.json();
    localStorage.setItem("access_token", data.access);
    return data.access;
  } catch (e: any) {
    clearTokens();
    return null;
  }
}

export async function api(path: string, options?: Record<string, any>): Promise<any> {
  if (!options) options = {};
  const token = getToken();
  const headers: Record<string, string> = Object.assign(
    { "Content-Type": "application/json" },
    options.headers || {}
  );
  if (token) headers["Authorization"] = "Bearer " + token;
  let res = await fetch(API_BASE + path, Object.assign({}, options, { headers }));
  if (res.status === 401 && token) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers["Authorization"] = "Bearer " + newToken;
      res = await fetch(API_BASE + path, Object.assign({}, options, { headers }));
    }
  }
  // Session expired and refresh failed -> back to login instead of a dead error
  if (res.status === 401) {
    clearTokens();
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    throw new Error("Сессия истекла. Войдите снова.");
  }
  if (!res.ok) {
    let errorData: ApiError = {};
    try { errorData = await res.json(); } catch { errorData = { detail: res.statusText }; }
    if (typeof errorData === "object") {
      const messages: string[] = [];
      for (const key in errorData) {
        const val = (errorData as any)[key];
        if (Array.isArray(val)) messages.push(key + ": " + val.join(", "));
        else if (typeof val === "string") messages.push(val);
      }
      throw new Error(messages.join("; ") || "HTTP " + res.status);
    }
    throw new Error(String(errorData) || "HTTP " + res.status);
  }
  return res.json();
}

export async function login(email: string, password: string): Promise<any> {
  const data = await api("/auth/login/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setTokens(data.access, data.refresh);
  return data;
}

export async function registerUser(data: any): Promise<any> {
  return api("/auth/register/", { method: "POST", body: JSON.stringify(data) });
}

export async function getMe(): Promise<any> { return api("/auth/me/"); }
export async function getRequests(): Promise<any> { return api("/requests/"); }
export async function getRequest(id: number): Promise<any> { return api("/requests/" + id + "/"); }

export async function createRequest(
  raw_text: string, comment?: string,
  deliveryAddress?: string, geoResult?: { latitude: number; longitude: number; city: string }
): Promise<any> {
  const body: any = { raw_text, comment };
  if (deliveryAddress) body.delivery_address = deliveryAddress;
  if (geoResult) { body.latitude = geoResult.latitude; body.longitude = geoResult.longitude; body.city = geoResult.city; }
  return api("/requests/", { method: "POST", body: JSON.stringify(body) });
}

export async function parseRequest(id: number): Promise<any> {
  return api("/requests/" + id + "/parse/", { method: "POST" });
}

export async function getSuppliers(params?: any): Promise<any> {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return api("/suppliers/" + qs);
}

export async function searchSuppliersRadius(lat: number, lon: number, radius?: number): Promise<any> {
  if (!radius) radius = 150;
  return api("/suppliers/search_radius/?lat=" + lat + "&lon=" + lon + "&radius=" + radius);
}

export async function getQuotes(requestId?: number): Promise<any> {
  return api("/quotes/" + (requestId ? "?request_id=" + requestId : ""));
}

export async function geocodeAddress(address: string): Promise<any> {
  return api("/auth/geocode/", { method: "POST", body: JSON.stringify({ address }) });
}

export async function matchSuppliers(requestId: number, limit?: number): Promise<any> {
  if (!limit) limit = 20;
  return api("/requests/" + requestId + "/match_suppliers/", {
    method: "POST", body: JSON.stringify({ limit }),
  });
}

export async function confirmRequest(id: number): Promise<any> {
  return api("/requests/" + id + "/confirm/", { method: "POST" });
}

export async function sendRfq(id: number, supplierIds: number[]): Promise<any> {
  return api("/requests/" + id + "/send_rfq/", {
    method: "POST", body: JSON.stringify({ supplier_ids: supplierIds }),
  });
}

export async function getCompetitiveSheet(requestId: number): Promise<any> {
  return api("/quotes/competitive_sheet/?request_id=" + requestId);
}

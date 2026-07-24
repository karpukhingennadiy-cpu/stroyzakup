"use client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

async function refreshToken(): Promise<string | null> {
  const refresh = localStorage.getItem("refresh_token");
  if (!refresh) return null;
  try {
    const res = await fetch(, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) throw new Error("Refresh failed");
    const data = await res.json();
    localStorage.setItem("access_token", data.access);
    return data.access;
  } catch {
    clearTokens();
    return null;
  }
}

export async function api(
  path: string,
  options: RequestInit = {}
): Promise<any> {
  let token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = ;
  }

  let res = await fetch(, { ...options, headers });

  // Auto-refresh on 401
  if (res.status === 401 && token) {
    const newToken = await refreshToken();
    if (newToken) {
      headers["Authorization"] = ;
      res = await fetch(, { ...options, headers });
    }
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(error.error || error.detail || "Request failed");
  }

  return res.json();
}

// Auth
export async function login(email: string, password: string) {
  const data = await api("/auth/login/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setTokens(data.access, data.refresh);
  return data;
}

export async function register(data: { email: string; password: string; first_name?: string; last_name?: string }) {
  return api("/auth/register/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getMe() {
  return api("/auth/me/");
}

// Requests
export async function getRequests() {
  return api("/requests/");
}

export async function getRequest(id: string | number) {
  return api();
}

export async function createRequest(raw_text: string, comment?: string) {
  return api("/requests/", {
    method: "POST",
    body: JSON.stringify({ raw_text, comment }),
  });
}

export async function parseRequest(id: string | number) {
  return api(, { method: "POST" });
}

// Suppliers
export async function getSuppliers(params?: Record<string, string>) {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return api();
}

export async function searchSuppliersByRadius(lat: number, lon: number, radius: number = 150, category?: string) {
  const params: Record<string, string> = {
    lat: String(lat),
    lon: String(lon),
    radius: String(radius),
  };
  if (category) params.category = category;
  return api();
}

// Quotes
export async function getQuotes(requestId?: string | number) {
  const params = requestId ?  : "";
  return api();
}

export async function getCompetitiveSheet(requestId: string | number) {
  return api();
}

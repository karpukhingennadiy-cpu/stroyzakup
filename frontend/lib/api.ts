"use client";

var API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setTokens(access, refresh) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

async function refreshAccessToken() {
  var refresh = localStorage.getItem("refresh_token");
  if (!refresh) return null;
  try {
    var res = await fetch(API_BASE + "/auth/token/refresh/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refresh }),
    });
    if (!res.ok) throw new Error("Refresh failed");
    var data = await res.json();
    localStorage.setItem("access_token", data.access);
    return data.access;
  } catch (e) {
    clearTokens();
    return null;
  }
}

export async function api(path, options) {
  if (!options) options = {};
  var token = getToken();
  var headers = Object.assign({ "Content-Type": "application/json" }, options.headers || {});
  if (token) headers["Authorization"] = "Bearer " + token;
  var res = await fetch(API_BASE + path, Object.assign({}, options, { headers: headers }));
  if (res.status === 401 && token) {
    var newToken = await refreshAccessToken();
    if (newToken) {
      headers["Authorization"] = "Bearer " + newToken;
      res = await fetch(API_BASE + path, Object.assign({}, options, { headers: headers }));
    }
  }
  if (!res.ok) {
    var error = await res.json().catch(function() { return { detail: res.statusText }; });
    throw new Error(error.detail || error.error || "HTTP " + res.status);
  }
  return res.json();
}

export async function login(email, password) {
  var data = await api("/auth/login/", { method: "POST", body: JSON.stringify({ email: email, password: password }) });
  setTokens(data.access, data.refresh);
  return data;
}

export async function registerUser(data) {
  return api("/auth/register/", { method: "POST", body: JSON.stringify(data) });
}

export async function getMe() { return api("/auth/me/"); }
export async function getRequests() { return api("/requests/"); }
export async function getRequest(id) { return api("/requests/" + id + "/"); }
export async function createRequest(raw_text, comment, deliveryAddress) {
  var body = { raw_text: raw_text, comment: comment };
  if (deliveryAddress) body.delivery_address = deliveryAddress;
  return api("/requests/", { method: "POST", body: JSON.stringify(body) });
}
export async function parseRequest(id) {
  return api("/requests/" + id + "/parse/", { method: "POST" });
}
export async function getSuppliers(params) {
  var qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return api("/suppliers/" + qs);
}
export async function searchSuppliersRadius(lat, lon, radius) {
  if (!radius) radius = 150;
  return api("/suppliers/search_radius/?lat=" + lat + "&lon=" + lon + "&radius=" + radius);
}
export async function getQuotes(requestId) {
  return api("/quotes/" + (requestId ? "?request_id=" + requestId : ""));
}

export async function geocodeAddress(address) {
  return api("/auth/geocode/", { method: "POST", body: JSON.stringify({ address: address }) });
}
export async function matchSuppliers(requestId, limit) {
  if (!limit) limit = 20;
  return api("/requests/" + requestId + "/match_suppliers/", {
    method: "POST", body: JSON.stringify({ limit: limit }),
  });
}
export async function confirmRequest(id) {
  return api("/requests/" + id + "/confirm/", { method: "POST" });
}
export async function sendRfq(id, supplierIds) {
  return api("/requests/" + id + "/send_rfq/", {
    method: "POST", body: JSON.stringify({ supplier_ids: supplierIds }),
  });
}

export async function getCompetitiveSheet(requestId) {
  return api("/quotes/competitive_sheet/?request_id=" + requestId);
}
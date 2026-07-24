"use client";

var API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

function setTokens(access, refresh) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

async function refreshToken() {
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

async function api(path, options) {
  if (!options) options = {};
  var token = getToken();
  var headers = Object.assign({ "Content-Type": "application/json" }, options.headers || {});
  if (token) headers["Authorization"] = "Bearer " + token;

  var res = await fetch(API_BASE + path, Object.assign({}, options, { headers: headers }));

  if (res.status === 401 && token) {
    var newToken = await refreshToken();
    if (newToken) {
      headers["Authorization"] = "Bearer " + newToken;
      res = await fetch(API_BASE + path, Object.assign({}, options, { headers: headers }));
    }
  }

  if (!res.ok) {
    var error = await res.json().catch(function() { return { error: res.statusText }; });
    throw new Error(error.error || error.detail || "Request failed");
  }

  return res.json();
}

async function login(email, password) {
  var data = await api("/auth/login/", {
    method: "POST",
    body: JSON.stringify({ email: email, password: password }),
  });
  setTokens(data.access, data.refresh);
  return data;
}

async function registerUser(data) {
  return api("/auth/register/", { method: "POST", body: JSON.stringify(data) });
}

async function getMe() { return api("/auth/me/"); }
async function getRequests() { return api("/requests/"); }
async function getRequest(id) { return api("/requests/" + id + "/"); }
async function createRequest(raw_text, comment) {
  return api("/requests/", { method: "POST", body: JSON.stringify({ raw_text: raw_text, comment: comment }) });
}
async function parseRequest(id) {
  return api("/requests/" + id + "/parse/", { method: "POST" });
}
async function getSuppliers(params) {
  var qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return api("/suppliers/" + qs);
}
async function searchSuppliersByRadius(lat, lon, radius) {
  if (!radius) radius = 150;
  return api("/suppliers/search_radius/?lat=" + lat + "&lon=" + lon + "&radius=" + radius);
}
async function getQuotes(requestId) {
  var qs = requestId ? "?request_id=" + requestId : "";
  return api("/quotes/" + qs);
}
async function getCompetitiveSheet(requestId) {
  return api("/quotes/competitive_sheet/?request_id=" + requestId);
}

/**
 * Browser-side session helper.
 * Demo mode stores a JSON blob in localStorage. That is not authentication.
 * Replace getToken() / login() wiring with real cookies or JWT from FastAPI.
 */
import { config } from "./config.js";
import * as authApi from "./api/auth.js";

export function getSession() {
  try {
    const raw = localStorage.getItem(config.sessionKey);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setSession(session) {
  localStorage.setItem(config.sessionKey, JSON.stringify(session));
}

export function clearSession() {
  localStorage.removeItem(config.sessionKey);
}

export function getCurrentUser() {
  return getSession()?.user || null;
}

export function getToken() {
  return getSession()?.token || null;
}

export function isAuthenticated() {
  return Boolean(getCurrentUser());
}

export function isAdmin() {
  return getCurrentUser()?.role === "admin";
}

export async function login(credentials) {
  const result = await authApi.login(credentials);
  setSession({
    token: result.token,
    user: result.user,
    demo: result.demo === true,
    issuedAt: new Date().toISOString(),
  });
  return result.user;
}

export async function register(payload) {
  const result = await authApi.register(payload);
  setSession({
    token: result.token,
    user: result.user,
    demo: result.demo === true,
    issuedAt: new Date().toISOString(),
  });
  return result.user;
}

export async function loginWithGoogle() {
  const result = await authApi.loginWithGoogle();
  setSession({
    token: result.token,
    user: result.user,
    demo: result.demo === true,
    issuedAt: new Date().toISOString(),
  });
  return result.user;
}

export function logout() {
  clearSession();
}

export function requireAuth(loginHref = "login.html") {
  if (!isAuthenticated()) {
    const next = encodeURIComponent(location.pathname.split("/").pop() + location.search);
    location.replace(`${loginHref}?next=${next}`);
    return false;
  }
  return true;
}

export function requireAdmin() {
  if (!requireAuth()) return false;
  if (!isAdmin()) {
    location.replace("index.html");
    return false;
  }
  return true;
}

export function redirectIfAuthed() {
  if (isAuthenticated()) {
    const params = new URLSearchParams(location.search);
    location.replace(params.get("next") || "index.html");
  }
}

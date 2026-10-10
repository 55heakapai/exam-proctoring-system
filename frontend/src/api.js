export const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const WS_BASE = API.replace(/^http/, "ws");

const KEY = "es_auth";
export const getAuth = () => JSON.parse(localStorage.getItem(KEY) || "null");
export const setAuth = (a) => localStorage.setItem(KEY, JSON.stringify(a));
export const clearAuth = () => localStorage.removeItem(KEY);
export const getToken = () => getAuth()?.access_token;

export async function api(path, { method = "GET", body } = {}) {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: { "Content-Type": "application/json", ...(getToken() && { Authorization: `Bearer ${getToken()}` }) },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail?.toString() || `Request failed (${res.status})`);
  }
  return res.json();
}

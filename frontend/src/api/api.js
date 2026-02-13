const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";
const TOKEN_KEY = "rps_token";

let token = null;

function loadToken() {
  if (token) return token;
  try {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (stored) token = stored;
  } catch (_) {}
  return token;
}

export function setToken(jwt) {
  token = jwt;
  try {
    if (jwt) localStorage.setItem(TOKEN_KEY, jwt);
    else localStorage.removeItem(TOKEN_KEY);
  } catch (_) {}
}

export function getToken() {
  return token || loadToken();
}

async function request(path, method, body = null) {
  const authToken = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    },
    body: body ? JSON.stringify(body) : null,
  });

  if (!res.ok) {
    const err = new Error("API request failed");
    err.status = res.status;
    try {
      err.data = await res.json();
    } catch (_) {}
    throw err;
  }

  return res.json();
}

export function apiPost(path, body = {}) {
  return request(path, "POST", body);
}

export function apiGet(path) {
  return request(path, "GET");
}

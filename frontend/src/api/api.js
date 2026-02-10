const API_BASE = "http://127.0.0.1:8000/api";

let token = null;

export function setToken(jwt) {
  token = jwt;
}

export function getToken() {
  return token;
}

async function request(path, method, body = null) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: body ? JSON.stringify(body) : null
  });

  if (!res.ok) {
    throw new Error("API request failed");
  }

  return res.json();
}

export function apiPost(path, body = {}) {
  return request(path, "POST", body);
}

export function apiGet(path) {
  return request(path, "GET");
}

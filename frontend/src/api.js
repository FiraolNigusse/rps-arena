const API_BASE = "http://127.0.0.1:8000/api";

let token = null;

export function setToken(jwt) {
  token = jwt;
}

export async function apiPost(path, body = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(body)
  });

  return res.json();
}

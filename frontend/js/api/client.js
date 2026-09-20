import { config } from "../config.js";

export class ApiError extends Error {
  constructor(message, { status = 400, code = "API_ERROR" } = {}) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export async function request(path, { method = "GET", body, token } = {}) {
  const headers = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${config.apiBase}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text };
    }
  }

  if (!res.ok) {
    throw new ApiError(data?.message || `Request failed (${res.status})`, {
      status: res.status,
      code: data?.code || "HTTP_ERROR",
    });
  }
  return data;
}

export function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function mockWait() {
  const { min, max } = config.mockLatencyMs;
  return delay(min + Math.floor(Math.random() * (max - min)));
}

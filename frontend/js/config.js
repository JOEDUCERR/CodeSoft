/**
 * Single place for frontend-to-backend wiring.
 *
 * Production (Nginx): apiBase stays "/api" so the same origin serves
 * static files and reverse-proxies FastAPI.
 *
 * useMock is false: the FastAPI API is the source of truth. Do not put
 * host IPs or secrets here.
 *
 * Demo auth in localStorage is not production security.
 */
export const config = {
  apiBase: "/api",
  useMock: false,
  mockLatencyMs: { min: 280, max: 720 },
  sessionKey: "codesoft.session",
  storeKeys: {
    problems: "codesoft.store.problems",
    submissions: "codesoft.store.submissions",
    profile: "codesoft.store.profile",
  },
};

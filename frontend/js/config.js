/**
 * Single place for frontend-to-backend wiring.
 *
 * Production (Nginx): apiBase stays "/api" so the same origin serves
 * static files and reverse-proxies FastAPI.
 *
 * useMock: true until the backend exists. Flip to false when
 * FastAPI routes are live. Do not put host IPs or secrets here.
 *
 * Demo auth in localStorage is not production security.
 */
export const config = {
  apiBase: "/api",
  useMock: true,
  mockLatencyMs: { min: 280, max: 720 },
  sessionKey: "codesoft.session",
  storeKeys: {
    problems: "codesoft.store.problems",
    submissions: "codesoft.store.submissions",
    profile: "codesoft.store.profile",
  },
};

import { config } from "../config.js";
import { ApiError, mockWait, request } from "./client.js";
import { MOCK_PROBLEMS } from "../../data/problems.js";
import { store } from "./store.js";

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

export function getProblemCatalog() {
  const overlay = store.getProblemsOverlay();
  return overlay ? clone(overlay) : clone(MOCK_PROBLEMS);
}

export function persistProblemCatalog(problems) {
  store.setProblemsOverlay(problems);
}

function token() {
  try {
    const raw = localStorage.getItem(config.sessionKey);
    return raw ? JSON.parse(raw).token : null;
  } catch {
    return null;
  }
}

export async function listProblems({ q = "", difficulty = "all", language = "all", includeUnpublished = false } = {}) {
  if (config.useMock) {
    await mockWait();
    let items = getProblemCatalog();
    if (!includeUnpublished) items = items.filter((p) => p.published);
    const query = q.trim().toLowerCase();
    if (query) {
      items = items.filter(
        (p) =>
          p.title.toLowerCase().includes(query) ||
          p.tags.some((t) => t.toLowerCase().includes(query)) ||
          p.slug.toLowerCase().includes(query)
      );
    }
    if (difficulty !== "all") {
      items = items.filter((p) => p.difficulty.toLowerCase() === difficulty.toLowerCase());
    }
    if (language !== "all") {
      items = items.filter((p) => p.languages.includes(language));
    }
    return items.map((p) => ({
      id: p.id,
      slug: p.slug,
      title: p.title,
      difficulty: p.difficulty,
      tags: p.tags,
      published: p.published,
      languages: p.languages,
    }));
  }
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (difficulty && difficulty !== "all") params.set("difficulty", difficulty);
  if (language && language !== "all") params.set("language", language);
  const qs = params.toString();
  return request(`/problems${qs ? `?${qs}` : ""}`, { token: token() });
}

export async function getProblem(idOrSlug) {
  if (config.useMock) {
    await mockWait();
    const problem = getProblemCatalog().find((p) => p.id === idOrSlug || p.slug === idOrSlug);
    if (!problem || !problem.published) {
      throw new ApiError("Problem not found.", { status: 404, code: "NOT_FOUND" });
    }
    return problem;
  }
  return request(`/problems/${encodeURIComponent(idOrSlug)}`, { token: token() });
}

export async function getProblemAdmin(idOrSlug) {
  if (config.useMock) {
    await mockWait();
    const problem = getProblemCatalog().find((p) => p.id === idOrSlug || p.slug === idOrSlug);
    if (!problem) throw new ApiError("Problem not found.", { status: 404, code: "NOT_FOUND" });
    return problem;
  }
  return request(`/admin/problems/${encodeURIComponent(idOrSlug)}`, { token: token() });
}

export async function saveProblem(problem) {
  if (config.useMock) {
    await mockWait();
    const list = getProblemCatalog();
    const idx = list.findIndex((p) => p.id === problem.id);
    if (idx >= 0) list[idx] = problem;
    else list.unshift(problem);
    persistProblemCatalog(list);
    return problem;
  }
  if (problem.id && !String(problem.id).startsWith("new")) {
    return request(`/admin/problems/${encodeURIComponent(problem.id)}`, {
      method: "PATCH",
      body: problem,
      token: token(),
    });
  }
  return request("/admin/problems", { method: "POST", body: problem, token: token() });
}

export async function deleteProblem(id) {
  if (config.useMock) {
    await mockWait();
    persistProblemCatalog(getProblemCatalog().filter((p) => p.id !== id));
    return { ok: true };
  }
  return request(`/admin/problems/${encodeURIComponent(id)}`, { method: "DELETE", token: token() });
}

export async function setPublished(id, published) {
  if (config.useMock) {
    await mockWait();
    const list = getProblemCatalog();
    const item = list.find((p) => p.id === id);
    if (!item) throw new ApiError("Problem not found.", { status: 404, code: "NOT_FOUND" });
    item.published = published;
    persistProblemCatalog(list);
    return item;
  }
  return request(`/admin/problems/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: { published },
    token: token(),
  });
}

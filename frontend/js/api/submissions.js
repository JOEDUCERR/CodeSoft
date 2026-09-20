import { config } from "../config.js";
import { ApiError, mockWait, request } from "./client.js";
import { MOCK_SUBMISSIONS } from "../../data/submissions.js";
import { store } from "./store.js";
import { getProblemCatalog } from "./problems.js";
import { judge } from "./mockJudge.js";

function token() {
  try {
    const raw = localStorage.getItem(config.sessionKey);
    return raw ? JSON.parse(raw).token : null;
  } catch {
    return null;
  }
}

function allSubmissions() {
  return [...store.getExtraSubmissions(), ...MOCK_SUBMISSIONS];
}

export async function listSubmissions() {
  if (config.useMock) {
    await mockWait();
    return allSubmissions();
  }
  return request("/submissions", { token: token() });
}

export async function getSubmission(id) {
  if (config.useMock) {
    await mockWait();
    const item = allSubmissions().find((s) => s.id === id);
    if (!item) throw new ApiError("Submission not found.", { status: 404, code: "NOT_FOUND" });
    return item;
  }
  return request(`/submissions/${encodeURIComponent(id)}`, { token: token() });
}

export async function runCode({ problemId, language, code }) {
  if (config.useMock) {
    await mockWait();
    const problem = getProblemCatalog().find((p) => p.id === problemId);
    if (!problem) throw new ApiError("Problem not found.", { status: 404, code: "NOT_FOUND" });
    return judge({ problem, language, code, mode: "run" });
  }
  return request("/run", { method: "POST", body: { problemId, language, code }, token: token() });
}

export async function submitCode({ problemId, language, code }) {
  if (config.useMock) {
    await mockWait();
    const problem = getProblemCatalog().find((p) => p.id === problemId);
    if (!problem) throw new ApiError("Problem not found.", { status: 404, code: "NOT_FOUND" });
    const result = judge({ problem, language, code, mode: "submit" });
    const submission = {
      id: `s_${Date.now()}`,
      problemId,
      problemTitle: problem.title,
      language,
      status: result.status,
      runtimeMs: result.runtimeMs,
      memoryKb: result.memoryKb,
      createdAt: new Date().toISOString(),
      code,
      testsPassed: result.testsPassed,
      testsTotal: result.testsTotal,
      cases: result.cases,
    };
    store.addSubmission(submission);
    return submission;
  }
  return request("/submissions", {
    method: "POST",
    body: { problemId, language, code },
    token: token(),
  });
}

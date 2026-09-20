/**
 * Mock judge used only when config.useMock is true.
 * Does not execute user code. Deterministic for demos:
 * unchanged starter templates fail; edited code is accepted
 * unless it looks empty or contains obvious error markers.
 */
export const STATUSES = [
  "Accepted",
  "Wrong Answer",
  "Runtime Error",
  "Compilation Error",
  "Time Limit Exceeded",
  "Memory Limit Exceeded",
  "Pending",
  "Running",
];

function normalize(code) {
  return (code || "").replace(/\s+/g, " ").trim();
}

function looksEmpty(code) {
  const n = normalize(code);
  if (n.length < 24) return true;
  const stripped = n
    .replace(/from typing import.*/, "")
    .replace(/#include.*/, "")
    .replace(/using namespace std;/, "")
    .replace(/import java\.util\.\*;/, "")
    .replace(/class Solution[^{]*\{/, "")
    .replace(/public: /, "")
    .replace(/pass/, "")
    .replace(/return -1;/, "")
    .replace(/\{\s*\}/g, "")
    .trim();
  return stripped.length < 20;
}

function hash(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0;
  return h;
}

export function judge({ problem, language, code, mode }) {
  const starter = problem.starter?.[language] || "";
  const edited = normalize(code) !== normalize(starter);
  const empty = looksEmpty(code);
  const tests = problem.tests || [];
  const samples = tests.filter((t) => t.sample);
  const pool = mode === "run" ? (samples.length ? samples : tests.slice(0, 1)) : tests;

  let status = "Accepted";
  if (!edited || empty) status = "Wrong Answer";
  else if (/syntax error|undefined_name|;;;;/.test(code)) status = "Compilation Error";
  else if (/while\s*\(\s*true\s*\)|while True/.test(code)) status = "Time Limit Exceeded";
  else if (/raise |throw new |segfault/.test(code)) status = "Runtime Error";

  const seed = hash(code + language + problem.id);
  const runtimeMs = status === "Compilation Error" ? 0 : 8 + (seed % 90);
  const memoryKb = status === "Compilation Error" ? 0 : 12000 + (seed % 28000);

  const cases = pool.map((t, i) => {
    const pass = status === "Accepted";
    return {
      index: i + 1,
      input: t.input,
      expected: t.output,
      output: pass ? t.output : status === "Wrong Answer" ? "(empty)" : "",
      passed: pass,
      sample: Boolean(t.sample),
    };
  });

  const passed = cases.filter((c) => c.passed).length;
  return {
    status,
    runtimeMs,
    memoryKb,
    stdout: status === "Accepted" ? cases.map((c) => c.output).join("\n") : "",
    stderr:
      status === "Compilation Error"
        ? "error: expected expression before end of input"
        : status === "Runtime Error"
          ? "RuntimeError: mock exception"
          : "",
    testsPassed: passed,
    testsTotal: cases.length,
    cases,
    mode,
    language,
    problemId: problem.id,
  };
}

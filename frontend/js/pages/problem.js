import { getProblem } from "../api/problems.js";
import { runCode, submitCode } from "../api/submissions.js";
import { ApiError } from "../api/client.js";
import { attachEditor } from "../components/editor.js";
import { difficultyClass, statusClass, formatMemory, formatRuntime } from "../components/status.js";
import { escapeHtml } from "../components/header.js";
import { setBusy } from "../components/forms.js";
import { toast } from "../components/toast.js";

const params = new URLSearchParams(location.search);
const id = params.get("id") || params.get("slug") || "two-sum";

const problemRoot = document.getElementById("problem-pane");
const language = document.getElementById("language");
const editor = document.getElementById("editor");
const runBtn = document.getElementById("run-btn");
const submitBtn = document.getElementById("submit-btn");
const outputBody = document.getElementById("output-body");
const outputPane = document.getElementById("output-pane");
const collapseBtn = document.getElementById("collapse-output");

let problem = null;
let lastRun = null;
let lastSubmission = null;
let tab = "output";

attachEditor(editor);

function setTab(name) {
  tab = name;
  document.querySelectorAll(".output-tabs [data-tab]").forEach((btn) => {
    btn.setAttribute("aria-selected", String(btn.dataset.tab === tab));
  });
  renderOutput();
}

document.querySelectorAll(".output-tabs [data-tab]").forEach((btn) => {
  btn.addEventListener("click", () => setTab(btn.dataset.tab));
});

collapseBtn?.addEventListener("click", () => {
  const collapsed = outputPane.classList.toggle("collapsed");
  outputBody.hidden = collapsed;
  collapseBtn.textContent = collapsed ? "Expand" : "Collapse";
});

function renderProblem() {
  const examples = (problem.examples || [])
    .map(
      (ex, i) => `<div class="example-block">
        <h3>Example ${i + 1}</h3>
        <p><strong>Input:</strong> <code>${escapeHtml(ex.input)}</code></p>
        <p><strong>Output:</strong> <code>${escapeHtml(ex.output)}</code></p>
        ${ex.explanation ? `<p class="muted">${escapeHtml(ex.explanation)}</p>` : ""}
      </div>`
    )
    .join("");
  const constraints = (problem.constraints || []).map((c) => `<li>${escapeHtml(c)}</li>`).join("");
  problemRoot.innerHTML = `
    <div class="problem-meta">
      <span class="${difficultyClass(problem.difficulty)}">${escapeHtml(problem.difficulty)}</span>
      <span class="muted">${problem.tags.map(escapeHtml).join(" · ")}</span>
    </div>
    <h1>${escapeHtml(problem.title)}</h1>
    <p>${escapeHtml(problem.description).replace(/\n\n/g, "</p><p>").replace(/\n/g, "<br>")}</p>
    ${examples}
    <h2>Constraints</h2>
    <div class="constraint-list"><ul>${constraints}</ul></div>
    <h2>I/O</h2>
    <p><strong>Input</strong></p>
    <pre>${escapeHtml(problem.inputFormat)}</pre>
    <p><strong>Output</strong></p>
    <pre>${escapeHtml(problem.outputFormat)}</pre>
  `;
}

function loadStarter() {
  editor.value = problem.starter?.[language.value] || "";
}

language.addEventListener("change", loadStarter);

function renderCases(cases) {
  if (!cases?.length) return `<p class="muted">No test case details.</p>`;
  return cases
    .map(
      (c) => `<div class="case-block">
        <h4>Test Case ${c.index} ${c.passed ? '<span class="badge badge-ok">Passed</span>' : '<span class="badge badge-err">Failed</span>'}</h4>
        <p><strong>Input</strong></p><pre>${escapeHtml(c.input)}</pre>
        <p><strong>Output</strong></p><pre>${escapeHtml(c.output || "—")}</pre>
        <p><strong>Expected</strong></p><pre>${escapeHtml(c.expected)}</pre>
      </div>`
    )
    .join("");
}

function renderOutput() {
  if (tab === "output") {
    if (!lastRun && !lastSubmission) {
      outputBody.innerHTML = `<p class="muted">Run or submit code to see results. The browser does not execute code; this talks to POST /api/run or the mock judge.</p>`;
      return;
    }
    const r = lastRun || lastSubmission;
    outputBody.innerHTML = `
      <p>Status: <span class="${statusClass(r.status)}">${escapeHtml(r.status)}</span></p>
      <p>Execution time: ${formatRuntime(r.runtimeMs)} · Memory: ${formatMemory(r.memoryKb)}</p>
      ${r.stdout ? `<p><strong>Stdout</strong></p><pre>${escapeHtml(r.stdout)}</pre>` : ""}
      ${r.stderr ? `<p><strong>Stderr</strong></p><pre>${escapeHtml(r.stderr)}</pre>` : ""}
    `;
    return;
  }
  if (tab === "tests") {
    const cases = lastSubmission?.cases || lastRun?.cases;
    outputBody.innerHTML = cases ? renderCases(cases) : `<p class="muted">No test results yet.</p>`;
    return;
  }
  if (!lastSubmission) {
    outputBody.innerHTML = `<p class="muted">No submission in this session.</p>`;
    return;
  }
  const s = lastSubmission;
  outputBody.innerHTML = `
    <p>Status: <span class="${statusClass(s.status)}">${escapeHtml(s.status)}</span></p>
    <p>Language: ${escapeHtml(s.language)}</p>
    <p>Tests: ${s.testsPassed}/${s.testsTotal}</p>
    <p>Time: ${formatRuntime(s.runtimeMs)} · Memory: ${formatMemory(s.memoryKb)}</p>
    <p>Submitted: ${new Date(s.createdAt).toLocaleString()}</p>
  `;
}

runBtn.addEventListener("click", async () => {
  setBusy(runBtn, true, "Running...");
  submitBtn.disabled = true;
  try {
    lastRun = await runCode({ problemId: problem.id, language: language.value, code: editor.value });
    setTab("output");
    toast(`Run finished: ${lastRun.status}`, lastRun.status === "Accepted" ? "ok" : "error");
  } catch (err) {
    outputBody.innerHTML = `<p class="page-error">${escapeHtml(err instanceof ApiError ? err.message : "Execution failed.")}</p>`;
  } finally {
    setBusy(runBtn, false);
    submitBtn.disabled = false;
  }
});

submitBtn.addEventListener("click", async () => {
  setBusy(submitBtn, true, "Submitting...");
  runBtn.disabled = true;
  try {
    lastSubmission = await submitCode({ problemId: problem.id, language: language.value, code: editor.value });
    lastRun = lastSubmission;
    setTab("details");
    toast(`Submission: ${lastSubmission.status}`, lastSubmission.status === "Accepted" ? "ok" : "error");
  } catch (err) {
    outputBody.innerHTML = `<p class="page-error">${escapeHtml(err instanceof ApiError ? err.message : "Submission failed.")}</p>`;
  } finally {
    setBusy(submitBtn, false);
    runBtn.disabled = false;
  }
});

async function init() {
  try {
    problem = await getProblem(id);
    document.title = `${problem.title} · CodeSoft`;
    renderProblem();
    loadStarter();
    renderOutput();
  } catch (err) {
    problemRoot.innerHTML = `<p class="page-error">${err instanceof ApiError ? err.message : "Problem not found."}</p>`;
    runBtn.disabled = true;
    submitBtn.disabled = true;
  }
}

init();

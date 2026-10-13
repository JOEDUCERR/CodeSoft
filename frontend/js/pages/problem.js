import { getProblem } from "../api/problems.js";
import { getSubmission, runCode, submitCode } from "../api/submissions.js";
import { ApiError } from "../api/client.js";
import { attachEditor } from "../components/editor.js";
import { difficultyClass, statusClass, formatMemory, formatRuntime } from "../components/status.js";
import { escapeHtml } from "../components/header.js";
import { toast } from "../components/toast.js";

const params = new URLSearchParams(location.search);
const id = params.get("id") || params.get("slug") || "two-sum";
const POLL_INTERVAL_MS = 750;
const EXECUTION_TIMEOUT_MS = 120_000;

const problemRoot = document.getElementById("problem-pane");
const language = document.getElementById("language");
const editor = document.getElementById("editor");
const runBtn = document.getElementById("run-btn");
const submitBtn = document.getElementById("submit-btn");
const outputBody = document.getElementById("output-body");
const outputPane = document.getElementById("output-pane");
const collapseBtn = document.getElementById("collapse-output");

let problem = null;
let currentResult = null;
let currentMode = null;
let tab = "output";
let executionGeneration = 0;
let executionActive = false;
let pollTimer = null;
let executionNotice = "";
let draftStorageWarningShown = false;

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
  try {
    const savedDraft = localStorage.getItem(draftKey());
    editor.value = savedDraft === null ? problem.starter?.[language.value] || "" : savedDraft;
  } catch (error) {
    editor.value = problem.starter?.[language.value] || "";
    warnDraftStorage(error);
  }
}

function draftKey() {
  return `codesoft.draft.${encodeURIComponent(problem.id)}.${encodeURIComponent(language.value)}`;
}

function warnDraftStorage(error) {
  if (draftStorageWarningShown) return;
  draftStorageWarningShown = true;
  console.error("Unable to access the editor draft in local storage.", error);
  toast("The editor draft could not be saved or restored in this browser.", "error");
}

editor.addEventListener("input", () => {
  if (!problem) return;
  try {
    localStorage.setItem(draftKey(), editor.value);
  } catch (error) {
    warnDraftStorage(error);
  }
});

language.addEventListener("change", loadStarter);

function renderCases(cases) {
  if (!cases?.length) return `<p class="muted">No test case details.</p>`;
  return cases
    .map(
      (c) => `<details class="case-block">
        <summary>Test Case ${escapeHtml(c.index)} ${c.passed ? '<span class="badge badge-ok">Passed</span>' : '<span class="badge badge-err">Failed</span>'}</summary>
        <p><strong>Input</strong></p><pre>${escapeHtml(c.input ?? "—")}</pre>
        <p><strong>Actual output</strong></p><pre>${escapeHtml(c.output || c.actual || "—")}</pre>
        <p><strong>Expected output</strong></p><pre>${escapeHtml(c.expected ?? "—")}</pre>
        ${c.error ? `<p><strong>Error</strong></p><pre>${escapeHtml(c.error)}</pre>` : ""}
      </details>`
    )
    .join("");
}

function hasStructuredCaseOutput(result) {
  if (!result.stdout || !result.cases?.length) return false;
  try {
    const output = JSON.parse(result.stdout);
    return Array.isArray(output) && output.length === result.cases.length &&
      output.every((testCase) => typeof testCase?.passed === "boolean");
  } catch {
    return false;
  }
}

function renderOutput() {
  if (tab === "output") {
    if (!currentResult) {
      outputBody.innerHTML = `<p class="muted">${escapeHtml(executionNotice || "Run or submit code to see results. Execution runs on the backend.")}</p>`;
      return;
    }
    const r = currentResult;
    const label = currentMode === "run" ? "Run Result" : "Submit Result";
    outputBody.innerHTML = `
      <div class="execution-result-head">
        <h3>${label}</h3>
        <span class="${statusClass(r.status)}">${escapeHtml(r.status || "Unknown")}</span>
      </div>
      ${r.cases?.length ? `<p>Passed: ${escapeHtml(r.testsPassed ?? 0)} / ${escapeHtml(r.testsTotal ?? r.cases.length)} test cases</p>` : ""}
      <p>Execution time: ${formatRuntime(r.runtimeMs)} · Memory: ${formatMemory(r.memoryKb)}</p>
      ${r.stdout && !hasStructuredCaseOutput(r) ? `<p><strong>Stdout</strong></p><pre>${escapeHtml(r.stdout)}</pre>` : ""}
      ${hasStructuredCaseOutput(r) ? `<p class="muted">Structured test output is available in the Test Cases tab.</p>` : ""}
      ${r.stderr ? `<p><strong>Stderr</strong></p><pre>${escapeHtml(r.stderr)}</pre>` : ""}
      ${executionNotice ? `<p class="page-error" role="status">${escapeHtml(executionNotice)}</p>` : ""}
    `;
    return;
  }
  if (tab === "tests") {
    outputBody.innerHTML = currentResult?.cases
      ? renderCases(currentResult.cases)
      : `<p class="muted">No test results yet.</p>`;
    return;
  }
  if (!currentResult) {
    outputBody.innerHTML = `<p class="muted">No execution in this session.</p>`;
    return;
  }
  const s = currentResult;
  outputBody.innerHTML = `
    <p>Type: ${currentMode === "run" ? "Run (sample tests)" : "Submit (full test suite)"}</p>
    <p>Status: <span class="${statusClass(s.status)}">${escapeHtml(s.status)}</span></p>
    <p>Language: ${escapeHtml(s.language)}</p>
    ${s.cases?.length ? `<p>Tests passed: ${escapeHtml(s.testsPassed ?? 0)}/${escapeHtml(s.testsTotal ?? s.cases.length)}</p>` : ""}
    <p>Time: ${formatRuntime(s.runtimeMs)} · Memory: ${formatMemory(s.memoryKb)}</p>
    ${s.createdAt ? `<p>Submitted: ${escapeHtml(new Date(s.createdAt).toLocaleString())}</p>` : ""}
    ${s.stderr ? `<p><strong>Stderr</strong></p><pre>${escapeHtml(s.stderr)}</pre>` : ""}
    ${executionNotice ? `<p class="page-error" role="status">${escapeHtml(executionNotice)}</p>` : ""}
  `;
}

function setExecutionControls(busy, mode) {
  runBtn.disabled = busy;
  submitBtn.disabled = busy;
  language.disabled = busy;
  runBtn.textContent = busy && mode === "run" ? "Running..." : "Run";
  submitBtn.textContent = busy && mode === "submit" ? "Submitting..." : "Submit";
}

function stopPolling() {
  if (pollTimer !== null) {
    clearTimeout(pollTimer);
    pollTimer = null;
  }
}

function isCurrentExecution(generation) {
  return generation === executionGeneration;
}

function isTerminal(status) {
  return Boolean(status) && status !== "Queued" && status !== "Running";
}

function finishExecution(generation) {
  if (!isCurrentExecution(generation)) return;
  stopPolling();
  executionActive = false;
  setExecutionControls(false, currentMode);
}

function schedulePoll(generation, submissionId, startedAt) {
  if (!isCurrentExecution(generation)) return;
  const remaining = EXECUTION_TIMEOUT_MS - (Date.now() - startedAt);
  if (remaining <= 0) {
    executionNotice = "Status polling stopped after two minutes. This job may still be running; check Submissions for its latest status.";
    finishExecution(generation);
    renderOutput();
    return;
  }
  pollTimer = setTimeout(() => pollSubmission(generation, submissionId, startedAt), Math.min(POLL_INTERVAL_MS, remaining));
}

async function pollSubmission(generation, submissionId, startedAt) {
  if (!isCurrentExecution(generation)) return;
  try {
    const result = await getSubmission(submissionId);
    if (!isCurrentExecution(generation)) return;
    currentResult = result;
    executionNotice = "";
    renderOutput();
    if (isTerminal(result.status)) {
      finishExecution(generation);
      toast(`${currentMode === "run" ? "Run" : "Submission"} finished: ${result.status}`, result.status === "Accepted" ? "ok" : "error");
      return;
    }
    schedulePoll(generation, submissionId, startedAt);
  } catch (err) {
    if (!isCurrentExecution(generation)) return;
    executionNotice = `Could not refresh execution status: ${err instanceof ApiError ? err.message : "request failed."} Polling has stopped.`;
    finishExecution(generation);
    renderOutput();
    toast("Could not refresh execution status.", "error");
  }
}

async function execute(mode) {
  if (executionActive || !problem) return;
  stopPolling();
  executionActive = true;
  const generation = ++executionGeneration;
  const startedAt = Date.now();
  const payload = { problemId: problem.id, language: language.value, code: editor.value };
  currentMode = mode;
  currentResult = null;
  executionNotice = mode === "run" ? "Queueing run..." : "Queueing submission...";
  setExecutionControls(true, mode);
  setTab("output");
  renderOutput();

  try {
    const result = mode === "run" ? await runCode(payload) : await submitCode(payload);
    if (!isCurrentExecution(generation)) return;
    currentResult = result;
    executionNotice = "";
    renderOutput();
    if (isTerminal(result.status)) {
      finishExecution(generation);
      toast(`${mode === "run" ? "Run" : "Submission"} finished: ${result.status}`, result.status === "Accepted" ? "ok" : "error");
      return;
    }
    if (!result.id) {
      executionNotice = "The backend queued this execution without returning a submission ID, so its status cannot be refreshed.";
      finishExecution(generation);
      renderOutput();
      return;
    }
    schedulePoll(generation, result.id, startedAt);
  } catch (err) {
    if (!isCurrentExecution(generation)) return;
    executionNotice = err instanceof ApiError ? err.message : "Execution request failed.";
    finishExecution(generation);
    renderOutput();
  }
}

runBtn.addEventListener("click", () => execute("run"));
submitBtn.addEventListener("click", () => execute("submit"));

window.addEventListener("pagehide", () => {
  stopPolling();
  executionGeneration += 1;
  executionActive = false;
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

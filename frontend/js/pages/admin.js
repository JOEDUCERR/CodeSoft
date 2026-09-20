import {
  listProblems,
  getProblemAdmin,
  saveProblem,
  deleteProblem,
  setPublished,
} from "../api/problems.js";
import { escapeHtml } from "../components/header.js";
import { difficultyClass, statusClass } from "../components/status.js";
import { toast } from "../components/toast.js";
import { setBusy } from "../components/forms.js";

const rowsEl = document.getElementById("admin-rows");
const form = document.getElementById("problem-form");
const testsEl = document.getElementById("test-cases");
const empty = document.getElementById("empty");
const newBtn = document.getElementById("new-problem");
const saveBtn = document.getElementById("save-problem");
const deleteBtn = document.getElementById("delete-problem");

let current = null;

function blankProblem() {
  return {
    id: `p_${Date.now()}`,
    slug: "",
    title: "",
    difficulty: "Easy",
    tags: [],
    published: false,
    languages: ["python", "cpp", "java"],
    description: "",
    inputFormat: "",
    outputFormat: "",
    examples: [{ input: "", output: "", explanation: "" }],
    constraints: [""],
    starter: {
      python: "class Solution:\n    def solve(self):\n        pass\n",
      cpp: "class Solution {\npublic:\n    void solve() {}\n};\n",
      java: "class Solution {\n    public void solve() {}\n}\n",
    },
    tests: [{ input: "", output: "", sample: true }],
  };
}

function fillForm(p) {
  current = p;
  form.title.value = p.title;
  form.slug.value = p.slug;
  form.difficulty.value = p.difficulty;
  form.tags.value = (p.tags || []).join(", ");
  form.published.checked = Boolean(p.published);
  form.description.value = p.description;
  form.constraints.value = (p.constraints || []).join("\n");
  form.examples.value = (p.examples || [])
    .map((e) => `Input: ${e.input}\nOutput: ${e.output}${e.explanation ? `\nExplanation: ${e.explanation}` : ""}`)
    .join("\n\n");
  form.inputFormat.value = p.inputFormat || "";
  form.outputFormat.value = p.outputFormat || "";
  form.starterPython.value = p.starter?.python || "";
  form.starterCpp.value = p.starter?.cpp || "";
  form.starterJava.value = p.starter?.java || "";
  renderTests(p.tests || []);
  deleteBtn.hidden = false;
}

function renderTests(tests) {
  testsEl.innerHTML = tests
    .map(
      (t, i) => `<div class="test-case-row" data-i="${i}">
        <label>Input<textarea name="tin">${escapeHtml(t.input)}</textarea></label>
        <label>Output<textarea name="tout">${escapeHtml(t.output)}</textarea></label>
        <div>
          <label><input type="checkbox" name="tsample" ${t.sample ? "checked" : ""}> Sample</label>
          <button type="button" class="btn btn-secondary" data-remove>Remove</button>
        </div>
      </div>`
    )
    .join("");
}

testsEl.addEventListener("click", (e) => {
  if (!e.target.matches("[data-remove]")) return;
  e.target.closest(".test-case-row").remove();
});

document.getElementById("add-test")?.addEventListener("click", () => {
  const wrap = document.createElement("div");
  wrap.className = "test-case-row";
  wrap.innerHTML = `<label>Input<textarea name="tin"></textarea></label>
    <label>Output<textarea name="tout"></textarea></label>
    <div>
      <label><input type="checkbox" name="tsample"> Sample</label>
      <button type="button" class="btn btn-secondary" data-remove>Remove</button>
    </div>`;
  testsEl.appendChild(wrap);
});

function parseExamples(text) {
  return text
    .split(/\n\s*\n/)
    .map((block) => {
      const input = (block.match(/Input:\s*([\s\S]*?)(?=Output:|$)/i) || [, ""])[1].trim();
      const output = (block.match(/Output:\s*([\s\S]*?)(?=Explanation:|$)/i) || [, ""])[1].trim();
      const explanation = (block.match(/Explanation:\s*([\s\S]*)/i) || [, ""])[1].trim();
      return { input, output, explanation };
    })
    .filter((e) => e.input || e.output);
}

function readForm() {
  const tests = [...testsEl.querySelectorAll(".test-case-row")].map((row) => ({
    input: row.querySelector('[name="tin"]').value,
    output: row.querySelector('[name="tout"]').value,
    sample: row.querySelector('[name="tsample"]').checked,
  }));
  return {
    ...current,
    title: form.title.value.trim(),
    slug: form.slug.value.trim() || form.title.value.trim().toLowerCase().replace(/\s+/g, "-"),
    difficulty: form.difficulty.value,
    tags: form.tags.value.split(",").map((t) => t.trim()).filter(Boolean),
    published: form.published.checked,
    description: form.description.value,
    constraints: form.constraints.value.split("\n").map((s) => s.trim()).filter(Boolean),
    examples: parseExamples(form.examples.value),
    inputFormat: form.inputFormat.value,
    outputFormat: form.outputFormat.value,
    starter: {
      python: form.starterPython.value,
      cpp: form.starterCpp.value,
      java: form.starterJava.value,
    },
    tests,
  };
}

async function refreshList() {
  empty.hidden = false;
  empty.textContent = "Loading...";
  try {
    const items = await listProblems({ includeUnpublished: true });
    if (!items.length) {
      empty.textContent = "No problems.";
      rowsEl.innerHTML = "";
      return;
    }
    empty.hidden = true;
    rowsEl.innerHTML = items
      .map(
        (p) => `<tr data-id="${escapeHtml(p.id)}">
          <td><button type="button" class="row-link" data-edit>${escapeHtml(p.title)}</button></td>
          <td><span class="${difficultyClass(p.difficulty)}">${escapeHtml(p.difficulty)}</span></td>
          <td><span class="${statusClass(p.published ? "Published" : "Draft")}">${p.published ? "Published" : "Draft"}</span></td>
        </tr>`
      )
      .join("");
  } catch {
    empty.hidden = false;
    empty.textContent = "Failed to load problems.";
  }
}

rowsEl.addEventListener("click", async (e) => {
  const tr = e.target.closest("tr[data-id]");
  if (!tr) return;
  try {
    fillForm(await getProblemAdmin(tr.dataset.id));
  } catch {
    toast("Failed to open problem.", "error");
  }
});

newBtn.addEventListener("click", () => fillForm(blankProblem()));

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = readForm();
  if (!payload.title) {
    toast("Title is required.", "error");
    return;
  }
  setBusy(saveBtn, true, "Saving...");
  try {
    current = await saveProblem(payload);
    toast("Problem saved (demo store).", "ok");
    await refreshList();
  } catch {
    toast("Save failed.", "error");
  } finally {
    setBusy(saveBtn, false);
  }
});

deleteBtn.addEventListener("click", async () => {
  if (!current?.id) return;
  if (!confirm("Delete this problem from the demo catalog?")) return;
  try {
    await deleteProblem(current.id);
    fillForm(blankProblem());
    deleteBtn.hidden = true;
    toast("Deleted.", "ok");
    await refreshList();
  } catch {
    toast("Delete failed.", "error");
  }
});

document.getElementById("toggle-publish")?.addEventListener("click", async () => {
  if (!current?.id) return;
  try {
    const next = await setPublished(current.id, !current.published);
    fillForm(next);
    toast(next.published ? "Published." : "Unpublished.", "ok");
    await refreshList();
  } catch {
    toast("Update failed.", "error");
  }
});

fillForm(blankProblem());
deleteBtn.hidden = true;
refreshList();

import * as problemsApi from "../api/problems.js";
import { listSubmissions } from "../api/submissions.js";
import { difficultyClass } from "../components/status.js";
import { escapeHtml } from "../components/header.js";

const tbody = document.getElementById("problem-rows");
const empty = document.getElementById("empty");
const search = document.getElementById("search");
const difficulty = document.getElementById("difficulty");
const language = document.getElementById("language");
const table = document.getElementById("problems-table");

let rows = [];
let sortKey = "title";
let sortDir = 1;
let solved = new Set();
let attempted = new Set();

function statusOf(id) {
  if (solved.has(id)) return "Solved";
  if (attempted.has(id)) return "Attempted";
  return "—";
}

function render() {
  const q = search.value.trim().toLowerCase();
  const diff = difficulty.value;
  const lang = language.value;
  let list = rows.filter((p) => {
    if (q && !p.title.toLowerCase().includes(q) && !p.tags.join(" ").toLowerCase().includes(q)) return false;
    if (diff !== "all" && p.difficulty.toLowerCase() !== diff) return false;
    if (lang !== "all" && !p.languages.includes(lang)) return false;
    return true;
  });
  list.sort((a, b) => {
    let av = a[sortKey];
    let bv = b[sortKey];
    if (sortKey === "status") {
      av = statusOf(a.id);
      bv = statusOf(b.id);
    }
    return String(av).localeCompare(String(bv)) * sortDir;
  });
  if (!list.length) {
    tbody.innerHTML = "";
    empty.hidden = false;
    empty.textContent = rows.length ? "No problems found." : "No problems available.";
    return;
  }
  empty.hidden = true;
  tbody.innerHTML = list
    .map((p) => {
      const st = statusOf(p.id);
      return `<tr data-href="problem.html?id=${encodeURIComponent(p.id)}">
        <td><a class="row-link" href="problem.html?id=${encodeURIComponent(p.id)}">${escapeHtml(p.title)}</a></td>
        <td><span class="${difficultyClass(p.difficulty)}">${escapeHtml(p.difficulty)}</span></td>
        <td>${st === "Solved" ? '<span class="badge badge-ok">Solved</span>' : escapeHtml(st)}</td>
      </tr>`;
    })
    .join("");
}

table?.querySelectorAll("th.sortable").forEach((th) => {
  th.addEventListener("click", () => {
    const key = th.dataset.key;
    if (sortKey === key) sortDir *= -1;
    else {
      sortKey = key;
      sortDir = 1;
    }
    render();
  });
});

tbody?.addEventListener("click", (e) => {
  const tr = e.target.closest("tr[data-href]");
  if (tr && e.target.tagName !== "A") location.href = tr.dataset.href;
});

[search, difficulty, language].forEach((el) => el?.addEventListener("input", render));

async function init() {
  empty.hidden = false;
  empty.textContent = "Loading...";
  try {
    const [problems, submissions] = await Promise.all([problemsApi.listProblems(), listSubmissions()]);
    rows = problems;
    submissions.forEach((s) => {
      attempted.add(s.problemId);
      if (s.status === "Accepted") solved.add(s.problemId);
    });
    render();
  } catch {
    empty.hidden = false;
    empty.textContent = "Failed to load problems.";
  }
}

init();

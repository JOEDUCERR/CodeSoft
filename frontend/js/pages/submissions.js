import { listSubmissions, getSubmission } from "../api/submissions.js";
import { openModal } from "../components/modal.js";
import { statusClass, formatTime, formatMemory, formatRuntime } from "../components/status.js";
import { escapeHtml } from "../components/header.js";

const tbody = document.getElementById("submission-rows");
const empty = document.getElementById("empty");

function detailHtml(s) {
  return `
    <p>Problem: <a href="problem.html?id=${encodeURIComponent(s.problemId)}">${escapeHtml(s.problemTitle)}</a></p>
    <p>Language: ${escapeHtml(s.language)}</p>
    <p>Status: <span class="${statusClass(s.status)}">${escapeHtml(s.status)}</span></p>
    <p>Time: ${formatRuntime(s.runtimeMs)} · Memory: ${formatMemory(s.memoryKb)}</p>
    <p>Submitted: ${new Date(s.createdAt).toLocaleString()}</p>
    <p>Tests: ${s.testsPassed}/${s.testsTotal}</p>
    <p><strong>Source</strong></p>
    <pre class="mono">${escapeHtml(s.code)}</pre>
  `;
}

function show(s) {
  openModal({
    title: s.problemTitle,
    bodyHtml: detailHtml(s),
  });
}

async function init() {
  empty.hidden = false;
  empty.textContent = "Loading...";
  try {
    const items = await listSubmissions();
    if (!items.length) {
      empty.textContent = "No submissions yet.";
      return;
    }
    empty.hidden = true;
    tbody.innerHTML = items
      .map(
        (s) => `<tr data-id="${escapeHtml(s.id)}">
          <td><a class="row-link" href="problem.html?id=${encodeURIComponent(s.problemId)}">${escapeHtml(s.problemTitle)}</a></td>
          <td>${escapeHtml(s.language)}</td>
          <td><span class="${statusClass(s.status)}">${escapeHtml(s.status)}</span></td>
          <td>${formatTime(s.createdAt)}</td>
        </tr>`
      )
      .join("");

    tbody.addEventListener("click", async (e) => {
      const tr = e.target.closest("tr[data-id]");
      if (!tr) return;
      if (e.target.closest("a")) return;
      try {
        const s = await getSubmission(tr.dataset.id);
        show(s);
      } catch {
        empty.hidden = false;
        empty.textContent = "Failed to load submission.";
      }
    });

    const focusId = new URLSearchParams(location.search).get("id");
    if (focusId) {
      const s = items.find((x) => x.id === focusId) || (await getSubmission(focusId).catch(() => null));
      if (s) show(s);
    }
  } catch {
    empty.hidden = false;
    empty.textContent = "Failed to load submissions.";
  }
}

init();

import { getCurrentUser } from "../auth.js";
import * as problemsApi from "../api/problems.js";
import * as submissionsApi from "../api/submissions.js";
import { difficultyClass, statusClass, formatTime } from "../components/status.js";
import { escapeHtml } from "../components/header.js";

const root = document.getElementById("home");
const user = getCurrentUser();

function row(item) {
  return `<a href="problem.html?id=${encodeURIComponent(item.id)}">${escapeHtml(item.title)}
    <span class="${difficultyClass(item.difficulty)}">${escapeHtml(item.difficulty)}</span></a>`;
}

async function init() {
  root.innerHTML = `<p class="muted">Loading...</p>`;
  try {
    const [problems, submissions] = await Promise.all([
      problemsApi.listProblems(),
      submissionsApi.listSubmissions(),
    ]);
    const recentAttempt = submissions[0];
    const continueId = recentAttempt?.problemId || problems[0]?.id;
    const continueProblem = problems.find((p) => p.id === continueId) || problems[0];
    const popular = problems.filter((p) => p.difficulty !== "Hard").slice(0, 6);
    const recentSubs = submissions.slice(0, 5);

    root.innerHTML = `
      <h1>Welcome back, ${escapeHtml(user?.name || "User")}</h1>
      <section class="full">
        <div class="section-head">
          <h2>Continue solving</h2>
          ${continueProblem ? `<a class="btn" href="problem.html?id=${encodeURIComponent(continueProblem.id)}">Open ${escapeHtml(continueProblem.title)}</a>` : ""}
        </div>
        <p class="muted">${continueProblem ? "Pick up from your last submission or a recommended problem." : "No problems available."}</p>
      </section>
      <div class="home-grid">
        <section>
          <h2>Recommended</h2>
          <div class="card-list">${popular.map(row).join("") || '<div class="item muted">No problems found.</div>'}</div>
        </section>
        <section>
          <h2>Recent submissions</h2>
          <div class="card-list">
            ${
              recentSubs.length
                ? recentSubs
                    .map(
                      (s) => `<a href="submissions.html?id=${encodeURIComponent(s.id)}">
                        ${escapeHtml(s.problemTitle)}
                        <span class="${statusClass(s.status)}">${escapeHtml(s.status)}</span>
                        <span class="muted"> · ${formatTime(s.createdAt)}</span>
                      </a>`
                    )
                    .join("")
                : '<div class="item muted">No submissions yet.</div>'
            }
          </div>
        </section>
      </div>
    `;
  } catch {
    root.innerHTML = `<p class="page-error">Failed to load home data.</p>`;
  }
}

init();

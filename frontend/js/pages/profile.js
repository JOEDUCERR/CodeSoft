import { getProfile } from "../api/user.js";
import { statusClass, formatTime } from "../components/status.js";
import { escapeHtml } from "../components/header.js";

const root = document.getElementById("profile");

async function init() {
  root.innerHTML = `<p class="muted">Loading...</p>`;
  try {
    const p = await getProfile();
    root.innerHTML = `
      <h1>${escapeHtml(p.name)}</h1>
      <p class="muted">${escapeHtml(p.email)} ${p.role === "admin" ? "· admin" : ""}</p>
      <div class="stats-row">
        <div><strong>${p.solved}</strong><span>Problems solved</span></div>
        <div><strong>${p.submissions}</strong><span>Submissions</span></div>
        <div><strong>${p.accepted}</strong><span>Accepted</span></div>
      </div>
      <h2>Activity</h2>
      <p class="muted">Recent submission density (demo)</p>
      <div class="activity-grid" aria-hidden="true">
        ${p.activity.map((v) => `<div class="activity-cell ${v === 2 ? "on" : v === 1 ? "mid" : ""}"></div>`).join("")}
      </div>
      <h2 style="margin-top:24px">Recent submissions</h2>
      <div class="card-list">
        ${
          p.recent.length
            ? p.recent
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
    `;
  } catch {
    root.innerHTML = `<p class="page-error">Failed to load profile.</p>`;
  }
}

init();

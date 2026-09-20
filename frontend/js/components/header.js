import { getCurrentUser, isAdmin, logout } from "../auth.js";

export function renderHeader(active) {
  const header = document.querySelector("[data-header]");
  if (!header) return;
  const user = getCurrentUser();
  const name = user?.name || "User";
  header.innerHTML = `
    <a class="brand" href="index.html">CodeSoft</a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">Menu</button>
    <nav class="site-nav" id="site-nav" aria-label="Main">
      <a href="problems.html" ${active === "problems" ? 'aria-current="page"' : ""}>Problems</a>
      <a href="submissions.html" ${active === "submissions" ? 'aria-current="page"' : ""}>Submissions</a>
      <a href="profile.html" ${active === "profile" ? 'aria-current="page"' : ""}>Profile</a>
      ${isAdmin() ? `<a href="admin.html" ${active === "admin" ? 'aria-current="page"' : ""}>Admin</a>` : ""}
    </nav>
    <div class="header-spacer"></div>
    <div class="user-menu">
      <button class="user-menu-btn" type="button" aria-haspopup="true" aria-expanded="false">${escapeHtml(name)} ▾</button>
      <div class="user-menu-list" role="menu">
        <a href="profile.html" role="menuitem">Profile</a>
        ${isAdmin() ? '<a href="admin.html" role="menuitem">Admin</a>' : ""}
        <button type="button" data-logout role="menuitem">Log out</button>
      </div>
    </div>
  `;

  const toggle = header.querySelector(".nav-toggle");
  toggle?.addEventListener("click", () => {
    const open = header.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });

  const menu = header.querySelector(".user-menu");
  const btn = header.querySelector(".user-menu-btn");
  btn?.addEventListener("click", () => {
    const open = menu.classList.toggle("open");
    btn.setAttribute("aria-expanded", String(open));
  });
  document.addEventListener("click", (e) => {
    if (!menu.contains(e.target)) {
      menu.classList.remove("open");
      btn?.setAttribute("aria-expanded", "false");
    }
  });

  header.querySelector("[data-logout]")?.addEventListener("click", () => {
    logout();
    location.href = "login.html";
  });
}

export function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

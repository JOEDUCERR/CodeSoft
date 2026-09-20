import { renderHeader } from "./components/header.js";
import { requireAuth, requireAdmin, redirectIfAuthed } from "./auth.js";

const PAGE = document.body.dataset.page;

if (document.querySelector("[data-header]")) {
  if (PAGE === "admin") requireAdmin();
  else requireAuth();
  renderHeader(PAGE);
}

if (PAGE === "login" || PAGE === "register") {
  redirectIfAuthed();
}

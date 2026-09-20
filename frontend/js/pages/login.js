import { login } from "../auth.js";
import { ApiError } from "../api/client.js";
import { isEmail, setBusy } from "../components/forms.js";
import { toast } from "../components/toast.js";

const form = document.getElementById("login-form");
const errorBox = document.getElementById("form-error");
const email = document.getElementById("email");
const password = document.getElementById("password");
const submit = document.getElementById("login-submit");
const google = document.getElementById("google-btn");
const toggle = document.getElementById("toggle-password");

toggle?.addEventListener("click", () => {
  const hidden = password.type === "password";
  password.type = hidden ? "text" : "password";
  toggle.textContent = hidden ? "Hide" : "Show";
});

function showError(msg) {
  errorBox.hidden = !msg;
  errorBox.textContent = msg || "";
}

form?.addEventListener("submit", async (e) => {
  e.preventDefault();
  showError("");
  const emailVal = email.value.trim();
  const passVal = password.value;
  if (!emailVal || !passVal) {
    showError("Email and password are required.");
    return;
  }
  if (!isEmail(emailVal)) {
    showError("Enter a valid email address.");
    return;
  }
  setBusy(submit, true, "Signing in...");
  try {
    await login({ email: emailVal, password: passVal });
    const next = new URLSearchParams(location.search).get("next") || "index.html";
    location.href = next;
  } catch (err) {
    showError(err instanceof ApiError ? err.message : "Login failed.");
  } finally {
    setBusy(submit, false);
  }
});

google?.addEventListener("click", async () => {
  toast("Google sign-in is a placeholder until OAuth is wired on the backend.", "error");
});

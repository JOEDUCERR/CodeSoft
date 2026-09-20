import { register } from "../auth.js";
import { ApiError } from "../api/client.js";
import { isEmail, passwordIssues, setBusy } from "../components/forms.js";

const form = document.getElementById("register-form");
const errorBox = document.getElementById("form-error");
const submit = document.getElementById("register-submit");

function showError(msg) {
  errorBox.hidden = !msg;
  errorBox.textContent = msg || "";
}

form?.addEventListener("submit", async (e) => {
  e.preventDefault();
  showError("");
  const name = form.name.value.trim();
  const email = form.email.value.trim();
  const password = form.password.value;
  const confirm = form.confirm.value;
  if (!name || !email || !password || !confirm) {
    showError("All fields are required.");
    return;
  }
  if (!isEmail(email)) {
    showError("Enter a valid email address.");
    return;
  }
  const issues = passwordIssues(password);
  if (issues.length) {
    showError(issues.join(" "));
    return;
  }
  if (password !== confirm) {
    showError("Passwords do not match.");
    return;
  }
  setBusy(submit, true, "Creating account...");
  try {
    await register({ name, email, password });
    location.href = "index.html";
  } catch (err) {
    showError(err instanceof ApiError ? err.message : "Registration failed.");
  } finally {
    setBusy(submit, false);
  }
});

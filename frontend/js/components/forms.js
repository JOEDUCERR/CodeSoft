export function isEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

export function passwordIssues(password) {
  const issues = [];
  if (password.length < 8) issues.push("At least 8 characters.");
  if (!/[A-Za-z]/.test(password)) issues.push("Include a letter.");
  if (!/[0-9]/.test(password)) issues.push("Include a number.");
  return issues;
}

export function setBusy(button, busy, busyLabel) {
  if (!button.dataset.label) button.dataset.label = button.textContent;
  button.disabled = busy;
  button.textContent = busy ? busyLabel : button.dataset.label;
}
